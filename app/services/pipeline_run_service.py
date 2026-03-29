"""
Execute the scaffold document pipeline with Postgres persistence.

Called from the ARQ worker inside a thread (see `worker.pipeline.run_pipeline_job`).
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.db.models import Document
from app.pipeline.constants import DOCUMENT_SCAFFOLD_STAGES
from app.repositories import pipeline_repository as pipe_repo

log = logging.getLogger("verifiedsignal.pipeline.run")


def execute_scaffold_pipeline(session: Session, document_id: uuid.UUID, job_id: str) -> None:
    """
    Create `pipeline_runs` + `pipeline_events`, advance `documents.status`:
    queued → processing → completed (or failed on error).
    """
    if session.get(Document, document_id) is None:
        raise ValueError(f"document not found: {document_id}")

    run = pipe_repo.create_pipeline_run(session, document_id, job_id)
    pipe_repo.set_document_status(session, document_id, "processing")
    pipe_repo.append_event(
        session,
        run.id,
        0,
        "pipeline_started",
        None,
        {"job_id": job_id, "document_id": str(document_id)},
    )
    log.info("pipeline_started document_id=%s job_id=%s", document_id, job_id)

    try:
        for step_idx, stage in enumerate(DOCUMENT_SCAFFOLD_STAGES, start=1):
            run.stage = stage
            pipe_repo.append_event(
                session,
                run.id,
                step_idx,
                "pipeline_stage",
                stage,
                {"job_id": job_id, "stage": stage, "document_id": str(document_id)},
            )
            log.info("pipeline_stage document_id=%s stage=%s job_id=%s", document_id, stage, job_id)

        pipe_repo.complete_run(session, run)
        pipe_repo.set_document_status(session, document_id, "completed")
        log.info("pipeline_complete document_id=%s job_id=%s", document_id, job_id)
    except Exception as e:
        pipe_repo.fail_run(session, run, str(e))
        pipe_repo.set_document_status(session, document_id, "failed")
        log.exception("pipeline_failed document_id=%s job_id=%s", document_id, job_id)
        raise
