"""
Import side effects: register FastMCP tools, resources, and prompts.

Import this module after ``init_runtime()`` so ``get_adapter()`` is ready when
handlers run (registration only attaches functions; adapter is resolved per call).
"""

from __future__ import annotations

import mcp_server.prompts  # noqa: F401
import mcp_server.resources  # noqa: F401
import mcp_server.tools  # noqa: F401
