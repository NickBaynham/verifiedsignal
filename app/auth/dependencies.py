"""FastAPI auth dependencies (Bearer JWT → Supabase user id)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.deps import get_db
from app.auth.jwt_verify import decode_access_token_claims
from app.core.config import Settings, get_settings
from app.services.identity_service import ensure_personal_tenant_for_claims

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Validates the Bearer JWT and returns the user_id (`sub` claim).

    When `VERIFIEDSIGNAL_AUTO_PROVISION_IDENTITY` is true, ensures a `users` row plus personal
    org/membership/inbox collection exist (idempotent), and commits when inserts occur.

    Never calls Supabase HTTP — verification uses JWKS or shared secret only.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token_claims(credentials.credentials, settings)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    request.state.vs_claims = claims

    _, created = ensure_personal_tenant_for_claims(db, claims, settings)
    if created:
        db.commit()

    return claims.sub


async def get_optional_current_user_sub(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """
    Bearer JWT → auth ``sub`` string; missing header → ``None``.

    Search applies ``VERIFIEDSIGNAL_REQUIRE_AUTH_SEARCH`` in the service layer. Invalid or
    expired token → 401 when Authorization is sent.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        claims = decode_access_token_claims(credentials.credentials, settings)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    request.state.vs_claims = claims

    _, created = ensure_personal_tenant_for_claims(db, claims, settings)
    if created:
        db.commit()

    return claims.sub


async def get_sse_subscriber_sub(
    request: Request,
    access_token: str | None = Query(
        default=None,
        alias="access_token",
        description="JWT for browser EventSource (cannot send Authorization header).",
    ),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """
    JWT for ``GET /events/stream``.

    Returns ``sub`` when auth is required and the token is valid; same provisioning as Bearer
    routes. Returns ``None`` when ``VERIFIEDSIGNAL_REQUIRE_AUTH_SSE`` is false (legacy).
    """
    if not settings.require_auth_for_sse:
        return None

    raw: str | None = None
    if credentials is not None and credentials.credentials:
        raw = credentials.credentials.strip()
    elif access_token is not None and access_token.strip():
        raw = access_token.strip()

    if not raw:
        raise HTTPException(
            status_code=401,
            detail="SSE requires authentication (Bearer header or access_token query parameter)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token_claims(raw, settings)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    request.state.vs_claims = claims

    _, created = ensure_personal_tenant_for_claims(db, claims, settings)
    if created:
        db.commit()

    return claims.sub
