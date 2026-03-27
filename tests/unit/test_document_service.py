"""Unit tests for document submission / queue handoff."""

from __future__ import annotations

import asyncio

import pytest
from app.core.config import reset_settings_cache
from app.services.document_service import submit_document_for_processing
from app.services.queue_backend import close_job_queue, get_memory_queue


@pytest.mark.unit
def test_submit_document_uses_fake_queue(monkeypatch):
    monkeypatch.setenv("USE_FAKE_QUEUE", "true")
    reset_settings_cache()

    async def run():
        await close_job_queue()
        result = await submit_document_for_processing(
            title="Hello",
            source_uri="https://example.com/x",
            metadata={"k": "v"},
        )
        assert result["status"] == "queued"
        assert result["document_id"]
        assert result["job_id"]
        q = get_memory_queue()
        assert len(q.jobs) == 1
        jid, did = q.jobs[0]
        assert jid == result["job_id"]
        assert did == result["document_id"]
        await close_job_queue()

    asyncio.run(run())
    reset_settings_cache()
