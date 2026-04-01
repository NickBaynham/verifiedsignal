"""Unit tests for in-memory SSE event hub."""

from __future__ import annotations

import asyncio
import json

import pytest
from app.services.event_service import get_event_hub, reset_event_hub


@pytest.mark.unit
def test_event_hub_publish_delivers(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USE_FAKE_EVENT_HUB", "true")
    from app.core.config import reset_settings_cache

    reset_settings_cache()
    reset_event_hub()

    async def run():
        hub = get_event_hub()
        q = await hub.subscribe()
        await hub.publish("test_event", {"n": 1})
        raw = await asyncio.wait_for(q.get(), timeout=2.0)
        data = json.loads(raw)
        assert data["type"] == "test_event"
        assert data["payload"] == {"n": 1}
        await hub.unsubscribe(q)

    asyncio.run(run())
    reset_event_hub()
    reset_settings_cache()
