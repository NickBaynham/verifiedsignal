"""Integration: collections API and scaffold pipeline persistence (Postgres)."""

from __future__ import annotations

import uuid

import psycopg
import pytest


@pytest.mark.integration
def test_list_collections_includes_default_inbox(intake_api_client):
    r = intake_api_client.get("/api/v1/collections")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "collections" in data
    assert len(data["collections"]) >= 1
    slugs = {c["slug"] for c in data["collections"]}
    assert "default-inbox" in slugs
    row = next(c for c in data["collections"] if c["slug"] == "default-inbox")
    assert row["name"] == "Default Inbox"
    assert "document_count" in row
    assert row["document_count"] >= 0


@pytest.mark.integration
def test_list_collections_document_count_after_intake(intake_api_client):
    before = intake_api_client.get("/api/v1/collections").json()
    default_before = next(
        c["document_count"] for c in before["collections"] if c["slug"] == "default-inbox"
    )

    files = {"file": ("counted.txt", b"abc", "text/plain")}
    ir = intake_api_client.post("/api/v1/documents", files=files)
    assert ir.status_code == 200

    after = intake_api_client.get("/api/v1/collections").json()
    default_after = next(
        c["document_count"] for c in after["collections"] if c["slug"] == "default-inbox"
    )
    assert default_after == default_before + 1


@pytest.mark.integration
def test_scaffold_pipeline_persists_run_events_and_completes_document(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.pipeline_run_service import execute_scaffold_pipeline

    reset_settings_cache()
    reset_engine()

    files = {"file": ("pipe.txt", b"data", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-integration-test")
        sess.commit()
    finally:
        sess.close()

    with psycopg.connect(database_url) as conn:
        st = conn.execute(
            "SELECT status FROM documents WHERE id = %s::uuid",
            (did,),
        ).fetchone()[0]
        assert st == "completed"

        pr = conn.execute(
            "SELECT status, stage FROM pipeline_runs WHERE document_id = %s::uuid "
            "ORDER BY created_at DESC LIMIT 1",
            (did,),
        ).fetchone()
        assert pr is not None
        assert pr[0] == "succeeded"
        assert pr[1] == "finalize"

        ev_count = conn.execute(
            """
            SELECT COUNT(*) FROM pipeline_events pe
            INNER JOIN pipeline_runs pr ON pr.id = pe.pipeline_run_id
            WHERE pr.document_id = %s::uuid
            """,
            (did,),
        ).fetchone()[0]
        assert ev_count == 7
