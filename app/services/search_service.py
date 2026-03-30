"""Search against OpenSearch (or in-memory fake) with metadata filters and optional facets."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.document_access import resolve_accessible_collection_ids
from app.services.opensearch_document_index import search_documents_sync
from app.services.search_filters import SearchFilters


def build_search_filters(
    db: Session,
    auth_sub: str | None,
    *,
    collection_id: uuid.UUID | None,
    content_type: str | None,
    status: str | None,
    ingest_source: str | None,
    tags: list[str] | None,
) -> SearchFilters:
    settings = get_settings()
    tlist = [x.strip() for x in (tags or []) if x and str(x).strip()]

    if ingest_source is not None and ingest_source not in ("upload", "url"):
        raise HTTPException(status_code=400, detail="ingest_source must be upload or url")

    if auth_sub is None:
        col_tuple: tuple[str, ...] | None = None
    else:
        allowed = resolve_accessible_collection_ids(db, auth_sub, settings)
        if collection_id is not None:
            if collection_id not in allowed:
                raise HTTPException(status_code=403, detail="collection_id not accessible")
            col_tuple = (str(collection_id),)
        else:
            col_tuple = tuple(str(x) for x in allowed)

    return SearchFilters(
        collection_ids=col_tuple,
        content_type=content_type,
        status=status,
        ingest_source=ingest_source,
        tags_all=tuple(tlist),
    )


async def search_documents(
    db: Session,
    auth_sub: str | None,
    query: str,
    limit: int = 10,
    *,
    collection_id: uuid.UUID | None = None,
    content_type: str | None = None,
    status: str | None = None,
    ingest_source: str | None = None,
    tags: list[str] | None = None,
    include_facets: bool = False,
) -> dict[str, Any]:
    """
    Full-text on title, body, and flattened metadata text; bool filters on index fields.

    With a valid Bearer token, results are restricted to collections the user may access.
    Without a token, behavior is unchanged from early phases (no collection ACL on search).
    """
    settings = get_settings()
    filters = build_search_filters(
        db,
        auth_sub,
        collection_id=collection_id,
        content_type=content_type,
        status=status,
        ingest_source=ingest_source,
        tags=tags,
    )
    result = await asyncio.to_thread(
        search_documents_sync,
        query,
        limit=limit,
        filters=filters,
        include_facets=include_facets,
        settings=settings,
    )
    return {
        "query": query,
        "limit": limit,
        "hits": result["hits"],
        "total": result["total"],
        "index_status": result["index_status"],
        "message": result.get("message"),
        "facets": result.get("facets"),
    }
