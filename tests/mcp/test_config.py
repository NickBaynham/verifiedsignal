"""MCP config tests."""

from __future__ import annotations

import pytest
from mcp_server.config import MCPSettings


def test_settings_validates_missing_token():
    s = MCPSettings(access_token="", api_url="http://localhost:8000")
    with pytest.raises(ValueError, match="VERIFIEDSIGNAL_ACCESS_TOKEN"):
        s.validate_runtime()


def test_settings_ok_with_token():
    s = MCPSettings(access_token="fake-jwt", api_url="http://localhost:8000")
    s.validate_runtime()
