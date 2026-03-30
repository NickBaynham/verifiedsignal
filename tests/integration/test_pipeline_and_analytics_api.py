"""Integration: HTTP surface for pipeline status and collection analytics.

Uses Postgres and fake OpenSearch (via `intake_api_client` / env). Failures here usually indicate
API contract, auth/tenancy, or service wiring — not the worker ARQ entrypoint alone.
"""

from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
def test_get_document_pipeline_after_scaffold_returns_run_and_events(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Happy path: persisted pipeline matches GET /documents/{id}/pipeline shape."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("pipeline_api.txt", b"pipeline-api-body", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-pipeline-api-test")
        sess.commit()
    finally:
        sess.close()

    pr = intake_api_client.get(f"/api/v1/documents/{did}/pipeline")
    assert pr.status_code == 200, pr.text
    body = pr.json()
    assert body["document_id"] == did
    assert body["document_status"] == "completed"
    assert body["run"] is not None
    assert body["run"]["status"] == "succeeded"
    assert body["run"]["stage"] == "finalize"
    assert body["run"]["document_id"] == did
    events = body["events"]
    assert len(events) == 12
    types = [e["event_type"] for e in events]
    assert types[0] == "pipeline_started"
    assert "enrich_complete" in types
    enrich_ev = next(e for e in events if e["event_type"] == "enrich_complete")
    assert enrich_ev["payload"].get("mode") == "text_stats"
    assert enrich_ev["payload"].get("word_count") == 1


@pytest.mark.integration
def test_get_document_pipeline_queued_without_run_returns_null_run(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Intake only: no pipeline row yet — API still returns 200 with run=null (UI polling)."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("no_pipeline_yet.txt", b"x", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    pr = intake_api_client.get(f"/api/v1/documents/{did}/pipeline")
    assert pr.status_code == 200, pr.text
    body = pr.json()
    assert body["document_id"] == did
    assert body["document_status"] == "queued"
    assert body["run"] is None
    assert body["events"] == []


@pytest.mark.integration
def test_get_document_pipeline_unknown_id_returns_404(intake_api_client):
    missing = uuid.uuid4()
    pr = intake_api_client.get(f"/api/v1/documents/{missing}/pipeline")
    assert pr.status_code == 404


@pytest.mark.integration
def test_get_collection_analytics_after_pipeline(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Analytics combines OpenSearch facets (fake index) + Postgres canonical score rollups."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {
        "file": (
            "analytics.txt",
            b"analytics-doc-token",
            "text/plain",
        )
    }
    meta = '{"tags":["analytics-tag"],"label":"integration"}'
    r = intake_api_client.post(
        "/api/v1/documents",
        files=files,
        data={"metadata": meta},
    )
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-analytics-api-test")
        sess.commit()
    finally:
        sess.close()

    detail = intake_api_client.get(f"/api/v1/documents/{did}")
    assert detail.status_code == 200, detail.text
    collection_id = detail.json()["collection_id"]

    ar = intake_api_client.get(f"/api/v1/collections/{collection_id}/analytics")
    assert ar.status_code == 200, ar.text
    data = ar.json()
    assert data["collection_id"] == collection_id
    assert data["index_status"] == "fake"
    assert data["index_total"] >= 1
    facets = data.get("facets") or {}
    assert "ingest_source" in facets
    assert "status" in facets
    assert "tags" in facets
    pg = data["postgres"]
    assert pg["document_count"] >= 1
    assert pg["scored_documents"] >= 1
    assert pg["avg_factuality"] is not None or pg["avg_ai_probability"] is not None

    tag_buckets = {b["key"]: b["count"] for b in facets["tags"]}
    assert tag_buckets.get("analytics-tag", 0) >= 1


@pytest.mark.integration
def test_collection_analytics_forbidden_for_other_tenant_collection(jwt_integration_client):
    """403 isolates tenancy bugs from empty analytics or index issues."""
    client, make_token = jwt_integration_client
    sub_a = str(uuid.uuid4())
    sub_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {make_token(sub=sub_a, email='owner-a@example.com')}"}
    headers_b = {"Authorization": f"Bearer {make_token(sub=sub_b, email='owner-b@example.com')}"}

    r = client.get("/api/v1/collections", headers=headers_a)
    assert r.status_code == 200, r.text
    collection_id = r.json()["collections"][0]["id"]

    ar = client.get(f"/api/v1/collections/{collection_id}/analytics", headers=headers_b)
    assert ar.status_code == 403
    assert "not accessible" in (ar.json().get("detail") or "").lower()
