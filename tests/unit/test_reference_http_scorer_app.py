"""Smoke tests for scripts/reference_http_scorer (docs/scoring-http.md v1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from reference_http_scorer.app import app

pytestmark = pytest.mark.unit


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("REFERENCE_SCORER_BEARER_TOKEN", raising=False)
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_score_v1_success(client: TestClient) -> None:
    payload = {
        "schema_version": 1,
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Hello",
        "body_text": "Some body for scoring.",
        "body_text_truncated": False,
        "content_type": "application/pdf",
        "content_fingerprint": "a" * 64,
    }
    r = client.post("/score", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["schema_version"] == 1
    for key in (
        "factuality_score",
        "ai_generation_probability",
        "fallacy_score",
        "confidence_score",
    ):
        assert key in data
        assert 0.0 <= float(data[key]) <= 1.0
    assert data["metadata"]["scorer"] == "reference_http_scorer"


def test_score_rejects_wrong_schema_version(client: TestClient) -> None:
    r = client.post(
        "/score",
        json={
            "schema_version": 99,
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "body_text": "",
            "body_text_truncated": False,
            "content_fingerprint": "b" * 64,
        },
    )
    assert r.status_code == 400


def test_score_bearer_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REFERENCE_SCORER_BEARER_TOKEN", "secret-token")
    c = TestClient(app)
    r = c.post(
        "/score",
        json={
            "schema_version": 1,
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "body_text": "x",
            "body_text_truncated": False,
            "content_fingerprint": "c" * 64,
        },
    )
    assert r.status_code == 401

    ok = c.post(
        "/score",
        json={
            "schema_version": 1,
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "body_text": "x",
            "body_text_truncated": False,
            "content_fingerprint": "c" * 64,
        },
        headers={"Authorization": "Bearer secret-token"},
    )
    assert ok.status_code == 200


def test_parse_remote_accepts_reference_response(client: TestClient) -> None:
    from app.services.score_http_remote import parse_remote_score_body

    payload = {
        "schema_version": 1,
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "body_text": "x",
        "body_text_truncated": False,
        "content_fingerprint": "d" * 64,
    }
    r = client.post("/score", json=payload)
    assert r.status_code == 200
    parsed = parse_remote_score_body(r.json())
    assert parsed.factuality_score is not None
    assert 0.0 <= parsed.factuality_score <= 1.0
