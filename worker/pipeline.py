"""
Document processing pipeline (scaffold).

Intended evolution:
1. Load document + sources from Postgres (system-of-record).
2. Extract text / features; store artifacts in object storage (MinIO/S3).
3. Run scoring / LLM steps; persist `document_scores` + `pipeline_events`.
4. Index derived fields into OpenSearch (rebuildable; replay from Postgres + events).
"""

from __future__ import annotations

import asyncio
from typing import Any

from worker.events import emit_worker_event
from worker.logging import get_logger

log = get_logger("veridoc.worker.pipeline")

# Simulated stages — map to `pipeline_runs.stage` values in the real system.
STAGES = ("ingest", "extract", "enrich", "score", "index", "finalize")


async def run_document_pipeline(ctx: dict[str, Any], document_id: str) -> None:
    """
    Placeholder pipeline: sleeps between stages and emits events.

    `ctx` is the ARQ job context (`ctx['job_id']`, redis, etc.).
    """
    job_id = ctx.get("job_id", "unknown")
    log.info("pipeline_start document_id=%s job_id=%s", document_id, job_id)
    emit_worker_event(
        "pipeline_started",
        {"document_id": document_id, "job_id": job_id},
    )

    for stage in STAGES:
        await asyncio.sleep(0.05)
        log.info("pipeline_stage document_id=%s stage=%s", document_id, stage)
        emit_worker_event(
            "pipeline_stage",
            {"document_id": document_id, "stage": stage, "job_id": job_id},
        )

    log.info("pipeline_complete document_id=%s", document_id)
    emit_worker_event(
        "pipeline_completed",
        {"document_id": document_id, "job_id": job_id},
    )
