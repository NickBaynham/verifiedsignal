"""Development-only: ensure a Supabase Auth user exists for local API + SPA login."""

from __future__ import annotations

import logging

from supabase_auth.errors import AuthApiError

from app.auth.supabase_service import get_supabase_service_client
from app.core.config import Settings

log = logging.getLogger(__name__)


def _duplicate_user_error(exc: AuthApiError) -> bool:
    msg = (getattr(exc, "message", None) or str(exc)).lower()
    code = str(getattr(exc, "name", "") or getattr(exc, "code", "") or "").lower()
    return (
        "already" in msg
        or "exists" in msg
        or "registered" in msg
        or "duplicate" in msg
        or code in ("email_exists", "user_already_exists")
    )


def _find_user_id_by_email(
    client: object,
    email: str,
    *,
    per_page: int = 200,
    max_pages: int = 25,
) -> str | None:
    """Return GoTrue user id for email, or None (paginates admin list — dev-only)."""
    target = email.strip().lower()
    for page in range(1, max_pages + 1):
        users = client.auth.admin.list_users(page=page, per_page=per_page)
        if not users:
            return None
        for u in users:
            em = (getattr(u, "email", None) or "").strip().lower()
            if em == target:
                uid = getattr(u, "id", None)
                return str(uid) if uid else None
        if len(users) < per_page:
            return None
    return None


def _sync_dev_user_password(client: object, uid: str, password: str, email: str) -> None:
    client.auth.admin.update_user_by_id(
        uid,
        {
            "password": password,
            "email_confirm": True,
        },
    )
    log.info("dev_auth_bootstrap synced password + email_confirm for email=%s", email)


def bootstrap_dev_auth_user(settings: Settings) -> None:
    """
    Ensure a confirmed email/password user exists in Supabase Auth when enabled.

    If the user already exists (e.g. from an older default password), their password is reset to
    match current settings so local login keeps working.

    Guarded by ENVIRONMENT=development, VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_USER, and
    configured Supabase keys.
    """
    if settings.environment.strip().lower() != "development":
        return
    if not settings.dev_bootstrap_auth_user:
        return
    if not settings.supabase_auth_configured:
        log.debug("dev_auth_bootstrap skipped: Supabase auth not configured")
        return

    email = settings.dev_bootstrap_auth_email.strip().lower()
    password = settings.dev_bootstrap_auth_password
    if not email or not password:
        log.warning("dev_auth_bootstrap skipped: empty email or password in settings")
        return

    client = get_supabase_service_client()
    try:
        uid = _find_user_id_by_email(client, email)
        if uid:
            _sync_dev_user_password(client, uid, password, email)
            return
        client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            },
        )
        log.info("dev_auth_bootstrap created Supabase user for local login email=%s", email)
    except AuthApiError as e:
        if _duplicate_user_error(e):
            uid2 = _find_user_id_by_email(client, email)
            if uid2:
                try:
                    _sync_dev_user_password(client, uid2, password, email)
                except AuthApiError as e2:
                    log.warning(
                        "dev_auth_bootstrap post-duplicate update failed: %s",
                        getattr(e2, "message", None) or str(e2),
                    )
            else:
                log.info(
                    "dev_auth_bootstrap user already exists email=%s (could not list id)",
                    email,
                )
            return
        log.warning("dev_auth_bootstrap failed: %s", getattr(e, "message", None) or str(e))
    except Exception:
        log.exception("dev_auth_bootstrap unexpected error")
