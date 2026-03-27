"""
Document intake: Postgres canonical row + MinIO/S3 + worker enqueue.

Ordering (intentional):
1) Validate input
2) INSERT document (`created`) — canonical identity exists for audit
3) Upload bytes to object storage
4) UPDATE to `queued`, set storage_key, INSERT document_sources
5) Enqueue `process_document`; on failure set enqueue_error, keep `queued` and storage

We use `created` only briefly; if upload fails the row moves to `failed` with ingest_error.
Skipping a separate user-visible "created" response keeps the client model simple: they either
get `queued` (maybe without job_id) or an error before any row exists.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from io import BytesIO

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.repositories import document_repository as doc_repo
from app.services.event_service import get_event_hub
from app.services.exceptions import IntakeValidationError, StorageUploadError
from app.services.queue_service import enqueue_process_document_sync
from app.services.storage_service import ObjectStorage, build_raw_object_key, get_object_storage

log = logging.getLogger("verifiedsignal.intake")


def _read_upload_to_limit(raw: bytes, *, max_bytes: int) -> None:
    if len(raw) > max_bytes:
        raise IntakeValidationError(f"file exceeds max size of {max_bytes} bytes")
    if len(raw) == 0:
        raise IntakeValidationError("empty file")


def resolve_collection_id(
    collection_id_param: str | None,
    settings: Settings,
) -> uuid.UUID:
    if collection_id_param is None or collection_id_param.strip() == "":
        if settings.default_collection_id is None:
            raise IntakeValidationError(
                "collection_id is required (or set VERIFIEDSIGNAL_DEFAULT_COLLECTION_ID)"
            )
        return settings.default_collection_id
    try:
        return uuid.UUID(collection_id_param.strip())
    except ValueError as e:
        raise IntakeValidationError("invalid collection_id UUID") from e


def run_file_intake(
    session: Session,
    *,
    file_bytes: bytes,
    original_filename: str,
    content_type: str | None,
    title: str | None,
    collection_id_param: str | None,
    storage: ObjectStorage | None = None,
    settings: Settings | None = None,
) -> dict:
    """
    Synchronous intake pipeline. Caller owns session lifecycle (request-scoped).
    Returns a dict suitable for IntakeResponse.
    """
    settings = settings or get_settings()
    storage = storage or get_object_storage()

    name = (original_filename or "").strip()
    if not name:
        raise IntakeValidationError("original filename is required")

    _read_upload_to_limit(file_bytes, max_bytes=settings.max_upload_bytes)
    collection_id = resolve_collection_id(collection_id_param, settings)

    document_id = uuid.uuid4()
    storage_key = build_raw_object_key(document_id, name)

    log.info(
        "intake_start document_id=%s collection_id=%s bytes=%s key=%s",
        document_id,
        collection_id,
        len(file_bytes),
        storage_key,
    )

    doc_repo.create_intake_row_created(
        session,
        document_id=document_id,
        collection_id=collection_id,
        original_filename=name,
        content_type=content_type,
        file_size=len(file_bytes),
        title=title,
    )
    session.commit()

    try:
        storage.ensure_bucket()
        storage.upload_bytes(storage_key, file_bytes, content_type)
    except StorageUploadError as e:
        log.warning("intake_storage_failed document_id=%s err=%s", document_id, e)
        doc_repo.mark_intake_failed(session, document_id, str(e))
        session.commit()
        raise StorageUploadError(str(e), document_id=document_id) from e

    doc_repo.finalize_intake_after_upload(
        session,
        document_id=document_id,
        storage_key=storage_key,
        bucket=storage.bucket,
        content_type=content_type,
        file_size=len(file_bytes),
    )
    session.commit()

    job_id: str | None = None
    enqueue_error: str | None = None
    try:
        job_id = enqueue_process_document_sync(str(document_id))
    except Exception as e:
        enqueue_error = str(e)[:8192]
        log.error("intake_enqueue_failed document_id=%s err=%s", document_id, enqueue_error)
        doc_repo.mark_enqueue_failed(session, document_id, enqueue_error)
        session.commit()

    if job_id:
        asyncio.run(
            get_event_hub().publish(
                "document_queued",
                {"document_id": str(document_id), "job_id": job_id, "storage_key": storage_key},
            )
        )

    log.info(
        "intake_complete document_id=%s job_id=%s enqueue_error=%s",
        document_id,
        job_id,
        enqueue_error,
    )

    return {
        "document_id": str(document_id),
        "status": "queued",
        "job_id": job_id,
        "storage_key": storage_key,
        "enqueue_error": enqueue_error,
    }


def upload_streaming_intake(
    session: Session,
    *,
    fileobj,
    original_filename: str,
    content_type: str | None,
    title: str | None,
    collection_id_param: str | None,
    storage: ObjectStorage | None = None,
    settings: Settings | None = None,
) -> dict:
    """Read entire file into memory with size limit, then delegate to run_file_intake."""
    settings = settings or get_settings()
    storage = storage or get_object_storage()
    chunks: list[bytes] = []
    total = 0
    max_b = settings.max_upload_bytes
    while True:
        chunk = fileobj.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_b:
            raise IntakeValidationError(f"file exceeds max size of {max_b} bytes")
        chunks.append(chunk)
    data = b"".join(chunks)
    return run_file_intake(
        session,
        file_bytes=data,
        original_filename=original_filename,
        content_type=content_type,
        title=title,
        collection_id_param=collection_id_param,
        storage=storage,
        settings=settings,
    )


# Back-compat: streaming upload used by API; expose BytesIO helper for tests
def run_file_intake_from_bytesio(
    session: Session,
    *,
    buf: BytesIO,
    original_filename: str,
    content_type: str | None,
    title: str | None,
    collection_id_param: str | None,
    storage: ObjectStorage | None = None,
    settings: Settings | None = None,
) -> dict:
    return run_file_intake(
        session,
        file_bytes=buf.read(),
        original_filename=original_filename,
        content_type=content_type,
        title=title,
        collection_id_param=collection_id_param,
        storage=storage,
        settings=settings,
    )
