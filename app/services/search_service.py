"""Search against OpenSearch (or in-memory fake when USE_FAKE_OPENSEARCH=true)."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import get_settings
from app.services.opensearch_document_index import search_keyword_sync


async def search_documents(query: str, limit: int = 10) -> dict[str, Any]:
    """
    Keyword search on indexed `title` and `body_text` (worker extract + index stages).

    Uses OpenSearch HTTP unless `USE_FAKE_OPENSEARCH=true` (tests).
    """
    settings = get_settings()
    result = await asyncio.to_thread(search_keyword_sync, query, limit=limit, settings=settings)
    return {
        "query": query,
        "limit": limit,
        "hits": result["hits"],
        "total": result["total"],
        "index_status": result["index_status"],
        "message": result.get("message"),
    }
