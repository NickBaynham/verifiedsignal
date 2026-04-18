"""Persistence for model write-back artifacts and audit events."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import ModelWritebackArtifact, ModelWritebackEvent


def insert_artifact(
    session: Session,
    *,
    knowledge_model_id: uuid.UUID,
    knowledge_model_version_id: uuid.UUID | None,
    artifact_kind: str,
    title: str,
    summary: str | None,
    payload_json: dict,
    origin_type: str,
    origin_id: str | None,
    verification_state: str,
    confidence_score: float | None,
    related_document_id: uuid.UUID | None,
    related_asset_id: uuid.UUID | None,
    related_writeback_id: uuid.UUID | None,
    related_entity_id: uuid.UUID | None,
    related_claim_id: uuid.UUID | None,
    evidence_refs_json: list | dict,
    supersedes_id: uuid.UUID | None = None,
) -> ModelWritebackArtifact:
    row = ModelWritebackArtifact(
        knowledge_model_id=knowledge_model_id,
        knowledge_model_version_id=knowledge_model_version_id,
        artifact_kind=artifact_kind,
        title=title.strip(),
        summary=summary.strip() if summary else None,
        payload_json=payload_json,
        origin_type=origin_type,
        origin_id=origin_id.strip() if origin_id else None,
        verification_state=verification_state,
        confidence_score=confidence_score,
        related_document_id=related_document_id,
        related_asset_id=related_asset_id,
        related_writeback_id=related_writeback_id,
        related_entity_id=related_entity_id,
        related_claim_id=related_claim_id,
        evidence_refs_json=evidence_refs_json,
        supersedes_id=supersedes_id,
    )
    session.add(row)
    session.flush()
    return row


def insert_event(
    session: Session,
    *,
    artifact_id: uuid.UUID,
    event_type: str,
    payload_json: dict,
    actor_origin_type: str | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> ModelWritebackEvent:
    row = ModelWritebackEvent(
        artifact_id=artifact_id,
        event_type=event_type,
        payload_json=payload_json,
        actor_origin_type=actor_origin_type,
        actor_user_id=actor_user_id,
    )
    session.add(row)
    session.flush()
    return row


def get_artifact_for_model(
    session: Session,
    *,
    model_id: uuid.UUID,
    artifact_id: uuid.UUID,
) -> ModelWritebackArtifact | None:
    row = session.get(ModelWritebackArtifact, artifact_id)
    if row is None or row.knowledge_model_id != model_id:
        return None
    return row


def list_artifacts(
    session: Session,
    *,
    model_id: uuid.UUID,
    artifact_kind: str | None = None,
    verification_state: str | None = None,
    version_id: uuid.UUID | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[ModelWritebackArtifact]:
    stmt: Select[tuple[ModelWritebackArtifact]] = select(ModelWritebackArtifact).where(
        ModelWritebackArtifact.knowledge_model_id == model_id
    )
    if artifact_kind:
        stmt = stmt.where(ModelWritebackArtifact.artifact_kind == artifact_kind)
    if verification_state:
        stmt = stmt.where(ModelWritebackArtifact.verification_state == verification_state)
    if version_id:
        stmt = stmt.where(ModelWritebackArtifact.knowledge_model_version_id == version_id)
    stmt = (
        stmt.order_by(ModelWritebackArtifact.created_at.desc()).limit(limit).offset(offset)
    )
    return list(session.scalars(stmt).all())


def update_verification(
    session: Session,
    row: ModelWritebackArtifact,
    *,
    verification_state: str,
    reviewer_id: uuid.UUID | None,
    review_note: str | None,
) -> None:
    row.verification_state = verification_state
    row.reviewer_id = reviewer_id
    row.review_note = review_note.strip() if review_note else None
    row.reviewed_at = datetime.now(UTC)
