"""Search against OpenSearch (derived index). Not implemented — stub for API contract."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


async def search_documents(query: str, limit: int = 10) -> dict[str, Any]:
    """
    Placeholder: real implementation will query OpenSearch using indexed fields
    rebuilt from Postgres. Returns an empty result set so the API stays runnable.
    """
    _ = get_settings()
    return {
        "query": query,
        "limit": limit,
        "hits": [],
        "total": 0,
        "index_status": "stub",
        "message": "OpenSearch query not wired; index is disposable and rebuildable from Postgres.",
    }
