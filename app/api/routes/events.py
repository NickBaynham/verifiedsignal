"""Server-Sent Events stream for pipeline / system notifications."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.auth.placeholder import get_optional_user
from app.services.event_service import get_event_hub

router = APIRouter(prefix="/events", tags=["events"])


async def _sse_generator() -> AsyncIterator[dict]:
    hub = get_event_hub()
    q = await hub.subscribe()
    try:
        yield {"data": '{"type":"connected","payload":{}}'}
        while True:
            line = await q.get()
            yield {"data": line}
    finally:
        await hub.unsubscribe(q)


@router.get("/stream")
async def event_stream(_user: dict = Depends(get_optional_user)) -> EventSourceResponse:
    """
    SSE endpoint. Clients receive `connected` then any events published via EventHub
    (e.g. worker stages). Replace fan-out with Redis pub/sub for multi-instance APIs.
    """
    _ = _user
    return EventSourceResponse(_sse_generator())
