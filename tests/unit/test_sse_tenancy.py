"""Unit tests: SSE line filtering by subscriber auth_sub."""

import json

import pytest
from app.api.routes.events import sse_event_visible_to_subscriber


@pytest.mark.unit
def test_sse_visible_when_subscriber_unset():
    line = json.dumps({"type": "x", "payload": {"auth_sub": "other"}})
    assert sse_event_visible_to_subscriber(line, None) is True


@pytest.mark.unit
def test_sse_visible_when_auth_sub_matches():
    sub = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    line = json.dumps({"type": "document_queued", "payload": {"auth_sub": sub, "document_id": "x"}})
    assert sse_event_visible_to_subscriber(line, sub) is True


@pytest.mark.unit
def test_sse_hidden_when_auth_sub_mismatches():
    line = json.dumps(
        {"type": "document_queued", "payload": {"auth_sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}}
    )
    assert sse_event_visible_to_subscriber(line, "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb") is False


@pytest.mark.unit
def test_sse_hidden_when_payload_missing_auth_sub():
    line = json.dumps({"type": "document_queued", "payload": {"document_id": "x"}})
    assert sse_event_visible_to_subscriber(line, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa") is False
