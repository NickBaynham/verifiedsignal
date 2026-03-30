"""Unit tests: URL intake SSRF validation."""

from __future__ import annotations

import socket

import pytest
from app.core.config import Settings
from app.services.exceptions import IntakeValidationError
from app.services.url_ingest_ssrf import validate_url_for_ingest


def _settings(**kwargs: object) -> Settings:
    base = dict(
        database_url="postgresql://x",
        redis_url="redis://x",
        allow_http_url_ingest=False,
        url_fetch_block_private_networks=True,
    )
    base.update(kwargs)
    return Settings.model_construct(**base)


def _mock_public_dns(monkeypatch: pytest.MonkeyPatch, *, port: int) -> None:
    """Resolve any hostname to a public IPv4 (no real DNS)."""

    def fake_gai(host: str, p: int, *args: object, **kwargs: object):
        _ = host
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("8.8.8.8", p or port))]

    monkeypatch.setattr("app.services.url_ingest_ssrf.socket.getaddrinfo", fake_gai)


@pytest.mark.unit
def test_validate_url_rejects_embedded_credentials():
    with pytest.raises(IntakeValidationError, match="credentials"):
        validate_url_for_ingest("https://user:pass@example.com/a", _settings())


@pytest.mark.unit
def test_validate_url_rejects_loopback_literal():
    with pytest.raises(IntakeValidationError, match="not allowed"):
        validate_url_for_ingest("https://127.0.0.1/file", _settings(allow_http_url_ingest=True))


@pytest.mark.unit
def test_validate_url_requires_https_when_http_disabled():
    with pytest.raises(IntakeValidationError, match="http"):
        validate_url_for_ingest("http://example.com/a", _settings(allow_http_url_ingest=False))


@pytest.mark.unit
def test_validate_url_allows_http_when_enabled(monkeypatch: pytest.MonkeyPatch):
    _mock_public_dns(monkeypatch, port=80)
    u = validate_url_for_ingest(
        "http://example.com/path?q=1", _settings(allow_http_url_ingest=True)
    )
    assert u.startswith("http://example.com/")
    assert "q=1" in u


@pytest.mark.unit
def test_validate_url_https_normalizes_query_order(monkeypatch: pytest.MonkeyPatch):
    _mock_public_dns(monkeypatch, port=443)
    u = validate_url_for_ingest("https://example.com/x?b=2&a=1", _settings())
    assert "a=1" in u and "b=2" in u
    assert u.index("a=") < u.index("b=")
