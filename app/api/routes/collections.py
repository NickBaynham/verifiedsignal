"""Collections API (placeholder; requires Supabase JWT)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("")
def list_collections(_user_id: str = Depends(get_current_user)) -> dict:
    return {"collections": []}
