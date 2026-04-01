"""SSE fan-out: Redis pub/sub in production, in-memory when USE_FAKE_EVENT_HUB=true."""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis_async

from app.core.config import get_settings

log = logging.getLogger(__name__)


def _build_message(event_type: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "type": event_type,
            "payload": payload,
            "ts": datetime.now(tz=UTC).isoformat(),
            "environment": get_settings().environment,
        }
    )


class EventHubBackend(ABC):
    """Shared contract for SSE event delivery."""

    @abstractmethod
    async def subscribe(self) -> asyncio.Queue[str]:
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release external resources; Redis hub overrides."""
        return


class InMemoryEventHub(EventHubBackend):
    """Fan-out to SSE clients on a single process (tests / dev without Redis)."""

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
        msg = _build_message(event_type, payload)
        async with self._lock:
            targets = list(self._subscribers)
        for q in targets:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                continue


class RedisEventHub(EventHubBackend):
    """
    Redis pub/sub so every API replica subscribed to the channel receives publishes.

    One Redis connection + pubsub per active SSE subscriber; a shared publisher client for PUBLISH.
    """

    def __init__(self, redis_url: str, channel: str) -> None:
        self._url = redis_url
        self._channel = channel
        self._pub: redis_async.Redis | None = None
        self._pub_lock = asyncio.Lock()
        self._listener_tasks: dict[asyncio.Queue[str], asyncio.Task[None]] = {}
        self._listener_lock = asyncio.Lock()

    async def _get_publisher(self) -> redis_async.Redis:
        async with self._pub_lock:
            if self._pub is None:
                self._pub = redis_async.from_url(self._url, decode_responses=True)
            return self._pub

    async def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=256)
        client = redis_async.from_url(self._url, decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe(self._channel)

        async def pump() -> None:
            try:
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    data = message.get("data")
                    if data is None:
                        continue
                    if not isinstance(data, str):
                        data = str(data)
                    try:
                        q.put_nowait(data)
                    except asyncio.QueueFull:
                        pass
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("redis_sse_listener_failed channel=%s", self._channel)
            finally:
                try:
                    await pubsub.unsubscribe(self._channel)
                except Exception:
                    pass
                try:
                    await pubsub.aclose()
                except Exception:
                    pass
                try:
                    await client.aclose()
                except Exception:
                    pass

        task = asyncio.create_task(pump())
        async with self._listener_lock:
            self._listener_tasks[q] = task
        return q

    async def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        async with self._listener_lock:
            task = self._listener_tasks.pop(q, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        msg = _build_message(event_type, payload)
        pub = await self._get_publisher()
        await pub.publish(self._channel, msg)

    async def aclose(self) -> None:
        async with self._listener_lock:
            tasks = list(self._listener_tasks.items())
            self._listener_tasks.clear()
        for _q, task in tasks:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        async with self._pub_lock:
            if self._pub is not None:
                try:
                    await self._pub.aclose()
                except Exception:
                    pass
                self._pub = None


_hub: EventHubBackend | None = None


def get_event_hub() -> EventHubBackend:
    global _hub
    if _hub is None:
        s = get_settings()
        if s.use_fake_event_hub:
            _hub = InMemoryEventHub()
        else:
            _hub = RedisEventHub(s.redis_url, s.event_pubsub_channel)
    return _hub


def reset_event_hub() -> None:
    """Clear singleton; closes Redis hub when no asyncio loop conflict."""
    global _hub
    if _hub is None:
        return
    hub = _hub
    _hub = None
    try:
        asyncio.run(hub.aclose())
    except RuntimeError:
        # Nested loop (e.g. rare test setup); drop reference only.
        pass


async def close_event_hub() -> None:
    """Application shutdown: close hub and clear singleton."""
    global _hub
    if _hub is None:
        return
    hub = _hub
    _hub = None
    await hub.aclose()
