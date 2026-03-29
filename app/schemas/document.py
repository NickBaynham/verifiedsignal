"""Pydantic models for document APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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


class DocumentListResponse(BaseModel):
    items: list[DocumentSummaryOut]
    total: int
    user_id: str
