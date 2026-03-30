"""Pipeline status API (read-only)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PipelineEventOut(BaseModel):
    id: uuid.UUID
    step_index: int
    event_type: str
    stage: str | None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PipelineRunOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    stage: str
    started_at: datetime | None
    completed_at: datetime | None
    error_detail: dict[str, Any] | None = None
    run_metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentPipelineOut(BaseModel):
    document_id: uuid.UUID
    document_status: str
    run: PipelineRunOut | None = None
    events: list[PipelineEventOut] = Field(default_factory=list)
