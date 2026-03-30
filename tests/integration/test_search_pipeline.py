"""Integration: extract → index (fake OpenSearch) → GET /search."""

from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
def test_search_finds_text_after_intake_and_pipeline(
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

    files = {"file": ("notes.txt", b"unique-keyword-xyz", "text/plain")}
    data = {"title": "Unique Title"}
    r = intake_api_client.post("/api/v1/documents", files=files, data=data)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-search-test")
        sess.commit()
    finally:
        sess.close()

    sr = intake_api_client.get("/api/v1/search", params={"q": "unique-keyword-xyz"})
    assert sr.status_code == 200, sr.text
    j = sr.json()
    assert j["index_status"] == "fake"
    assert j["total"] >= 1
    assert any(h.get("document_id") == did for h in j["hits"])

    detail = intake_api_client.get(f"/api/v1/documents/{did}")
    assert detail.status_code == 200
    assert "unique-keyword-xyz" in (detail.json().get("body_text") or "")
