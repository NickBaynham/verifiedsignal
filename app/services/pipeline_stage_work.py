"""Concrete work for scaffold pipeline stages (ingest, enrich, score hooks)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Document
from app.repositories import pipeline_repository as pipe_repo
from app.services.heuristic_score import write_heuristic_canonical_score
from app.services.queue_service import enqueue_score_document_sync
from app.services.storage_service import ObjectStorage, get_object_storage

log = logging.getLogger("verifiedsignal.pipeline.stages")


def ingest_verify_storage_stage(
    session: Session,
    *,
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    step_index: int,
    job_id: str,
    storage: ObjectStorage | None = None,
) -> None:
    """Confirm raw object exists before extract (avoids full read here)."""
    storage = storage or get_object_storage()
    doc = session.get(Document, document_id)
    if doc is None:
        return
    if not doc.storage_key:
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "ingest_skipped",
            "ingest",
            {"reason": "no_storage_key", "job_id": job_id},
        )
        return
    try:
        ok = storage.object_exists(doc.storage_key)
    except Exception as e:
        log.warning("ingest_head_failed document_id=%s err=%s", document_id, e)
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "ingest_failed",
            "ingest",
            {"reason": type(e).__name__, "job_id": job_id},
        )
        return
    if not ok:
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "ingest_failed",
            "ingest",
            {"reason": "object_missing", "job_id": job_id},
        )
        return
    pipe_repo.append_event(
        session,
        run_id,
        step_index,
        "ingest_verified",
        "ingest",
        {
            "job_id": job_id,
            "storage_key": doc.storage_key,
            "file_size": doc.file_size,
        },
    )


def enrich_stage(
    session: Session,
    *,
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    step_index: int,
    job_id: str,
) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        return
    body = doc.body_text or ""
    word_count = len(body.split())
    pipe_repo.append_event(
        session,
        run_id,
        step_index,
        "enrich_complete",
        "enrich",
        {
            "job_id": job_id,
            "mode": "text_stats",
            "word_count": word_count,
            "char_count": len(body),
            "has_body_text": bool(body.strip()),
        },
    )


def score_enqueue_stage(
    session: Session,
    *,
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    step_index: int,
    job_id: str,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    doc = session.get(Document, document_id)
    if doc is not None:
        write_heuristic_canonical_score(
            session,
            document_id=document_id,
            pipeline_run_id=run_id,
            body_text=doc.body_text,
        )

    if not settings.enqueue_score_after_pipeline:
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "score_skipped",
            "score",
            {"job_id": job_id, "reason": "enqueue_score_after_pipeline_disabled"},
        )
        return
    try:
        score_job_id = enqueue_score_document_sync(str(document_id))
    except Exception as e:
        log.warning("score_enqueue_failed document_id=%s err=%s", document_id, e)
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "score_enqueue_failed",
            "score",
            {"job_id": job_id, "reason": type(e).__name__},
        )
        return
    pipe_repo.append_event(
        session,
        run_id,
        step_index,
        "score_job_enqueued",
        "score",
        {"job_id": job_id, "score_job_id": score_job_id},
    )
