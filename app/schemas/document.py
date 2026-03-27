"""Pydantic models for document APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
