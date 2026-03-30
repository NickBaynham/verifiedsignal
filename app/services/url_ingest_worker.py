"""
Worker-side URL fetch → object storage → same finalize path as multipart intake.

Invoked by ARQ `fetch_url_and_ingest` (sync body suitable for `asyncio.to_thread`).
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import DocumentSource
from app.db.session import get_session_factory
from app.repositories import document_repository as doc_repo
from app.services.queue_service import enqueue_process_document_sync
from app.services.storage_service import ObjectStorage, build_raw_object_key, get_object_storage
from app.services.url_ingest_fetch import fetch_url_bytes

log = logging.getLogger("verifiedsignal.url_ingest.worker")


def _first_url_locator(session: Session, document_id: uuid.UUID) -> str | None:
    stmt = (
        select(DocumentSource.locator)
        .where(
            DocumentSource.document_id == document_id,
            DocumentSource.source_kind == "url",
        )
        .order_by(DocumentSource.created_at)
        .limit(1)
    )
    row = session.execute(stmt).first()
    return row[0] if row else None


def run_fetch_url_and_ingest_sync(document_id: str, settings: Settings | None = None) -> None:
    """
    Load document + URL source, GET bytes, upload to S3, finalize to `queued`, enqueue pipeline.

    Idempotent: if `storage_key` is already set, no-op.
    """
    settings = settings or get_settings()
    did = uuid.UUID(document_id)
    storage: ObjectStorage = get_object_storage()
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        doc = doc_repo.get_document(session, did)
        if doc is None:
            log.warning("url_ingest_missing_document document_id=%s", document_id)
            return
        if doc.storage_key:
            log.info("url_ingest_skip_already_stored document_id=%s", document_id)
            return
        if doc.status != "created":
            log.warning(
                "url_ingest_unexpected_status document_id=%s status=%s",
                document_id,
                doc.status,
            )
            return

        url = _first_url_locator(session, did)
        if not url:
            doc_repo.mark_intake_failed(session, did, "no url document_source row")
            session.commit()
            return

        try:
            body, ctype = fetch_url_bytes(url, settings)
        except ValueError as e:
            doc_repo.mark_intake_failed(session, did, str(e))
            session.commit()
            return

        if not body:
            doc_repo.mark_intake_failed(session, did, "empty response body")
            session.commit()
            return

        name = (doc.original_filename or "fetched").strip() or "fetched"
        storage_key = build_raw_object_key(did, name)

        try:
            storage.ensure_bucket()
            storage.upload_bytes(storage_key, body, ctype)
        except Exception as e:
            log.warning("url_ingest_storage_failed document_id=%s err=%s", document_id, e)
            doc_repo.mark_intake_failed(session, did, f"storage upload failed: {e}")
            session.commit()
            return

        doc_repo.finalize_intake_after_upload(
            session,
            document_id=did,
            storage_key=storage_key,
            bucket=storage.bucket,
            content_type=ctype,
            file_size=len(body),
        )
        session.commit()

        try:
            enqueue_process_document_sync(document_id)
        except Exception as e:
            doc_repo.mark_enqueue_failed(session, did, str(e))
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
