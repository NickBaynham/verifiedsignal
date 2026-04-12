"""Dev-only Supabase user bootstrap on API startup."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.auth.supabase_service import reset_supabase_service_client
from app.core.config import Settings, reset_settings_cache
from app.services.dev_auth_bootstrap import bootstrap_dev_auth_user
from supabase_auth.errors import AuthApiError

_SUPABASE_ENV = {
    "ENVIRONMENT": "development",
    "SUPABASE_URL": "http://localhost:54321",
    "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.test-anon-key",
    "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.test-service-key",
}


@pytest.fixture(autouse=True)
def _cleanup_supabase_singleton() -> None:
    yield
    reset_supabase_service_client()
    reset_settings_cache()


def test_bootstrap_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _SUPABASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER", "false")
    reset_settings_cache()

    mock_client = MagicMock()
    monkeypatch.setattr(
        "app.services.dev_auth_bootstrap.get_supabase_service_client",
        lambda: mock_client,
    )
    bootstrap_dev_auth_user(Settings())
    mock_client.auth.admin.create_user.assert_not_called()


def test_bootstrap_skips_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _SUPABASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER", "true")
    reset_settings_cache()

    mock_client = MagicMock()
    monkeypatch.setattr(
        "app.services.dev_auth_bootstrap.get_supabase_service_client",
        lambda: mock_client,
    )
    bootstrap_dev_auth_user(Settings())
    mock_client.auth.admin.create_user.assert_not_called()


def test_bootstrap_creates_user(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _SUPABASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER", "true")
    reset_settings_cache()

    mock_client = MagicMock()
    mock_client.auth.admin.list_users.return_value = []
    monkeypatch.setattr(
        "app.services.dev_auth_bootstrap.get_supabase_service_client",
        lambda: mock_client,
    )
    bootstrap_dev_auth_user(Settings())
    mock_client.auth.admin.create_user.assert_called_once()
    attrs = mock_client.auth.admin.create_user.call_args[0][0]
    assert attrs["email"] == "dev@example.com"
    assert attrs["password"] == "devpassword123"
    assert attrs["email_confirm"] is True


def test_bootstrap_syncs_password_when_user_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _SUPABASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER", "true")
    reset_settings_cache()

    existing = MagicMock()
    existing.id = "user-id-1"
    existing.email = "dev@example.com"

    mock_client = MagicMock()
    mock_client.auth.admin.list_users.return_value = [existing]
    monkeypatch.setattr(
        "app.services.dev_auth_bootstrap.get_supabase_service_client",
        lambda: mock_client,
    )
    bootstrap_dev_auth_user(Settings())
    mock_client.auth.admin.create_user.assert_not_called()
    mock_client.auth.admin.update_user_by_id.assert_called_once_with(
        "user-id-1",
        {"password": "devpassword123", "email_confirm": True},
    )


def test_bootstrap_duplicate_race_updates_password(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _SUPABASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER", "true")
    reset_settings_cache()

    existing = MagicMock()
    existing.id = "user-id-2"
    existing.email = "dev@example.com"

    mock_client = MagicMock()
    mock_client.auth.admin.list_users.side_effect = [
        [],
        [existing],
    ]
    mock_client.auth.admin.create_user.side_effect = AuthApiError(
        "User already registered",
        400,
        "email_exists",
    )
    monkeypatch.setattr(
        "app.services.dev_auth_bootstrap.get_supabase_service_client",
        lambda: mock_client,
    )
    bootstrap_dev_auth_user(Settings())
    mock_client.auth.admin.update_user_by_id.assert_called_once_with(
        "user-id-2",
        {"password": "devpassword123", "email_confirm": True},
    )
