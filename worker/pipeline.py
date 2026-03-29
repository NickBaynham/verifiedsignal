"""
Document processing pipeline: persists `pipeline_runs` / `pipeline_events` in Postgres.

Runs blocking DB work in a worker thread so the ARQ async task stays non-blocking.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.pipeline.constants import DOCUMENT_SCAFFOLD_STAGES

from worker.logging import get_logger

log = get_logger("verifiedsignal.worker.pipeline")

# Re-export for tests and callers that import STAGES from here.
STAGES = DOCUMENT_SCAFFOLD_STAGES


def run_pipeline_job(document_id: str, job_id: str) -> None:
    """Open a sync SQLAlchemy session, run scaffold pipeline, commit."""
    from app.db.session import get_session_factory
    from app.services.pipeline_run_service import execute_scaffold_pipeline

    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        execute_scaffold_pipeline(session, uuid.UUID(document_id), job_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def run_document_pipeline(ctx: dict[str, Any], document_id: str) -> None:
    """
    ARQ entry: execute pipeline in a thread pool (sync SQLAlchemy + psycopg).

    `ctx` is the ARQ job context (`ctx['job_id']`, redis, etc.).
    """
    job_id = str(ctx.get("job_id", "unknown"))
    log.info("pipeline_job_start document_id=%s job_id=%s", document_id, job_id)
    await asyncio.to_thread(run_pipeline_job, document_id, job_id)
    log.info("pipeline_job_done document_id=%s job_id=%s", document_id, job_id)
