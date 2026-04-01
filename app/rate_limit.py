"""Per-IP rate limits (slowapi). In-memory storage per process (not shared across API replicas)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import Settings

# Single process-wide instance so @limiter.decorators on routers stay wired correctly.
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", enabled=True)


def sync_limiter_from_settings(settings: Settings) -> None:
    """Call from create_app after loading Settings (tests toggle RATE_LIMIT_ENABLED)."""
    limiter.enabled = settings.rate_limit_enabled
