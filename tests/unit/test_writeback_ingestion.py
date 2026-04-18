"""Unit tests: internal write-back ingestion hooks delegate to service with expected provenance."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from app.services import writeback_ingestion as wi


def test_runtime_evidence_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def _capture(*_args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(wi.wb_svc, "create_evidence_note", _capture)
    session = MagicMock()
    mid = uuid.uuid4()
    wi.record_runtime_evidence(
        session,
        auth_sub="sub-1",
        model_id=mid,
        title="log excerpt",
        details="timeout",
    )
    body = captured["body"]
    assert body.provenance is not None
    assert body.provenance.origin_type == "runtime_evidence"
    assert body.provenance.verification_state == "auto_ingested"
    assert captured["model_id"] == mid
