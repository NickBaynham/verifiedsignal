"""E2E-style HTTP checks for search (uses in-memory index via api_client fixture)."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
@pytest.mark.api
def test_search_returns_fake_index_and_empty_hits_without_documents(api_client) -> None:
    r = api_client.get("/api/v1/search", params={"q": "anything", "limit": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["index_status"] == "fake"
    assert body["hits"] == []
    assert body["total"] == 0
