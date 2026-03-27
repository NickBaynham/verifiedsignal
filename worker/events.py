"""
Emit worker-side events (logs today; later Redis pub/sub or webhook to API SSE bridge).

Keeping this module small makes it easy to swap transports without touching tasks.
"""

from __future__ import annotations

from typing import Any

from worker.logging import get_logger

log = get_logger("veridoc.worker.events")


def emit_worker_event(event_type: str, payload: dict[str, Any]) -> None:
    log.info("worker_event type=%s payload=%s", event_type, payload)
