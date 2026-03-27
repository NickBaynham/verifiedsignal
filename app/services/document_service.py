"""Document intake: assign identity and enqueue background processing."""

from __future__ import annotations

import uuid

from app.services.event_service import get_event_hub
from app.services.queue_backend import get_job_queue


async def submit_document_for_processing(
    *,
    title: str | None,
    source_uri: str | None,
    metadata: dict | None,
) -> dict:
    """
    Simulate submission: generate a document id and enqueue `process_document`.

    Postgres persistence of rows is intentionally deferred; the API boundary and
    queue handoff are the scaffold focus.
    """
    _ = (title, source_uri, metadata)  # reserved for future validation / insert
    document_id = str(uuid.uuid4())
    queue = await get_job_queue()
    job_id = await queue.enqueue_process_document(document_id)
    await get_event_hub().publish(
        "document_queued",
        {"document_id": document_id, "job_id": job_id},
    )
    return {
        "document_id": document_id,
        "job_id": job_id,
        "status": "queued",
    }
