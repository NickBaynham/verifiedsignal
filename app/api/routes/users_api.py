"""User profile helpers (requires Supabase JWT)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_me(user_id: str = Depends(get_current_user)) -> dict[str, str]:
    return {"user_id": user_id}
