"""Pydantic models for document APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UrlIntakeRequest(BaseModel):
    """Remote URL; worker fetches bytes then matches multipart intake (storage + pipeline)."""

    url: str = Field(..., min_length=1, max_length=8192)
    collection_id: str | None = Field(
        default=None,
        description="Target collection UUID; defaults to VERIFIEDSIGNAL_DEFAULT_COLLECTION_ID",
    )
    title: str | None = Field(default=None, max_length=2048)


class UrlIntakeResponse(BaseModel):
    """Accepted: `created` until bytes land; then `queued` and `process_document`."""

    document_id: str
    status: str
    source_url: str
    job_id: str | None = None
    enqueue_error: str | None = None


class DocumentCreate(BaseModel):
    title: str | None = Field(default=None, max_length=2048)
    source_uri: str | None = Field(default=None, max_length=8192)
    metadata: dict | None = Field(default=None, description="Opaque client metadata")


class DocumentSubmitResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class IntakeResponse(BaseModel):
    """
    Response after successful file intake.

    Row is `queued` once storage and DB finalize succeeded.
    """

    document_id: str
    status: str
    storage_key: str
    job_id: str | None = None
    enqueue_error: str | None = None


class DocumentSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    source_kind: str
    locator: str
    mime_type: str | None = None
    byte_length: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    collection_id: uuid.UUID
    title: str | None = None
    external_key: str | None = None
    status: str
    original_filename: str | None = None
    content_type: str | None = None
    file_size: int | None = None
    storage_key: str | None = None
    ingest_error: str | None = None
    enqueue_error: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailOut(DocumentSummaryOut):
    sources: list[DocumentSourceOut] = Field(default_factory=list)
    body_text: str | None = Field(
        default=None,
        description="Plain text extracted for search (omitted in list responses).",
    )


class DocumentListResponse(BaseModel):
    items: list[DocumentSummaryOut]
    total: int
    user_id: str
