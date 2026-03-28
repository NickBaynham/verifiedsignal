"""
Supabase Auth pass-through: signup, login (refresh cookie), refresh, logout, reset email.

Thin wrappers around supabase-py GoTrue client; JWT validation for API routes lives in
`app.auth.dependencies` (JWKS / HS256 only — no Supabase round-trip per request).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidCredentialsError,
    AuthSessionMissingError,
    AuthWeakPasswordError,
)

from app.auth.supabase_service import get_supabase_service_client
from app.core.config import Settings, get_settings
from app.schemas.auth_api import (
    AccessTokenResponse,
    EmailPasswordBody,
    RefreshResponse,
    ResetPasswordBody,
    SignupResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "vs_refresh_token"
REFRESH_MAX_AGE = 7 * 24 * 3600
COOKIE_PATH = "/auth"


def _require_supabase_config(settings: Settings) -> None:
    if not settings.supabase_auth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase auth is not configured (set SUPABASE_URL and keys)",
        )


def _auth_error_detail(exc: AuthApiError) -> str:
    return getattr(exc, "message", None) or str(exc)


@router.post("/signup", response_model=SignupResponse)
def auth_signup(
    body: EmailPasswordBody,
    settings: Settings = Depends(get_settings),
) -> SignupResponse:
    _require_supabase_config(settings)
    client = get_supabase_service_client()
    try:
        client.auth.sign_up({"email": body.email, "password": body.password})
    except AuthWeakPasswordError as e:
        raise HTTPException(status_code=400, detail=_auth_error_detail(e)) from e
    except AuthApiError as e:
        code = getattr(e, "code", None) or getattr(e, "name", "") or ""
        if "exists" in str(code).lower() or "already" in _auth_error_detail(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered") from e
        raise HTTPException(status_code=400, detail=_auth_error_detail(e)) from e
    return SignupResponse()


@router.post("/login", response_model=AccessTokenResponse)
def auth_login(
    body: EmailPasswordBody,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> AccessTokenResponse:
    _require_supabase_config(settings)
    client = get_supabase_service_client()
    try:
        res = client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password},
        )
    except AuthInvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail="Invalid email or password") from e
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=_auth_error_detail(e)) from e
    session = res.session
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="No session returned (confirm your email if required)",
        )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=session.refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
        max_age=REFRESH_MAX_AGE,
        path=COOKIE_PATH,
    )
    return AccessTokenResponse(
        access_token=session.access_token,
        expires_in=session.expires_in,
    )


@router.post("/refresh", response_model=RefreshResponse)
def auth_refresh(
    response: Response,
    settings: Settings = Depends(get_settings),
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> RefreshResponse:
    _require_supabase_config(settings)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    client = get_supabase_service_client()
    try:
        res = client.auth.refresh_session(refresh_token)
    except (AuthApiError, AuthSessionMissingError) as e:
        raise HTTPException(status_code=401, detail="Refresh failed") from e
    session = res.session
    if session is None:
        raise HTTPException(status_code=401, detail="Refresh failed")
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=session.refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
        max_age=REFRESH_MAX_AGE,
        path=COOKIE_PATH,
    )
    return RefreshResponse(access_token=session.access_token, expires_in=session.expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def auth_logout(
    response: Response,
    settings: Settings = Depends(get_settings),
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> Response:
    _require_supabase_config(settings)
    client = get_supabase_service_client()
    if refresh_token:
        try:
            client.auth.refresh_session(refresh_token)
            client.auth.sign_out()
        except (AuthApiError, AuthSessionMissingError):
            pass
    response.delete_cookie(
        REFRESH_COOKIE,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def auth_reset_password(
    body: ResetPasswordBody,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    _require_supabase_config(settings)
    client = get_supabase_service_client()
    try:
        client.auth.reset_password_for_email(body.email)
    except AuthApiError:
        pass
    return {"message": "ok"}
