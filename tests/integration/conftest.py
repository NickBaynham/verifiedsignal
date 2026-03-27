"""Fixtures for Postgres integration tests."""

from __future__ import annotations

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
            "DATABASE_URL not set — integration tests need Postgres with migrations applied. "
            "Example: docker compose up -d postgres && "
            "docker compose exec -T postgres psql -U veridoc -d veridoc -v ON_ERROR_STOP=1 "
            "< db/migrations/001_initial_schema.up.sql"
        )
    return url


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
