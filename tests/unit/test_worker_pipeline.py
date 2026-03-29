"""Unit tests for worker pipeline simulation."""

from __future__ import annotations

import asyncio

import pytest
import worker.pipeline as worker_pipeline
from worker.pipeline import STAGES, run_document_pipeline


@pytest.mark.unit
def test_pipeline_runs_without_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(worker_pipeline, "run_pipeline_job", lambda _d, _j: None)

    async def run():
        await run_document_pipeline({"job_id": "job-unit"}, "00000000-0000-4000-8000-000000000099")

    asyncio.run(run())


@pytest.mark.unit
def test_pipeline_stages_cover_processing_lifecycle():
    assert STAGES[0] == "ingest"
    assert STAGES[-1] == "finalize"
    assert "score" in STAGES
    assert "index" in STAGES
