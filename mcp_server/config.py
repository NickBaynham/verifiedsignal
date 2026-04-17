"""Environment-driven configuration for the VerifiedSignal MCP server."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """
    Settings for connecting the MCP server to VerifiedSignal.

    Integration uses the public HTTP API (Bearer JWT) so the MCP process stays
    separate from the FastAPI app and works the same against Docker or host-run API.

    Tradeoff vs direct DB access: HTTP adds latency but reuses authz, avoids duplicating
    tenancy rules, and matches a future remote MCP deployment.
    """

    model_config = SettingsConfigDict(
        env_prefix="VERIFIEDSIGNAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_url: str = Field(
        default="http://127.0.0.1:8000",
        description="VerifiedSignal API origin (no trailing slash).",
    )
    access_token: str = Field(
        default="",
        description="Bearer JWT for /api/v1 (set VERIFIEDSIGNAL_ACCESS_TOKEN).",
    )
    request_timeout_seconds: float = Field(default=60.0, ge=1.0, le=300.0)
    log_level: str = Field(default="WARNING", description="Logging level for the MCP process.")

    def validate_runtime(self) -> None:
        if not self.access_token.strip():
            msg = (
                "Missing VERIFIEDSIGNAL_ACCESS_TOKEN. Use a JWT from your VerifiedSignal login "
                "(same as the web UI Bearer token)."
            )
            raise ValueError(msg)


def load_settings() -> MCPSettings:
    return MCPSettings()
