"""Unit tests: HTTP remote scorer request/response parsing and transport."""

import app.services.score_http_remote as score_http_remote_mod
import httpx
import pytest
from app.services.score_http_remote import (
    ScoringPermanentError,
    ScoringRetryableError,
    build_request_payload,
    content_fingerprint,
    parse_remote_score_body,
    post_remote_score,
)


def test_content_fingerprint_prefers_sha256():
    fp = content_fingerprint(body_text="x", content_sha256=b"\x01" * 32)
    assert fp == "01" * 32


def test_content_fingerprint_body_only():
    fp = content_fingerprint(body_text="hello", content_sha256=None)
    assert len(fp) == 64


def test_build_request_payload_truncation():
    long = "w" * 100
    p = build_request_payload(
        document_id="00000000-0000-4000-8000-000000000099",
        title="t",
        body_text=long,
        content_type="text/plain",
        fingerprint="abc",
        max_body_chars=20,
    )
    assert len(p["body_text"]) == 20
    assert p["body_text_truncated"] is True


def test_parse_remote_score_body_ok():
    r = parse_remote_score_body(
        {
            "schema_version": 1,
            "factuality_score": 0.5,
            "ai_generation_probability": 0.5,
            "metadata": {"x": 1},
        }
    )
    assert r.factuality_score == 0.5
    assert r.ai_generation_probability == 0.5
    assert r.extra.get("remote_metadata") == {"x": 1}


def test_parse_remote_score_body_rejects_bad_schema():
    with pytest.raises(ScoringPermanentError):
        parse_remote_score_body({"schema_version": 99})


def test_parse_remote_score_body_rejects_oob_score():
    with pytest.raises(ScoringPermanentError):
        parse_remote_score_body({"schema_version": 1, "factuality_score": 1.5})


def test_post_remote_score_200(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer secret"
        return httpx.Response(
            200,
            json={"schema_version": 1, "factuality_score": 0.1, "ai_generation_probability": 0.9},
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def patched_client(**kwargs):
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(score_http_remote_mod.httpx, "Client", patched_client)
    code, body, ms = post_remote_score(
        url="https://example.test/score",
        bearer_token="secret",
        payload={"x": 1},
        timeout_s=5.0,
    )
    assert code == 200
    assert body["factuality_score"] == 0.1
    assert ms >= 0


def test_post_remote_score_retryable_503(monkeypatch):
    transport = httpx.MockTransport(lambda r: httpx.Response(503, text="no"))
    real_client = httpx.Client

    def patched_client(**kwargs):
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(score_http_remote_mod.httpx, "Client", patched_client)
    with pytest.raises(ScoringRetryableError):
        post_remote_score(
            url="https://example.test/score",
            bearer_token=None,
            payload={},
            timeout_s=5.0,
        )


def test_post_remote_score_permanent_422(monkeypatch):
    transport = httpx.MockTransport(lambda r: httpx.Response(422, text="bad"))
    real_client = httpx.Client

    def patched_client(**kwargs):
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(score_http_remote_mod.httpx, "Client", patched_client)
    with pytest.raises(ScoringPermanentError):
        post_remote_score(
            url="https://example.test/score",
            bearer_token=None,
            payload={},
            timeout_s=5.0,
        )
