"""Decode Supabase access tokens using HS256 (local) or JWKS RS256 (hosted)."""

from __future__ import annotations

from functools import lru_cache

import httpx
from jose import JWTError, jwt
from jose.jwk import construct

from app.core.config import Settings


@lru_cache(maxsize=4)
def _jwks_document(url: str) -> dict:
    r = httpx.get(url, timeout=10.0)
    r.raise_for_status()
    return r.json()


def decode_access_token_sub(token: str, settings: Settings) -> str:
    """
    Verify JWT and return Auth user id (`sub`).
    JWKS URL set → RS256 + remote keys; otherwise HS256 + SUPABASE_JWT_SECRET.
    """
    jwks_url = settings.supabase_jwks_url.strip()
    if jwks_url:
        jwks = _jwks_document(jwks_url)
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        keys = jwks.get("keys", [])
        key_dict = next((k for k in keys if k.get("kid") == kid), None)
        if key_dict is None:
            raise JWTError("no matching JWK for kid")
        key = construct(key_dict)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.jwt_audience,
            options={"verify_aud": True},
        )
    else:
        secret = settings.supabase_jwt_secret.strip()
        if not secret:
            raise JWTError("SUPABASE_JWT_SECRET or SUPABASE_JWKS_URL must be set")
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            options={"verify_aud": True},
        )
    sub = payload.get("sub")
    if not sub:
        raise JWTError("missing sub claim")
    return str(sub)
