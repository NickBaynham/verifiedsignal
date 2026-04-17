"""Process-wide MCP app and VerifiedSignal adapter (initialized before stdio run)."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from mcp_server.adapters.models_adapter import ModelsAdapter
from mcp_server.adapters.verifiedsignal_client import VerifiedSignalClient
from mcp_server.config import MCPSettings, load_settings

log = logging.getLogger(__name__)

mcp = FastMCP(
    "verifiedsignal",
    json_response=True,
    instructions=(
        "This server exposes VerifiedSignal canonical knowledge models (Postgres-backed, "
        "versioned). Prefer tools and resources over guessing. Model search is a V1 "
        "placeholder (summary + asset titles); replace with dedicated retrieval when available."
    ),
)

_adapter: ModelsAdapter | None = None


def init_runtime(
    settings: MCPSettings | None = None,
    adapter: ModelsAdapter | None = None,
) -> None:
    """Build HTTP client + adapter. Call once from main() before handling stdio."""
    global _adapter
    if adapter is not None:
        _adapter = adapter
        return
    cfg = settings or load_settings()
    cfg.validate_runtime()
    log.info("MCP connecting to VerifiedSignal API at %s", cfg.api_url.rstrip("/"))
    client = VerifiedSignalClient(
        cfg.api_url,
        cfg.access_token,
        timeout_seconds=cfg.request_timeout_seconds,
    )
    _adapter = ModelsAdapter(client)


def get_adapter() -> ModelsAdapter:
    if _adapter is None:
        msg = "MCP runtime not initialized; call init_runtime() before serving."
        raise RuntimeError(msg)
    return _adapter


def reset_runtime_for_tests() -> None:
    """Clear adapter (unit tests only)."""
    global _adapter
    _adapter = None
