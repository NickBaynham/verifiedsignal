"""In-memory pub/sub for SSE (pipeline / system events). Replace with Redis pub/sub later."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


class EventHub:
    """Fan-out events to connected SSE clients (dev/test friendly)."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[str]] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        async with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        msg = json.dumps(
            {
                "type": event_type,
                "payload": payload,
                "ts": datetime.now(tz=UTC).isoformat(),
                "environment": get_settings().environment,
            }
        )
        async with self._lock:
            targets = list(self._subscribers)
        for q in targets:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                continue


_hub: EventHub | None = None


def get_event_hub() -> EventHub:
    global _hub
    if _hub is None:
        _hub = EventHub()
    return _hub


def reset_event_hub() -> None:
    global _hub
    _hub = None
