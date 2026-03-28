"""FastAPI auth dependencies (Bearer JWT → Supabase user id)."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.jwt_verify import decode_access_token_sub
from app.core.config import get_settings

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """
    Validates the Bearer JWT and returns the user_id (`sub` claim).
    Never calls Supabase HTTP — verification uses JWKS or shared secret only.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    try:
        return decode_access_token_sub(credentials.credentials, settings)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None
