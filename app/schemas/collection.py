"""Pydantic models for collection APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    document_count: int = Field(ge=0, description="Documents in this collection")
    created_at: datetime


class CollectionListResponse(BaseModel):
    collections: list[CollectionOut]
