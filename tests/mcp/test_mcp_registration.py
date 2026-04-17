"""MCP server registration and handler smoke tests."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from mcp_server.adapters.models_adapter import ModelsAdapter
from mcp_server.runtime import init_runtime, mcp, reset_runtime_for_tests


@pytest.fixture(autouse=True)
def _reset():
    reset_runtime_for_tests()
    yield
    reset_runtime_for_tests()


def test_tools_resources_prompts_registered():
    mock = MagicMock(spec=ModelsAdapter)
    mock.list_collections.return_value = {"collections": []}
    init_runtime(adapter=mock)
    import mcp_server.server  # noqa: F401 — register once per process

    async def _run():
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}
        assert "list_collections" in tool_names
        assert "search_model" in tool_names
        assert "compare_model_versions" in tool_names

        res = await mcp.list_resources()
        resource_list = res if isinstance(res, list) else res.resources
        static_uris = {str(r.uri) for r in resource_list}
        assert "verifiedsignal://collections" in static_uris
        tmpl = await mcp.list_resource_templates()
        tlist = tmpl if isinstance(tmpl, list) else tmpl.resourceTemplates
        tpl_uris = {str(t.uriTemplate) for t in tlist}
        assert "verifiedsignal://models/{model_id}" in tpl_uris

        prompts = await mcp.list_prompts()
        prompt_list = prompts if isinstance(prompts, list) else prompts.prompts
        names = {p.name for p in prompt_list}
        assert "summarize_model" in names
        assert "design_tests_from_model" in names

    asyncio.run(_run())


def test_resource_collections_uses_adapter():
    mock = MagicMock(spec=ModelsAdapter)
    mock.list_collections.return_value = {"collections": [{"id": "c1"}]}
    init_runtime(adapter=mock)
    import mcp_server.server  # noqa: F401
    from mcp_server.resources import resource_collections

    body = resource_collections()
    assert "c1" in body
    mock.list_collections.assert_called_once()


def test_tool_list_models_error_json():
    mock = MagicMock(spec=ModelsAdapter)
    mock.list_collection_models.side_effect = RuntimeError("boom")
    init_runtime(adapter=mock)
    import mcp_server.server  # noqa: F401
    from mcp_server.tools import list_models

    out = list_models("cid")
    assert out["ok"] is False
    assert "boom" in out["error"]
