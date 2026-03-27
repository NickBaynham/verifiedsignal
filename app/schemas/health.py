"""Health / info response models."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str


class InfoResponse(BaseModel):
    service: str
    environment: str
    api_prefix: str
    notes: str
