#!/usr/bin/env python3
"""Smoke check: MCP handlers register without talking to the API (mock adapter)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp_server.adapters.models_adapter import ModelsAdapter  # noqa: E402
from mcp_server.runtime import init_runtime, mcp, reset_runtime_for_tests  # noqa: E402


async def _main() -> None:
    reset_runtime_for_tests()
    init_runtime(adapter=MagicMock(spec=ModelsAdapter))
    import mcp_server.server  # noqa: F401

    tools = await mcp.list_tools()
    assert len(tools) >= 17, f"expected tools, got {len(tools)}"

    resources = await mcp.list_resources()
    rlist = resources if isinstance(resources, list) else resources.resources
    templates = await mcp.list_resource_templates()
    tlist = templates if isinstance(templates, list) else templates.resourceTemplates
    assert len(rlist) >= 1, f"expected static resources, got {len(rlist)}"
    assert len(tlist) >= 7, f"expected resource URI templates, got {len(tlist)}"

    prompts = await mcp.list_prompts()
    plist = prompts if isinstance(prompts, list) else prompts.prompts
    assert len(plist) >= 4, f"expected prompts, got {len(plist)}"


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except Exception as e:
        print("verify_mcp_smoke failed:", e, file=sys.stderr)
        sys.exit(1)
    print("verify_mcp_smoke: ok")
