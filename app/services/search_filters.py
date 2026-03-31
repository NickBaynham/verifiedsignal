"""Structured filters for document search (OpenSearch bool filter + fake index)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchFilters:
    """
    ``collection_ids``:
      - ``None`` — do not filter by collection (only when ``VERIFIEDSIGNAL_REQUIRE_AUTH_SEARCH=false``).
      - empty tuple — no accessible collections (return no hits).
      - non-empty — restrict to these collection id strings.
    """

    collection_ids: tuple[str, ...] | None = None
    content_type: str | None = None
    status: str | None = None
    ingest_source: str | None = None
    tags_all: tuple[str, ...] = ()


def opensearch_filter_clauses(filters: SearchFilters) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    if filters.collection_ids is not None:
        if len(filters.collection_ids) == 0:
            clauses.append({"term": {"document_id": "__vs_no_collection_access__"}})
        else:
            clauses.append({"terms": {"collection_id": list(filters.collection_ids)}})
    if filters.content_type:
        clauses.append({"term": {"content_type": filters.content_type}})
    if filters.status:
        clauses.append({"term": {"status": filters.status}})
    if filters.ingest_source:
        clauses.append({"term": {"ingest_source": filters.ingest_source}})
    for t in filters.tags_all:
        if t:
            clauses.append({"term": {"tags": t}})
    return clauses


def fake_doc_matches_filters(doc: dict[str, Any], filters: SearchFilters) -> bool:
    if filters.collection_ids is not None:
        if len(filters.collection_ids) == 0:
            return False
        if doc.get("collection_id") not in filters.collection_ids:
            return False
    if filters.content_type and doc.get("content_type") != filters.content_type:
        return False
    if filters.status and doc.get("status") != filters.status:
        return False
    if filters.ingest_source and doc.get("ingest_source") != filters.ingest_source:
        return False
    if filters.tags_all:
        dtags = doc.get("tags") or []
        if not isinstance(dtags, list):
            return False
        for t in filters.tags_all:
            if t not in dtags:
                return False
    return True
