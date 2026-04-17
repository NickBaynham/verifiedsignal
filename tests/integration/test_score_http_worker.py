"""Integration: async score_document job with HTTP scorer (mocked transport)."""

from __future__ import annotations

import uuid

import pytest


def _fake_post_remote_score_ok(**_kwargs):
    return (
        200,
        {
            "schema_version": 1,
            "factuality_score": 0.82,
            "ai_generation_probability": 0.18,
            "confidence_score": 0.9,
            "metadata": {"provider": "test-mock"},
        },
        12.5,
    )


@pytest.mark.integration
def test_score_http_worker_inserts_document_score_row(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SCORE_ASYNC_BACKEND", "http")
    monkeypatch.setenv("SCORE_HTTP_URL", "https://scorer.example/score")
    monkeypatch.setenv("SCORE_API_PROMOTE_CANONICAL", "false")
    monkeypatch.setattr(
        "app.services.score_document_worker.post_remote_score",
        _fake_post_remote_score_ok,
    )

    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline
    from app.services.score_document_worker import run_score_document_sync

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("http-score.txt", b"unique-http-score-body", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-http-score-test")
        sess.commit()
    finally:
        sess.close()

    run_score_document_sync(did)

    import psycopg

    with psycopg.connect(database_url) as conn:
        rows = conn.execute(
            """
            SELECT scorer_name, is_canonical, factuality_score::float, score_payload->>'job_status'
            FROM document_scores
            WHERE document_id = %s::uuid
            ORDER BY scorer_name
            """,
            (did,),
        ).fetchall()

    names = [row[0] for row in rows]
    assert "verifiedsignal_heuristic" in names
    assert "verifiedsignal_http" in names
    http_row = next(x for x in rows if x[0] == "verifiedsignal_http")
    assert http_row[1] is False  # promote off
    assert http_row[2] == pytest.approx(0.82)
    assert http_row[3] == "completed"


@pytest.mark.integration
def test_score_http_worker_idempotent_second_call_no_duplicate(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SCORE_ASYNC_BACKEND", "http")
    monkeypatch.setenv("SCORE_HTTP_URL", "https://scorer.example/score")
    monkeypatch.setattr(
        "app.services.score_document_worker.post_remote_score",
        _fake_post_remote_score_ok,
    )

    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline
    from app.services.score_document_worker import run_score_document_sync

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("idem.txt", b"idem-body", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-idem-test")
        sess.commit()
    finally:
        sess.close()

    run_score_document_sync(did)
    run_score_document_sync(did)

    import psycopg

    with psycopg.connect(database_url) as conn:
        n = conn.execute(
            """
            SELECT COUNT(*) FROM document_scores
            WHERE document_id = %s::uuid AND scorer_name = 'verifiedsignal_http'
            """,
            (did,),
        ).fetchone()[0]
    assert n == 1


@pytest.mark.integration
def test_score_http_promote_canonical_demotes_heuristic(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SCORE_ASYNC_BACKEND", "http")
    monkeypatch.setenv("SCORE_HTTP_URL", "https://scorer.example/score")
    monkeypatch.setenv("SCORE_API_PROMOTE_CANONICAL", "true")
    monkeypatch.setattr(
        "app.services.score_document_worker.post_remote_score",
        _fake_post_remote_score_ok,
    )

    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline
    from app.services.score_document_worker import run_score_document_sync

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("promo.txt", b"promo-body", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-promo-test")
        sess.commit()
    finally:
        sess.close()

    run_score_document_sync(did)

    import psycopg

    with psycopg.connect(database_url) as conn:
        rows = conn.execute(
            """
            SELECT scorer_name, is_canonical
            FROM document_scores
            WHERE document_id = %s::uuid AND scorer_name IN (
                'verifiedsignal_heuristic', 'verifiedsignal_http'
            )
            """,
            (did,),
        ).fetchall()
    canon = {name: c for name, c in rows}
    assert canon["verifiedsignal_heuristic"] is False
    assert canon["verifiedsignal_http"] is True


@pytest.mark.integration
def test_bayes_fusion_row_after_http_scorer(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SCORE_ASYNC_BACKEND", "http")
    monkeypatch.setenv("SCORE_HTTP_URL", "https://scorer.example/score")
    monkeypatch.setenv("BAYES_FUSION_ENABLED", "true")
    monkeypatch.setenv("BAYES_FUSION_PRIOR_AI_PROB", "0.15")
    monkeypatch.setattr(
        "app.services.score_document_worker.post_remote_score",
        _fake_post_remote_score_ok,
    )

    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline
    from app.services.score_document_worker import run_score_document_sync

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("bayes.txt", b"bayes-fusion-body-unique", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-bayes-test")
        sess.commit()
    finally:
        sess.close()

    run_score_document_sync(did)

    import psycopg

    with psycopg.connect(database_url) as conn:
        row = conn.execute(
            """
            SELECT scorer_name, ai_generation_probability::float, score_payload->>'kind'
            FROM document_scores
            WHERE document_id = %s::uuid AND scorer_name = 'verifiedsignal_bayes_v1'
            """,
            (did,),
        ).fetchone()
    assert row is not None
    assert row[0] == "verifiedsignal_bayes_v1"
    assert row[1] is not None
    assert 0.001 <= row[1] <= 0.999
    assert row[2] == "bayes_fusion_v1"


@pytest.mark.integration
def test_bayes_fusion_idempotent_second_worker_run(
    intake_api_client,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SCORE_ASYNC_BACKEND", "http")
    monkeypatch.setenv("SCORE_HTTP_URL", "https://scorer.example/score")
    monkeypatch.setenv("BAYES_FUSION_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.score_document_worker.post_remote_score",
        _fake_post_remote_score_ok,
    )

    from app.core.config import reset_settings_cache
    from app.db.session import get_session_factory, reset_engine
    from app.services.opensearch_document_index import reset_fake_opensearch_index
    from app.services.pipeline_run_service import execute_scaffold_pipeline
    from app.services.score_document_worker import run_score_document_sync

    reset_fake_opensearch_index()
    reset_settings_cache()
    reset_engine()

    files = {"file": ("bayes-idem.txt", b"bayes-idem-body", "text/plain")}
    r = intake_api_client.post("/api/v1/documents", files=files)
    assert r.status_code == 200, r.text
    did = r.json()["document_id"]

    sess = get_session_factory()()
    try:
        execute_scaffold_pipeline(sess, uuid.UUID(did), "job-bayes-idem")
        sess.commit()
    finally:
        sess.close()

    run_score_document_sync(did)
    run_score_document_sync(did)

    import psycopg

    with psycopg.connect(database_url) as conn:
        n = conn.execute(
            """
            SELECT COUNT(*) FROM document_scores
            WHERE document_id = %s::uuid AND scorer_name = 'verifiedsignal_bayes_v1'
            """,
            (did,),
        ).fetchone()[0]
    assert n == 1
