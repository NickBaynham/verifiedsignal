"""
Internal hooks for future automation: runtime evidence, imported findings, agent observations.

V1: thin wrappers around model_writeback_service with conservative defaults.
Browser / autonomous collection is out of scope; callers use these entry points explicitly.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.schemas.model_writeback import (
    EvidenceNoteCreateIn,
    ExecutionResultCreateIn,
    FindingCreateIn,
    WritebackProvenanceIn,
)
from app.services import model_writeback_service as wb_svc


def record_runtime_evidence(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    title: str,
    details: str | None,
    model_version_id: uuid.UUID | None = None,
    related_document_id: uuid.UUID | None = None,
    evidence_refs: list | None = None,
    settings: Settings | None = None,
):
    """Execution or operational evidence; defaults to auto_ingested + runtime_evidence."""
    body = EvidenceNoteCreateIn(
        title=title,
        model_version_id=model_version_id,
        details=details,
        related_document_id=related_document_id,
        evidence_refs=evidence_refs or [],
        provenance=WritebackProvenanceIn(
            origin_type="runtime_evidence",
            verification_state="auto_ingested",
        ),
    )
    return wb_svc.create_evidence_note(
        session, auth_sub=auth_sub, model_id=model_id, body=body, settings=settings
    )


def record_agent_observation(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    title: str,
    details: str | None,
    agent_id: str | None = None,
    model_version_id: uuid.UUID | None = None,
    settings: Settings | None = None,
):
    """Structured agent observation stored as a finding (proposed, agent)."""
    body = FindingCreateIn(
        title=title,
        model_version_id=model_version_id,
        details=details,
        provenance=WritebackProvenanceIn(origin_type="agent", origin_id=agent_id),
    )
    return wb_svc.create_finding(
        session, auth_sub=auth_sub, model_id=model_id, body=body, settings=settings
    )


def record_execution_outcome(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    title: str,
    status: str,
    summary: str | None = None,
    details: str | None = None,
    model_version_id: uuid.UUID | None = None,
    related_test_artifact_id: uuid.UUID | None = None,
    settings: Settings | None = None,
):
    """Test or check run outcome from automation; auto_ingested by default."""
    settings = settings or get_settings()
    body = ExecutionResultCreateIn(
        title=title,
        status=status,
        model_version_id=model_version_id,
        summary=summary,
        details=details,
        related_test_artifact_id=related_test_artifact_id,
        provenance=WritebackProvenanceIn(
            origin_type="internal_service",
            verification_state="auto_ingested",
        ),
    )
    return wb_svc.create_execution_result(
        session, auth_sub=auth_sub, model_id=model_id, body=body, settings=settings
    )


def create_imported_finding(
    session: Session,
    *,
    auth_sub: str,
    model_id: uuid.UUID,
    title: str,
    details: str | None,
    external_key: str | None = None,
    model_version_id: uuid.UUID | None = None,
    settings: Settings | None = None,
):
    """Finding sourced from an external system; remains proposed until reviewed."""
    body = FindingCreateIn(
        title=title,
        model_version_id=model_version_id,
        details=details,
        provenance=WritebackProvenanceIn(
            origin_type="imported_system",
            origin_id=external_key,
            verification_state="proposed",
        ),
    )
    return wb_svc.create_finding(
        session, auth_sub=auth_sub, model_id=model_id, body=body, settings=settings
    )
