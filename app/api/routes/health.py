"""Liveness and dependency health."""

from __future__ import annotations

from fastapi import APIRouter

from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_ok = check_database_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="up" if db_ok else "down",
    )
