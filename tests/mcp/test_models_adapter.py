"""Models adapter unit tests."""

from __future__ import annotations

import httpx
from mcp_server.adapters.models_adapter import ModelsAdapter
from mcp_server.adapters.verifiedsignal_client import VerifiedSignalClient


def test_pick_latest_version_via_list_versions():
    routes = {
        ("GET", "/api/v1/models/m1/versions"): httpx.Response(
            200,
            json={
                "items": [
                    {"id": "v1", "version_number": 1},
                    {"id": "v2", "version_number": 2},
                ],
                "knowledge_model_id": "m1",
            },
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        return routes[key]

    transport = httpx.MockTransport(handler)
    c = VerifiedSignalClient("http://api.test", "tok", transport=transport)
    try:
        ad = ModelsAdapter(c)
        assert ad.get_latest_version_id("m1") == "v2"
    finally:
        c.close()


def test_search_model_placeholder_finds_title():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/versions"):
            return httpx.Response(
                200,
                json={"items": [{"id": "vx", "version_number": 1}], "knowledge_model_id": "m1"},
            )
        if path.endswith("/versions/vx"):
            return httpx.Response(
                200,
                json={
                    "id": "vx",
                    "version_number": 1,
                    "summary_json": {"headline": "Refund policy"},
                },
            )
        if path.endswith("/versions/vx/assets"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "document_id": "d1",
                            "title": "Refunds overview",
                            "original_filename": None,
                        }
                    ],
                    "model_version_id": "vx",
                },
            )
        return httpx.Response(404, json={"detail": "unexpected " + path})

    transport = httpx.MockTransport(handler)
    c = VerifiedSignalClient("http://api.test", "tok", transport=transport)
    try:
        ad = ModelsAdapter(c)
        out = ad.search_model_placeholder("m1", "refund", version_id="vx")
        assert out["version_id"] == "vx"
        assert any(m.get("field") == "asset_title" for m in out["matches"])
    finally:
        c.close()


def test_compare_model_versions_doc_set_diff():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/versions/v1") and "/assets" not in path:
            return httpx.Response(
                200,
                json={
                    "id": "v1",
                    "version_number": 1,
                    "summary_json": {"a": 1},
                },
            )
        if path.endswith("/versions/v2") and "/assets" not in path:
            return httpx.Response(
                200,
                json={
                    "id": "v2",
                    "version_number": 2,
                    "summary_json": {"b": 2},
                },
            )
        if path.endswith("/versions/v1/assets"):
            return httpx.Response(
                200,
                json={"items": [{"document_id": "d1"}], "model_version_id": "v1"},
            )
        if path.endswith("/versions/v2/assets"):
            return httpx.Response(
                200,
                json={"items": [{"document_id": "d2"}], "model_version_id": "v2"},
            )
        return httpx.Response(404, json={"detail": path})

    transport = httpx.MockTransport(handler)
    c = VerifiedSignalClient("http://api.test", "tok", transport=transport)
    try:
        ad = ModelsAdapter(c)
        diff = ad.compare_model_versions("m1", "v1", "v2")
        assert diff["document_ids_only_in_left"] == ["d1"]
        assert diff["document_ids_only_in_right"] == ["d2"]
        assert "a" in diff["summary_json_keys_only_in_left"]
        assert "b" in diff["summary_json_keys_only_in_right"]
    finally:
        c.close()
