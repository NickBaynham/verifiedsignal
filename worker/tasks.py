"""ARQ task entrypoints."""

from __future__ import annotations

from typing import Any

from worker.logging import get_logger
from worker.pipeline import run_document_pipeline

log = get_logger("veridoc.worker.tasks")


async def process_document(ctx: dict[str, Any], document_id: str) -> str:
    """
    Background job: process a single document through the scaffold pipeline.

    Name must match API enqueue: `enqueue_job("process_document", document_id)`.
    """
    log.info("task_process_document document_id=%s", document_id)
    await run_document_pipeline(ctx, document_id)
    return document_id
