"""Unit tests: queue enqueue and collection resolution."""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from app.core.config import Settings, reset_settings_cache
from app.services.document_service import resolve_collection_id
from app.services.exceptions import IntakeValidationError
from app.services.queue_backend import close_job_queue, get_memory_queue
from app.services.queue_service import enqueue_fetch_url_ingest, enqueue_process_document


@pytest.mark.unit
def test_resolve_collection_id_explicit_uuid_string():
    cid = uuid.uuid4()
    s = Settings.model_construct(
        default_collection_id=None,
        database_url="postgresql://x",
        redis_url="redis://x",
    )
    assert resolve_collection_id(str(cid), s) == cid


@pytest.mark.unit
def test_resolve_collection_id_uses_env_default(monkeypatch):
    cid = uuid.uuid4()
    monkeypatch.setenv("VERIFIEDSIGNAL_DEFAULT_COLLECTION_ID", str(cid))
    monkeypatch.setenv("VERIFIEDSIGNAL_ALLOW_DEFAULT_COLLECTION_FALLBACK", "true")
    reset_settings_cache()
    from app.core.config import get_settings

    try:
        s = get_settings()
        assert resolve_collection_id(None, s) == cid
        assert resolve_collection_id("", s) == cid
    finally:
        monkeypatch.delenv("VERIFIEDSIGNAL_ALLOW_DEFAULT_COLLECTION_FALLBACK", raising=False)
        reset_settings_cache()


@pytest.mark.unit
def test_resolve_collection_id_invalid_uuid():
    with pytest.raises(IntakeValidationError, match="invalid collection_id"):
        resolve_collection_id(
            "nope",
            Settings.model_construct(
                default_collection_id=None,
                database_url="postgresql://x",
                redis_url="redis://x",
            ),
        )


@pytest.mark.unit
def test_enqueue_process_document_records_on_fake_queue():
    os.environ["USE_FAKE_QUEUE"] = "true"
    reset_settings_cache()

    async def _run():
        await close_job_queue()
        did = str(uuid.uuid4())
        jid = await enqueue_process_document(did)
        assert jid
        q = get_memory_queue()
        assert q.jobs == [(jid, "process_document", did)]
        await close_job_queue()

    asyncio.run(_run())
    reset_settings_cache()
    os.environ.pop("USE_FAKE_QUEUE", None)


@pytest.mark.unit
def test_enqueue_fetch_url_ingest_records_on_fake_queue():
    os.environ["USE_FAKE_QUEUE"] = "true"
    reset_settings_cache()

    async def _run():
        await close_job_queue()
        did = str(uuid.uuid4())
        jid = await enqueue_fetch_url_ingest(did)
        assert jid
        q = get_memory_queue()
        assert q.jobs == [(jid, "fetch_url_and_ingest", did)]
        await close_job_queue()

    asyncio.run(_run())
    reset_settings_cache()
    os.environ.pop("USE_FAKE_QUEUE", None)
