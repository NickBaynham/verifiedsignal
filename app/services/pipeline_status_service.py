"""Read pipeline run + events for a document (API + UI polling)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories import pipeline_repository as pipe_repo
from app.schemas.pipeline import DocumentPipelineOut, PipelineEventOut, PipelineRunOut
from app.services.document_service import get_document_for_user


def get_document_pipeline_for_user(
    session: Session,
    *,
    document_id: uuid.UUID,
    auth_sub: str,
) -> DocumentPipelineOut | None:
    out = get_document_for_user(session, document_id=document_id, auth_sub=auth_sub)
    if out is None:
        return None
    doc, _sources = out
    run = pipe_repo.get_latest_run_for_document(session, document_id)
    if run is None:
        return DocumentPipelineOut(
            document_id=doc.id,
            document_status=doc.status,
            run=None,
            events=[],
        )
    ev_rows = pipe_repo.list_events_for_run(session, run.id)
    events = [
        PipelineEventOut(
            id=e.id,
            step_index=e.step_index,
            event_type=e.event_type,
            stage=e.stage,
            payload=dict(e.payload or {}),
            created_at=e.created_at,
        )
        for e in ev_rows
    ]
    run_out = PipelineRunOut(
        id=run.id,
        document_id=run.document_id,
        status=run.status,
        stage=run.stage,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_detail=dict(run.error_detail) if run.error_detail else None,
        run_metadata=dict(run.run_metadata or {}),
    )
    return DocumentPipelineOut(
        document_id=doc.id,
        document_status=doc.status,
        run=run_out,
        events=events,
    )
