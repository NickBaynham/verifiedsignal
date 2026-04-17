"""Stdio MCP entrypoint for Claude Desktop and other MCP clients."""

from __future__ import annotations

import logging
import sys

from mcp_server.config import load_settings
from mcp_server.runtime import init_runtime, mcp


def main() -> None:
    cfg = load_settings()
    level = getattr(logging, cfg.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")
    try:
        init_runtime(cfg)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e
    import mcp_server.server  # noqa: F401 — register handlers
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
