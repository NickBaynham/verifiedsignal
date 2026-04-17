"""HTTP client tests (mocked transport)."""

from __future__ import annotations

import httpx
import pytest
from mcp_server.adapters.verifiedsignal_client import VerifiedSignalAPIError, VerifiedSignalClient


def test_request_json_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer tok"
        assert str(request.url).endswith("/api/v1/collections")
        return httpx.Response(200, json={"collections": []})

    transport = httpx.MockTransport(handler)
    c = VerifiedSignalClient("http://api.test", "tok", transport=transport)
    try:
        data = c.list_collections()
        assert data == {"collections": []}
    finally:
        c.close()


def test_request_json_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "nope"})

    transport = httpx.MockTransport(handler)
    c = VerifiedSignalClient("http://api.test", "tok", transport=transport)
    try:
        with pytest.raises(VerifiedSignalAPIError) as ei:
            c.get_model("00000000-0000-4000-8000-000000000001")
        assert ei.value.status_code == 404
    finally:
        c.close()
