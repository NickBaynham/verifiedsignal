"""Server-Sent Events stream for pipeline / system notifications."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.auth.dependencies import get_sse_subscriber_sub
from app.services.event_service import get_event_hub


def sse_event_visible_to_subscriber(line: str, subscriber_sub: str | None) -> bool:
    """
    When ``subscriber_sub`` is set (authenticated SSE with tenancy), only deliver events whose
    payload includes matching ``auth_sub`` (set at publish time, e.g. document intake).
    """
    if subscriber_sub is None:
        return True
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return False
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return False
    return payload.get("auth_sub") == subscriber_sub


router = APIRouter(prefix="/events", tags=["events"])


async def _sse_generator(subscriber_sub: str | None) -> AsyncIterator[dict]:
    hub = get_event_hub()
    q = await hub.subscribe()
    try:
        yield {"data": '{"type":"connected","payload":{}}'}
        while True:
            line = await q.get()
            if not sse_event_visible_to_subscriber(line, subscriber_sub):
                continue
            yield {"data": line}
    finally:
        await hub.unsubscribe(q)


@router.get("/stream")
async def event_stream(
    subscriber_sub: str | None = Depends(get_sse_subscriber_sub),
) -> EventSourceResponse:
    """
    SSE endpoint. Clients receive ``connected`` then tenant-scoped events (``auth_sub`` on
    payloads). Browsers should pass ``?access_token=<JWT>``; ``Authorization: Bearer`` also works.
    """
    return EventSourceResponse(_sse_generator(subscriber_sub))
