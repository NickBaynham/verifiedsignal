"""Fixtures for Postgres integration tests."""

from __future__ import annotations

import asyncio
import os

import psycopg
import pytest


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL not set — integration tests need Postgres with migrations 001 and 002 "
            "applied (see db/README.md)."
        )
    return url


@pytest.fixture
def intake_api_client(monkeypatch, database_url: str):
    """
    FastAPI client with real Postgres (DATABASE_URL), fake queue, and in-memory object storage.
    Use for POST /documents intake tests; requires migrations 001 + 002 applied.
    """
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("USE_FAKE_QUEUE", "true")
    monkeypatch.setenv("USE_FAKE_STORAGE", "true")

    from app.auth.dependencies import get_current_user
    from app.core.config import reset_settings_cache
    from app.db.session import reset_engine
    from app.main import create_app
    from app.services.event_service import reset_event_hub
    from app.services.queue_backend import close_job_queue
    from app.services.storage_service import reset_object_storage
    from fastapi.testclient import TestClient

    reset_settings_cache()
    reset_object_storage()
    reset_engine()
    reset_event_hub()
    asyncio.run(close_job_queue())

    async def _test_user_id() -> str:
        return "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    application = create_app()
    application.dependency_overrides[get_current_user] = _test_user_id
    with TestClient(application) as client:
        yield client
    application.dependency_overrides.pop(get_current_user, None)

    asyncio.run(close_job_queue())
    reset_engine()
    reset_event_hub()
    reset_object_storage()
    reset_settings_cache()


@pytest.fixture
def db_conn(database_url: str):
    """
    Connection per test; rolls back so tests do not persist data.
    Requires DDL already applied (migrations).
    """
    with psycopg.connect(database_url) as conn:
        conn.autocommit = False
        yield conn
        conn.rollback()
