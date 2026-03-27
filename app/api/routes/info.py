"""Service metadata."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import InfoResponse

router = APIRouter(tags=["info"])


@router.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    s = get_settings()
    return InfoResponse(
        service=s.app_name,
        environment=s.environment,
        api_prefix=s.api_v1_prefix,
        notes="OpenSearch is derived from Postgres; workers process documents asynchronously.",
    )
