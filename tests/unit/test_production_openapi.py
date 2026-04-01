"""OpenAPI / Swagger exposure rules for production-like environments."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_production_hides_openapi_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("EXPOSE_OPENAPI_DOCS", raising=False)
    from app.core.config import reset_settings_cache
    from app.main import create_app

    reset_settings_cache()
    try:
        app = create_app()
        with TestClient(app) as client:
            assert client.get("/").status_code == 404
            assert client.get("/openapi.json").status_code == 404
            assert client.get("/redoc").status_code == 404
            assert client.get("/docs").status_code == 404
    finally:
        reset_settings_cache()


def test_staging_hides_openapi_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.delenv("EXPOSE_OPENAPI_DOCS", raising=False)
    from app.core.config import reset_settings_cache
    from app.main import create_app

    reset_settings_cache()
    try:
        app = create_app()
        with TestClient(app) as client:
            assert client.get("/openapi.json").status_code == 404
    finally:
        reset_settings_cache()


def test_production_exposes_openapi_when_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("EXPOSE_OPENAPI_DOCS", "true")
    from app.core.config import reset_settings_cache
    from app.main import create_app

    reset_settings_cache()
    try:
        app = create_app()
        with TestClient(app) as client:
            r = client.get("/")
            assert r.status_code == 200
            assert "swagger" in r.text.lower()
    finally:
        reset_settings_cache()


def test_jwt_algorithm_rejects_non_hmac_without_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.delenv("SUPABASE_JWKS_URL", raising=False)
    from app.core.config import Settings, reset_settings_cache

    reset_settings_cache()
    try:
        with pytest.raises(ValueError, match="JWT_ALGORITHM"):
            Settings()
    finally:
        monkeypatch.delenv("JWT_ALGORITHM", raising=False)
        reset_settings_cache()


def test_allow_default_collection_fallback_env_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFIEDSIGNAL_ALLOW_DEFAULT_COLLECTION_FALLBACK", "true")
    from app.core.config import Settings, reset_settings_cache

    reset_settings_cache()
    try:
        s = Settings()
        assert s.allow_default_collection_fallback is True
    finally:
        monkeypatch.delenv("VERIFIEDSIGNAL_ALLOW_DEFAULT_COLLECTION_FALLBACK", raising=False)
        reset_settings_cache()


def test_jwt_algorithm_rs256_allowed_when_jwks_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://example.invalid/auth/v1/.well-known/jwks.json")
    from app.core.config import Settings, reset_settings_cache

    reset_settings_cache()
    try:
        s = Settings()
        assert s.jwt_algorithm == "RS256"
    finally:
        monkeypatch.delenv("JWT_ALGORITHM", raising=False)
        monkeypatch.delenv("SUPABASE_JWKS_URL", raising=False)
        reset_settings_cache()
