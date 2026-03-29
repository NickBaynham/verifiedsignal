"""List collections the caller may access (same rule as documents)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Collection
from app.repositories import collection_repository as coll_repo
from app.services.document_access import resolve_accessible_collection_ids


def list_collections_for_user(
    session: Session,
    auth_sub: str,
    settings: Settings | None = None,
) -> list[tuple[Collection, int]]:
    """
    Return list of (Collection ORM row, document_count) for accessible collections.
    """
    settings = settings or get_settings()
    ids = resolve_accessible_collection_ids(session, auth_sub, settings)
    rows = coll_repo.list_collections_by_ids(session, ids)
    counts = coll_repo.count_documents_per_collection(session, ids)
    return [(c, counts.get(c.id, 0)) for c in rows]
