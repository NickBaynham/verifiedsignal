"""Search API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchResponse(BaseModel):
    query: str
    limit: int
    hits: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    index_status: str
    message: str | None = None
