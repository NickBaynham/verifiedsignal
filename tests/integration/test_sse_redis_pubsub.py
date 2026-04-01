"""
Redis-backed SSE hub: optional integration check when Redis is reachable.

Skipped automatically if nothing answers on REDIS_URL (default localhost:6379).
"""

from __future__ import annotations

import asyncio
import json
import os

import pytest
from app.core.config import reset_settings_cache
from app.services.event_service import RedisEventHub, reset_event_hub


def _redis_ping() -> bool:
    try:
        import redis as sync_redis

        url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
        r = sync_redis.Redis.from_url(url, socket_connect_timeout=0.5)
        try:
            return bool(r.ping())
        finally:
            r.close()
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not _redis_ping(), reason="REDIS_URL not reachable (start Redis or skip)")
def test_redis_event_hub_delivers_across_hub_instances(monkeypatch: pytest.MonkeyPatch):
    """Two hub instances (simulating two API replicas) share one channel."""
    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    channel = "verifiedsignal:test_sse_integration"

    monkeypatch.setenv("USE_FAKE_EVENT_HUB", "false")
    monkeypatch.setenv("REDIS_URL", url)
    monkeypatch.setenv("EVENT_PUBSUB_CHANNEL", channel)
    reset_settings_cache()

    async def run() -> None:
        consumer = RedisEventHub(url, channel)
        producer = RedisEventHub(url, channel)
        try:
            q = await consumer.subscribe()
            await producer.publish("integration_ping", {"seq": 42})
            raw = await asyncio.wait_for(q.get(), timeout=5.0)
            data = json.loads(raw)
            assert data["type"] == "integration_ping"
            assert data["payload"] == {"seq": 42}
            await consumer.unsubscribe(q)
        finally:
            await consumer.aclose()
            await producer.aclose()

    try:
        asyncio.run(run())
    finally:
        reset_event_hub()
        reset_settings_cache()
