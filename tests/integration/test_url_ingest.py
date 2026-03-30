"""Integration: POST /documents/from-url and worker fetch path (Postgres + fake queue/storage)."""

from __future__ import annotations

import uuid

import pytest
from app.services.queue_backend import get_memory_queue
from app.services.url_ingest_worker import run_fetch_url_and_ingest_sync


@pytest.mark.integration
def test_post_from_url_accepts_and_enqueues_fetch_job(intake_api_client):
    r = intake_api_client.post(
        "/api/v1/documents/from-url",
        json={"url": "https://example.com/report.pdf", "title": "Report"},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "created"
    assert body["source_url"].startswith("https://example.com/")
    assert body["document_id"]
    assert body["job_id"]
    assert not body.get("enqueue_error")

    q = get_memory_queue()
    assert any(j[1] == "fetch_url_and_ingest" and j[2] == body["document_id"] for j in q.jobs), (
        q.jobs
    )


@pytest.mark.integration
def test_post_from_url_rejects_loopback(intake_api_client):
    r = intake_api_client.post(
        "/api/v1/documents/from-url",
        json={"url": "https://127.0.0.1/secrets"},
    )
    assert r.status_code == 400


@pytest.mark.integration
def test_fetch_worker_stores_bytes_and_enqueues_process_document(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    def _fake_fetch(_url: str, _settings, client=None):
        return b"url-ingest-body", "text/plain"

    monkeypatch.setattr(
        "app.services.url_ingest_worker.fetch_url_bytes",
        _fake_fetch,
    )

    r = intake_api_client.post(
        "/api/v1/documents/from-url",
        json={"url": "https://example.com/notes.txt"},
    )
    assert r.status_code == 202
    did = r.json()["document_id"]

    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import reset_engine

    reset_settings_cache()
    reset_engine()

    run_fetch_url_and_ingest_sync(did)

    one = intake_api_client.get(f"/api/v1/documents/{did}")
    assert one.status_code == 200
    detail = one.json()
    assert detail["status"] == "queued"
    assert detail["storage_key"]
    assert detail["file_size"] == len(b"url-ingest-body")

    kinds = {s["source_kind"] for s in detail["sources"]}
    assert "url" in kinds
    assert "upload" in kinds

    q = get_memory_queue()
    assert any(j[1] == "process_document" and j[2] == did for j in q.jobs)

    uuid.UUID(did)


@pytest.mark.integration
def test_fetch_worker_marks_failed_on_empty_body(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.services.url_ingest_worker.fetch_url_bytes",
        lambda *_a, **_k: (b"", "text/plain"),
    )

    r = intake_api_client.post(
        "/api/v1/documents/from-url",
        json={"url": "https://example.com/empty"},
    )
    did = r.json()["document_id"]

    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import reset_engine

    reset_settings_cache()
    reset_engine()

    run_fetch_url_and_ingest_sync(did)

    one = intake_api_client.get(f"/api/v1/documents/{did}")
    assert one.status_code == 200
    assert one.json()["status"] == "failed"
    assert one.json().get("ingest_error")


@pytest.mark.integration
def test_post_from_url_disabled_returns_400(intake_api_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("URL_INGEST_ENABLED", "false")
    from app.core.config import reset_settings_cache

    reset_settings_cache()
    try:
        r = intake_api_client.post(
            "/api/v1/documents/from-url",
            json={"url": "https://example.com/x"},
        )
        assert r.status_code == 400
    finally:
        monkeypatch.delenv("URL_INGEST_ENABLED", raising=False)
        reset_settings_cache()
