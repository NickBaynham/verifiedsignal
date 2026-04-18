"""Create, list, and govern model write-back artifacts."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import (
    Document,
    KnowledgeModelAsset,
    KnowledgeModelVersion,
    ModelBuildRun,
    ModelWritebackArtifact,
    ModelWritebackEvent,
)
from app.domain.model_writeback_constants import ARTIFACT_KINDS, ORIGIN_TYPES
from app.repositories import knowledge_model_repository as km_repo
from app.repositories import model_writeback_repository as wb_repo
from app.schemas.model_writeback import (
    ContradictionCreateIn,
    EvidenceNoteCreateIn,
    ExecutionResultCreateIn,
    FindingCreateIn,
    ModelActivityItemOut,
    ModelActivityResponse,
    RiskCreateIn,
    TestArtifactCreateIn,
    VerificationPatchIn,
    WritebackListResponse,
    WritebackOut,
    WritebackProvenanceIn,
)
from app.services.document_access import resolve_accessible_collection_ids
from app.services.identity_service import find_user_id_by_auth_sub
from app.services.model_writeback_governance import (
    assert_transition_allowed,
    assert_valid_verification_state,
)


def _ensure_model_access(
    session: Session,
    auth_sub: str,
    model_id: uuid.UUID,
    settings: Settings,
) -> Any:
    m = km_repo.get_model(session, model_id)
    if m is None:
        return None
    allowed = resolve_accessible_collection_ids(session, auth_sub, settings)
    if m.collection_id not in allowed:
        raise PermissionError("model not found or access denied")
    return m


def _resolve_version_id(
    session: Session,
    model_id: uuid.UUID,
    version_id: uuid.UUID | None,
) -> uuid.UUID | None:
    if version_id is None:
        latest = km_repo.get_latest_version(session, model_id)
        return latest.id if latest else None
    v = km_repo.get_version(session, version_id)
    if v is None or v.knowledge_model_id != model_id:
        raise ValueError("invalid model_version_id for this model")
    return v.id


def _validate_document(
    session: Session,
    collection_id: uuid.UUID,
    document_id: uuid.UUID | None,
) -> None:
    if document_id is None:
        return
    doc = session.get(Document, document_id)
    if doc is None or doc.collection_id != collection_id:
        raise ValueError("related_document_id must belong to the model's collection")


def _validate_asset(
    session: Session,
    *,
    model_id: uuid.UUID,
    collection_id: uuid.UUID,
    resolved_version_id: uuid.UUID | None,
    related_document_id: uuid.UUID | None,
    related_asset_id: uuid.UUID | None,
) -> None:
    if related_asset_id is None:
        return
    a = session.get(KnowledgeModelAsset, related_asset_id)
    if a is None:
        raise ValueError("related_asset_id not found")
    v = km_repo.get_version(session, a.model_version_id)
    if v is None or v.knowledge_model_id != model_id:
        raise ValueError("asset does not belong to this model")
    m = km_repo.get_model(session, model_id)
    if m is None or m.collection_id != collection_id:
        raise ValueError("collection mismatch")
    if resolved_version_id is not None and a.model_version_id != resolved_version_id:
        raise ValueError("related_asset_id is not part of the selected model version")
    if related_document_id is not None and a.document_id != related_document_id:
        raise ValueError("related_asset_id does not match related_document_id")
    _validate_document(session, collection_id, a.document_id)


def _validate_related_writeback(
    session: Session,
    model_id: uuid.UUID,
    related_id: uuid.UUID | None,
) -> None:
    if related_id is None:
        return
    other = wb_repo.get_artifact_for_model(session, model_id=model_id, artifact_id=related_id)
    if other is None:
        raise ValueError("related_writeback_id not found on this model")


def _normalize_evidence_refs(refs: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in refs:
        if hasattr(r, "model_dump"):
            out.append(r.model_dump())
        elif isinstance(r, dict):
            out.append(r)
    return out


def _apply_provenance_defaults(
    *,
    explicit: WritebackProvenanceIn | None,
    default_origin: str,
    default_origin_id: str | None,
    default_verification: str,
    allow_verification_override: bool,
) -> tuple[str, str | None, str]:
    origin_type = default_origin
    origin_id = default_origin_id
    verification_state = default_verification
    if explicit:
        if explicit.origin_type is not None:
            if explicit.origin_type not in ORIGIN_TYPES:
                raise ValueError("invalid origin_type")
            origin_type = explicit.origin_type
        if explicit.origin_id is not None:
            origin_id = explicit.origin_id.strip() or None
        if explicit.verification_state is not None:
            if not allow_verification_override:
                raise ValueError("verification_state cannot be set for this operation")
            assert_valid_verification_state(explicit.verification_state)
            verification_state = explicit.verification_state
    return origin_type, origin_id, verification_state


def create_finding(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: FindingCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {}
    if body.details:
        payload["details"] = body.details
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="finding",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=None,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "finding"},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def create_risk(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: RiskCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {}
    if body.details:
        payload["details"] = body.details
    if body.severity:
        payload["severity"] = body.severity
    if body.likelihood:
        payload["likelihood"] = body.likelihood
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="risk",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=None,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "risk"},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def create_test_artifact(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: TestArtifactCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_related_writeback(session, model_id, body.related_risk_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {"artifact_subtype": body.artifact_subtype}
    if body.content:
        payload["content"] = body.content
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="test_artifact",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=body.related_risk_id,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "test_artifact"},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def create_execution_result(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: ExecutionResultCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_related_writeback(session, model_id, body.related_test_artifact_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {"execution_status": body.status}
    if body.details:
        payload["details"] = body.details
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="execution_result",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=body.related_test_artifact_id,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "execution_result", "status": body.status},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def create_evidence_note(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: EvidenceNoteCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {"citation": body.citation}
    if body.details:
        payload["details"] = body.details
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="evidence_note",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=None,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "evidence_note"},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def create_contradiction(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    body: ContradictionCreateIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    vid = _resolve_version_id(session, model_id, body.model_version_id)
    _validate_document(session, m.collection_id, body.related_document_id)
    _validate_asset(
        session,
        model_id=model_id,
        collection_id=m.collection_id,
        resolved_version_id=vid,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
    )
    uid = find_user_id_by_auth_sub(session, auth_sub)
    origin, oid, vs = _apply_provenance_defaults(
        explicit=body.provenance,
        default_origin="human",
        default_origin_id=str(uid) if uid else auth_sub,
        default_verification="proposed",
        allow_verification_override=True,
    )
    payload: dict[str, Any] = {
        "conflicting_reference_a": body.conflicting_reference_a,
        "conflicting_reference_b": body.conflicting_reference_b,
    }
    if body.details:
        payload["details"] = body.details
    row = wb_repo.insert_artifact(
        session,
        knowledge_model_id=model_id,
        knowledge_model_version_id=vid,
        artifact_kind="contradiction",
        title=body.title,
        summary=body.summary,
        payload_json=payload,
        origin_type=origin,
        origin_id=oid,
        verification_state=vs,
        confidence_score=body.confidence_score,
        related_document_id=body.related_document_id,
        related_asset_id=body.related_asset_id,
        related_writeback_id=None,
        related_entity_id=None,
        related_claim_id=None,
        evidence_refs_json=_normalize_evidence_refs(body.evidence_refs),
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="created",
        payload_json={"artifact_kind": "contradiction"},
        actor_origin_type=origin,
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def list_writebacks(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    artifact_kind: str | None,
    verification_state: str | None,
    version_id: uuid.UUID | None,
    limit: int,
    offset: int,
    settings: Settings | None = None,
) -> WritebackListResponse | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    if artifact_kind and artifact_kind not in ARTIFACT_KINDS:
        raise ValueError("invalid artifact_kind filter")
    if verification_state:
        assert_valid_verification_state(verification_state)
    rows = wb_repo.list_artifacts(
        session,
        model_id=model_id,
        artifact_kind=artifact_kind,
        verification_state=verification_state,
        version_id=version_id,
        limit=min(limit, 500),
        offset=offset,
    )
    return WritebackListResponse(
        items=[WritebackOut.from_row(r) for r in rows],
        knowledge_model_id=model_id,
        limit=limit,
        offset=offset,
    )


def get_writeback(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    writeback_id: uuid.UUID,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    row = wb_repo.get_artifact_for_model(session, model_id=model_id, artifact_id=writeback_id)
    if row is None:
        return None
    return WritebackOut.from_row(row)


def patch_verification(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    writeback_id: uuid.UUID,
    body: VerificationPatchIn,
    settings: Settings | None = None,
) -> WritebackOut | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    row = wb_repo.get_artifact_for_model(session, model_id=model_id, artifact_id=writeback_id)
    if row is None:
        return None
    assert_transition_allowed(row.verification_state, body.verification_state)
    prev_state = row.verification_state
    uid = find_user_id_by_auth_sub(session, auth_sub)
    wb_repo.update_verification(
        session,
        row,
        verification_state=body.verification_state,
        reviewer_id=uid,
        review_note=body.review_note,
    )
    wb_repo.insert_event(
        session,
        artifact_id=row.id,
        event_type="verification_changed",
        payload_json={
            "from": prev_state,
            "to": body.verification_state,
            "review_note": body.review_note,
        },
        actor_origin_type="human",
        actor_user_id=uid,
    )
    session.commit()
    session.refresh(row)
    return WritebackOut.from_row(row)


def list_model_activity(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    settings: Settings | None = None,
) -> ModelActivityResponse | None:
    settings = settings or get_settings()
    m = _ensure_model_access(session, auth_sub, model_id, settings)
    if m is None:
        return None
    items: list[ModelActivityItemOut] = []
    items.append(
        ModelActivityItemOut(
            id=f"km:{m.id}",
            occurred_at=m.created_at,
            event_type="model_created",
            title=f"Knowledge model created: {m.name}",
            summary=m.description,
            payload={"model_type": m.model_type},
        )
    )
    versions = km_repo.list_versions_for_model(session, model_id)
    for v in versions:
        items.append(
            ModelActivityItemOut(
                id=f"ver:{v.id}",
                occurred_at=v.created_at,
                event_type="version_created",
                title=f"Version v{v.version_number} ({v.build_status})",
                summary=v.error_message,
                knowledge_model_version_id=v.id,
                payload={"build_status": v.build_status},
            )
        )
        if v.completed_at:
            items.append(
                ModelActivityItemOut(
                    id=f"ver_complete:{v.id}",
                    occurred_at=v.completed_at,
                    event_type="version_build_completed",
                    title=f"Version v{v.version_number} completed",
                    knowledge_model_version_id=v.id,
                    payload={"build_status": v.build_status},
                )
            )

    br_stmt = (
        select(ModelBuildRun)
        .join(
            KnowledgeModelVersion,
            KnowledgeModelVersion.id == ModelBuildRun.model_version_id,
        )
        .where(KnowledgeModelVersion.knowledge_model_id == model_id)
    )
    for br in session.scalars(br_stmt).all():
        ts = br.completed_at or br.started_at or br.created_at
        items.append(
            ModelActivityItemOut(
                id=f"build_run:{br.id}",
                occurred_at=ts,
                event_type="build_run",
                title=f"Build run {br.status}",
                summary=br.error_message,
                knowledge_model_version_id=br.model_version_id,
                payload={"metrics": dict(br.metrics_json or {})},
            )
        )
    artifacts = wb_repo.list_artifacts(session, model_id=model_id, limit=500, offset=0)
    for a in artifacts:
        items.append(
            ModelActivityItemOut(
                id=f"wb:{a.id}",
                occurred_at=a.created_at,
                event_type="writeback_created",
                title=a.title,
                summary=a.summary,
                knowledge_model_version_id=a.knowledge_model_version_id,
                artifact_kind=a.artifact_kind,
                artifact_id=a.id,
                verification_state=a.verification_state,
                origin_type=a.origin_type,
                origin_id=a.origin_id,
                payload={"payload": dict(a.payload_json or {})},
            )
        )

    ev_stmt = (
        select(ModelWritebackEvent)
        .join(ModelWritebackArtifact, ModelWritebackEvent.artifact_id == ModelWritebackArtifact.id)
        .where(ModelWritebackArtifact.knowledge_model_id == model_id)
        .where(ModelWritebackEvent.event_type != "created")
    )
    for ev in session.scalars(ev_stmt).all():
        art = session.get(ModelWritebackArtifact, ev.artifact_id)
        items.append(
            ModelActivityItemOut(
                id=f"wbev:{ev.id}",
                occurred_at=ev.created_at,
                event_type=f"writeback_{ev.event_type}",
                title=ev.event_type.replace("_", " ").title(),
                knowledge_model_version_id=art.knowledge_model_version_id if art else None,
                artifact_id=ev.artifact_id,
                artifact_kind=art.artifact_kind if art else None,
                verification_state=art.verification_state if art else None,
                origin_type=ev.actor_origin_type,
                payload=dict(ev.payload_json or {}),
            )
        )
    items.sort(key=lambda x: x.occurred_at, reverse=True)
    return ModelActivityResponse(items=items, knowledge_model_id=model_id)