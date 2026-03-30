"""Extract plain text from stored bytes and index into OpenSearch (worker pipeline)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Document
from app.repositories import pipeline_repository as pipe_repo
from app.services.document_text_extract import extract_plain_text_from_bytes
from app.services.opensearch_document_index import index_document_sync
from app.services.storage_service import ObjectStorage, get_object_storage

log = logging.getLogger("verifiedsignal.pipeline.extract_index")


def extract_body_text_stage(
    session: Session,
    *,
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    step_index: int,
    job_id: str,
    storage: ObjectStorage | None = None,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    storage = storage or get_object_storage()
    doc = session.get(Document, document_id)
    if doc is None:
        return
    if not doc.storage_key:
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "extract_skipped",
            "extract",
            {"reason": "no_storage_key", "job_id": job_id},
        )
        return
    try:
        raw = storage.get_bytes(doc.storage_key)
    except KeyError:
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "extract_failed",
            "extract",
            {"reason": "object_missing", "job_id": job_id},
        )
        return
    except Exception as e:
        log.warning("extract_read_failed document_id=%s err=%s", document_id, e)
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "extract_failed",
            "extract",
            {"reason": type(e).__name__, "job_id": job_id},
        )
        return

    text, note = extract_plain_text_from_bytes(raw, doc.content_type)
    doc.body_text = text if text else None
    pipe_repo.append_event(
        session,
        run_id,
        step_index,
        "extract_complete",
        "extract",
        {
            "job_id": job_id,
            "bytes": len(raw),
            "chars": len(text or ""),
            "note": note,
        },
    )


def index_opensearch_stage(
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
    if doc is None:
        return
    try:
        index_document_sync(
            document_id=doc.id,
            collection_id=doc.collection_id,
            title=doc.title,
            body_text=doc.body_text,
            status=doc.status,
            settings=settings,
        )
    except Exception as e:
        log.warning("index_failed document_id=%s err=%s", document_id, e)
        pipe_repo.append_event(
            session,
            run_id,
            step_index,
            "index_failed",
            "index",
            {"reason": str(e)[:500], "job_id": job_id},
        )
        return

    pipe_repo.append_event(
        session,
        run_id,
        step_index,
        "index_complete",
        "index",
        {"job_id": job_id},
    )
