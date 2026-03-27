"""Shared FastAPI dependencies (DB session, object storage, etc.)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db
from app.services.storage_service import ObjectStorage, get_object_storage


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_object_storage_dep() -> ObjectStorage:
    """Request-scoped accessor; override in tests with `dependency_overrides`."""
    return get_object_storage()
