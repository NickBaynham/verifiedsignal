"""Persistence helpers for document intake (Postgres canonical)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentSource

if TYPE_CHECKING:
    pass


def create_intake_row_created(
    session: Session,
    *,
    document_id: uuid.UUID,
    collection_id: uuid.UUID,
    original_filename: str,
    content_type: str | None,
    file_size: int,
    title: str | None,
) -> Document:
    """
    Insert canonical row in `created` before object storage upload completes.

    Tradeoff: a brief window exists where Postgres references bytes not yet in MinIO;
    `ingest_error` + `failed` status recover if upload fails.
    """
    doc = Document(
        id=document_id,
        collection_id=collection_id,
        title=title or original_filename,
        status="created",
        original_filename=original_filename,
        content_type=content_type,
        file_size=file_size,
        row_schema_version=2,
    )
    session.add(doc)
    session.flush()
    return doc


def mark_intake_failed(session: Session, document_id: uuid.UUID, message: str) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        return
    doc.status = "failed"
    doc.ingest_error = message[:8192]


def finalize_intake_after_upload(
    session: Session,
    *,
    document_id: uuid.UUID,
    storage_key: str,
    bucket: str,
    content_type: str | None,
    file_size: int,
) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        raise ValueError(f"document not found: {document_id}")
    doc.storage_key = storage_key
    doc.status = "queued"
    src = DocumentSource(
        document_id=document_id,
        source_kind="upload",
        locator=f"s3://{bucket}/{storage_key}",
        mime_type=content_type,
        byte_length=file_size,
        raw_metadata={"bucket": bucket, "storage_key": storage_key, "phase": "intake_raw"},
    )
    session.add(src)


def mark_enqueue_failed(session: Session, document_id: uuid.UUID, message: str) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        return
    doc.enqueue_error = message[:8192]


def get_document(session: Session, document_id: uuid.UUID) -> Document | None:
    return session.get(Document, document_id)


def get_document_by_storage_key(session: Session, storage_key: str) -> Document | None:
    stmt = select(Document).where(Document.storage_key == storage_key).limit(1)
    return session.scalars(stmt).first()
