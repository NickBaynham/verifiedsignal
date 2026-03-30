"""Search API: keyword query over OpenSearch (or in-memory fake when configured)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.placeholder import get_optional_user
from app.schemas.search import SearchResponse
from app.services.search_service import search_documents

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query("", min_length=0, max_length=2000),
    limit: int = Query(10, ge=1, le=100),
    _user: dict = Depends(get_optional_user),
) -> SearchResponse:
    _ = _user
    raw = await search_documents(q, limit=limit)
    return SearchResponse(**raw)
