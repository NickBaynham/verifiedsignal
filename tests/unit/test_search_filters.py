"""Unit tests: SearchFilters → OpenSearch clauses and fake matcher."""

from __future__ import annotations

import pytest
from app.services.search_filters import (
    SearchFilters,
    fake_doc_matches_filters,
    opensearch_filter_clauses,
)


@pytest.mark.unit
def test_opensearch_filter_clauses_tags_and_collection():
    f = SearchFilters(
        collection_ids=("cid-1", "cid-2"),
        content_type="text/plain",
        status="completed",
        ingest_source="upload",
        tags_all=("t1", "t2"),
    )
    clauses = opensearch_filter_clauses(f)
    assert {"terms": {"collection_id": ["cid-1", "cid-2"]}} in clauses
    assert {"term": {"content_type": "text/plain"}} in clauses
    assert {"term": {"status": "completed"}} in clauses
    assert {"term": {"ingest_source": "upload"}} in clauses
    assert {"term": {"tags": "t1"}} in clauses
    assert {"term": {"tags": "t2"}} in clauses


@pytest.mark.unit
def test_fake_doc_matches_tags_and():
    doc = {
        "collection_id": "a",
        "content_type": "text/plain",
        "status": "completed",
        "ingest_source": "upload",
        "tags": ["x", "y"],
    }
    assert fake_doc_matches_filters(
        doc,
        SearchFilters(collection_ids=("a",), tags_all=("x", "y")),
    )
    assert not fake_doc_matches_filters(
        doc,
        SearchFilters(collection_ids=("a",), tags_all=("x", "z")),
    )


@pytest.mark.unit
def test_empty_collection_ids_matches_nothing():
    doc = {"collection_id": "a", "document_id": "1"}
    assert not fake_doc_matches_filters(doc, SearchFilters(collection_ids=tuple()))
