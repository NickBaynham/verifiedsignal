"""
Integration: multipart intake hits Postgres, storage adapter, and queue.

Uses test doubles for S3 and Redis.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
from app.services.queue_backend import get_memory_queue


@pytest.mark.integration
def test_post_documents_multipart_happy_path(intake_api_client, database_url: str):
    files = {"file": ("note.txt", b"hello intake", "text/plain")}
    data = {"title": "My note"}
    r = intake_api_client.post("/api/v1/documents", files=files, data=data)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "queued"
    assert body["document_id"]
    assert body["storage_key"].startswith("raw/")
    assert body["storage_key"].endswith("note.txt")
    assert body["job_id"]
    assert not body.get("enqueue_error")

    q = get_memory_queue()
    assert len(q.jobs) == 1
    assert q.jobs[0][1] == body["document_id"]

    did = uuid.UUID(body["document_id"])
    with psycopg.connect(database_url) as conn:
        row = conn.execute(
            "SELECT status, storage_key, original_filename, file_size, content_type "
            "FROM documents WHERE id = %s",
            (did,),
        ).fetchone()
    assert row is not None
    assert row[0] == "queued"
    assert row[1] == body["storage_key"]
    assert row[2] == "note.txt"
    assert row[3] == len(b"hello intake")
    assert row[4] == "text/plain"

    with psycopg.connect(database_url) as conn:
        src = conn.execute(
            "SELECT source_kind, locator FROM document_sources WHERE document_id = %s",
            (did,),
        ).fetchone()
    assert src is not None
    assert src[0] == "upload"
    assert body["storage_key"] in src[1]


@pytest.mark.integration
def test_post_documents_rejects_empty_file(intake_api_client):
    files = {"file": ("empty.txt", b"", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 400


@pytest.mark.integration
def test_post_documents_rejects_bad_collection_uuid(intake_api_client):
    files = {"file": ("a.txt", b"x", "text/plain")}
    r = intake_api_client.post(
        "/api/v1/documents",
        files=files,
        data={"collection_id": "not-a-uuid"},
    )
    assert r.status_code == 400


@pytest.mark.integration
def test_enqueue_failure_keeps_queued_and_sets_enqueue_error(intake_api_client, monkeypatch):
    import app.services.document_service as ds

    def boom(_did: str) -> str:
        raise RuntimeError("enqueue simulated failure")

    monkeypatch.setattr(ds, "enqueue_process_document_sync", boom)

    files = {"file": ("jobfail.txt", b"data", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "queued"
    assert body["storage_key"]
    assert body["job_id"] is None
    assert body.get("enqueue_error")
    assert "simulated" in body["enqueue_error"].lower()


@pytest.mark.e2e
@pytest.mark.integration
def test_intake_flow_api_db_queue(intake_api_client, database_url: str):
    """Minimal e2e-style intake: HTTP → persisted document → job recorded on fake queue."""
    files = {"file": ("e2e.bin", b"\x00\x01\x02", "application/octet-stream")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200
    did = r.json()["document_id"]
    uuid.UUID(did)
    with psycopg.connect(database_url) as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE id = %s::uuid AND status = 'queued'",
            (did,),
        ).fetchone()[0]
    assert n == 1
    assert any(j[1] == did for j in get_memory_queue().jobs)
