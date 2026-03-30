"""Unit tests: fake OpenSearch index + async search_documents."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from app.core.config import reset_settings_cache
from app.services.opensearch_document_index import index_document_sync, reset_fake_opensearch_index
from app.services.search_service import search_documents


@pytest.mark.unit
def test_search_documents_fake_keyword_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_FAKE_OPENSEARCH", "true")
    reset_settings_cache()
    reset_fake_opensearch_index()

    did = uuid.uuid4()
    cid = uuid.uuid4()
    index_document_sync(
        document_id=did,
        collection_id=cid,
        title="Report",
        body_text="quarterly revenue audit",
        status="completed",
    )

    out = asyncio.run(search_documents("revenue", limit=10))
    assert out["index_status"] == "fake"
    assert out["total"] == 1
    assert out["hits"][0]["document_id"] == str(did)
    assert "revenue" in (out["hits"][0].get("snippet") or "")
