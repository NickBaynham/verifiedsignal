"""Unit tests: core intake orchestration with mocked storage and DB session."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.document_service import run_file_intake
from app.services.storage_service import InMemoryObjectStorage


@pytest.mark.unit
def test_run_file_intake_commits_document_storage_and_enqueue(monkeypatch):
    """Session and storage are real objects; enqueue is stubbed to avoid asyncio/Redis."""
    storage = InMemoryObjectStorage(bucket="test-bucket")
    session = MagicMock()
    fake_doc = MagicMock()
    session.get = MagicMock(return_value=fake_doc)

    monkeypatch.setattr(
        "app.services.document_service.enqueue_process_document_sync",
        lambda _did: "job-123",
    )
    hub = MagicMock()
    hub.publish = AsyncMock()
    monkeypatch.setattr("app.services.document_service.get_event_hub", lambda: hub)

    out = run_file_intake(
        session,
        file_bytes=b"abc",
        original_filename="doc.txt",
        content_type="text/plain",
        title=None,
        collection_id_param=None,
        storage=storage,
        settings=MagicMock(
            default_collection_id=uuid.UUID("00000000-0000-4000-8000-000000000002"),
            max_upload_bytes=1024,
        ),
    )

    assert out["status"] == "queued"
    assert out["job_id"] == "job-123"
    assert out["storage_key"].startswith("raw/")
    assert out["storage_key"] in storage.objects
    assert session.commit.call_count >= 2
