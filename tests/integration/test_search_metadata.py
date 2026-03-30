"""Integration: user_metadata intake, index projection, search filters, facets (fake OpenSearch)."""

from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
def test_search_filters_by_user_metadata_tag_and_facets(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("meta.txt", b"hello meta-search-token-abc", "text/plain")}
    data = {"metadata": '{"tags":["facet-meta-tag"],"label":"contract"}'}
    r = intake_api_client.post("/api/v1/documents", files=files, data=data)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    detail = intake_api_client.get(f"/api/v1/documents/{did}")
    assert detail.status_code == 200
    assert detail.json().get("user_metadata", {}).get("tags") == ["facet-meta-tag"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-meta-search-test")
        sess.commit()
    finally:
        sess.close()

    sr = intake_api_client.get(
        "/api/v1/search",
        params={"q": "meta-search-token-abc", "tags": "facet-meta-tag"},
    )
    assert sr.status_code == 200, sr.text
    j = sr.json()
    assert j["index_status"] == "fake"
    assert j["total"] >= 1
    assert any(h.get("document_id") == did for h in j["hits"])

    bad = intake_api_client.get(
        "/api/v1/search",
        params={"q": "meta-search-token-abc", "tags": "wrong-tag"},
    )
    assert bad.json()["total"] == 0

    fx = intake_api_client.get(
        "/api/v1/search",
        params={"q": "", "include_facets": "true", "limit": 5},
    )
    assert fx.status_code == 200
    facets = fx.json().get("facets") or {}
    assert "tags" in facets
    assert "ingest_source" in facets
