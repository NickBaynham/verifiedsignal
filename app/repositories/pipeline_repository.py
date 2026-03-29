"""Persistence for pipeline_runs / pipeline_events."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Document, PipelineEvent, PipelineRun
from app.pipeline.constants import PIPELINE_NAME, PIPELINE_VERSION


def create_pipeline_run(session: Session, document_id: uuid.UUID, job_id: str) -> PipelineRun:
    now = datetime.now(UTC)
    run = PipelineRun(
        document_id=document_id,
        pipeline_name=PIPELINE_NAME,
        pipeline_version=PIPELINE_VERSION,
        definition_schema_version=1,
        status="running",
        stage="queued",
        started_at=now,
        run_metadata={"job_id": job_id},
    )
    session.add(run)
    session.flush()
    return run


def append_event(
    session: Session,
    run_id: uuid.UUID,
    step_index: int,
    event_type: str,
    stage: str | None,
    payload: dict,
) -> None:
    ev = PipelineEvent(
        pipeline_run_id=run_id,
        step_index=step_index,
        event_type=event_type,
        stage=stage,
        payload=payload,
        event_schema_version=1,
    )
    session.add(ev)


def set_document_status(session: Session, document_id: uuid.UUID, status: str) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        raise ValueError(f"document not found: {document_id}")
    doc.status = status


def complete_run(session: Session, run: PipelineRun) -> None:
    run.status = "succeeded"
    run.completed_at = datetime.now(UTC)


def fail_run(session: Session, run: PipelineRun, message: str) -> None:
    run.status = "failed"
    run.error_detail = {"message": message[:4000]}
    run.completed_at = datetime.now(UTC)
