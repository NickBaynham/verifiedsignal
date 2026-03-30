"""
OpenSearch index for documents (keyword fields). Supports in-memory fake for tests.
"""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any

import httpx

from app.core.config import Settings, get_settings

log = logging.getLogger("verifiedsignal.opensearch")

_fake_lock = threading.Lock()
_fake_docs: dict[str, dict[str, Any]] = {}


def reset_fake_opensearch_index() -> None:
    """Test hook: clear in-memory index."""
    with _fake_lock:
        _fake_docs.clear()


def _index_url(settings: Settings) -> str:
    base = settings.opensearch_url.rstrip("/")
    name = settings.opensearch_index_name.strip() or "verifiedsignal_documents"
    return f"{base}/{name}"


def ensure_index_and_mapping(settings: Settings | None = None) -> None:
    """Create index with mapping if missing (no-op for fake mode)."""
    settings = settings or get_settings()
    if settings.use_fake_opensearch:
        return

    base = settings.opensearch_url.rstrip("/")
    name = settings.opensearch_index_name.strip() or "verifiedsignal_documents"
    mapping = {
        "mappings": {
            "properties": {
                "document_id": {"type": "keyword"},
                "collection_id": {"type": "keyword"},
                "title": {"type": "text"},
                "body_text": {"type": "text"},
                "status": {"type": "keyword"},
            }
        }
    }
    url = f"{base}/{name}"
    with httpx.Client(timeout=30.0) as client:
        r = client.put(url, json=mapping)
        if r.status_code in (200, 201):
            return
        try:
            body = r.json()
        except Exception:
            body = {}
        err = body.get("error", {})
        if r.status_code == 400 and err.get("type") == "resource_already_exists_exception":
            return
        log.warning("opensearch_create_index_failed status=%s body=%s", r.status_code, r.text[:500])


def index_document_sync(
    *,
    document_id: uuid.UUID,
    collection_id: uuid.UUID,
    title: str | None,
    body_text: str | None,
    status: str,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    doc_id = str(document_id)
    payload = {
        "document_id": doc_id,
        "collection_id": str(collection_id),
        "title": title or "",
        "body_text": body_text or "",
        "status": status,
    }
    if settings.use_fake_opensearch:
        with _fake_lock:
            _fake_docs[doc_id] = payload
        return

    ensure_index_and_mapping(settings)
    url = f"{_index_url(settings)}/_doc/{doc_id}?refresh=wait_for"
    with httpx.Client(timeout=30.0) as client:
        r = client.put(url, json=payload)
        if r.status_code not in (200, 201):
            log.warning(
                "opensearch_index_failed document_id=%s status=%s text=%s",
                doc_id,
                r.status_code,
                r.text[:500],
            )


def delete_document_from_index_sync(
    document_id: uuid.UUID,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    doc_id = str(document_id)
    if settings.use_fake_opensearch:
        with _fake_lock:
            _fake_docs.pop(doc_id, None)
        return

    url = f"{_index_url(settings)}/_doc/{doc_id}?refresh=wait_for"
    with httpx.Client(timeout=30.0) as client:
        r = client.delete(url)
        if r.status_code not in (200, 404):
            log.debug(
                "opensearch_delete_unexpected document_id=%s status=%s",
                doc_id,
                r.status_code,
            )


def search_keyword_sync(
    query: str,
    *,
    limit: int,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Run keyword search; return dict with hits list and total for SearchResponse.
    """
    settings = settings or get_settings()
    lim = max(1, min(limit, 100))

    if settings.use_fake_opensearch:
        return _search_fake(query, lim)

    ensure_index_and_mapping(settings)
    q = (query or "").strip()
    if q:
        body: dict[str, Any] = {
            "size": lim,
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^2", "body_text"],
                    "type": "best_fields",
                }
            },
        }
    else:
        body = {"size": lim, "query": {"match_all": {}}}

    url = f"{_index_url(settings)}/_search"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=body)
        if r.status_code != 200:
            return {
                "hits": [],
                "total": 0,
                "index_status": "error",
                "message": f"OpenSearch HTTP {r.status_code}: {r.text[:300]}",
            }
        data = r.json()
    hits_out: list[dict[str, Any]] = []
    for h in data.get("hits", {}).get("hits", [])[:lim]:
        src = h.get("_source") or {}
        hits_out.append(
            {
                "document_id": src.get("document_id"),
                "title": src.get("title"),
                "score": h.get("_score"),
                "snippet": (src.get("body_text") or "")[:280],
            }
        )
    total = data.get("hits", {}).get("total", 0)
    if isinstance(total, dict):
        total_val = int(total.get("value", 0))
    else:
        total_val = int(total or 0)
    return {
        "hits": hits_out,
        "total": total_val,
        "index_status": "ok",
        "message": None,
    }


def _search_fake(query: str, limit: int) -> dict[str, Any]:
    q = (query or "").strip().lower()
    with _fake_lock:
        docs = list(_fake_docs.values())
    if not q:
        ranked = docs[:limit]
    else:
        ranked = []
        for d in docs:
            title = (d.get("title") or "").lower()
            body = (d.get("body_text") or "").lower()
            if q in title or q in body:
                ranked.append(d)
        ranked = ranked[:limit]
    hits = [
        {
            "document_id": d.get("document_id"),
            "title": d.get("title"),
            "score": 1.0,
            "snippet": (d.get("body_text") or "")[:280],
        }
        for d in ranked
    ]
    return {
        "hits": hits,
        "total": len(ranked),
        "index_status": "fake",
        "message": None,
    }
