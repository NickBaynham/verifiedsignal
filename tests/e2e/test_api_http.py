"""End-to-end HTTP tests against the ASGI app (no external Docker required)."""

from __future__ import annotations

import pytest


@pytest.mark.api
@pytest.mark.e2e
def test_api_smoke_multi_route(api_client):
    """Cross-route smoke: mirrors how a client hits several endpoints in one session."""
    assert api_client.get("/api/v1/health").json()["status"] == "ok"
    r = api_client.get("/api/v1/search", params={"q": "audit"})
    assert r.status_code == 200
    assert r.json()["index_status"] == "stub"
    # Full intake (multipart + Postgres) lives in tests/integration/test_document_intake.py
