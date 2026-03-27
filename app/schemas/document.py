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
