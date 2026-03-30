"""Unit tests for plain-text extraction from raw bytes."""

from __future__ import annotations

import pytest
from app.services.document_text_extract import extract_plain_text_from_bytes


@pytest.mark.unit
def test_extract_plain_utf8() -> None:
    text, note = extract_plain_text_from_bytes(b"hello world", "text/plain")
    assert text == "hello world"
    assert note is None


@pytest.mark.unit
def test_extract_json() -> None:
    raw = b'{"a": 1}'
    text, note = extract_plain_text_from_bytes(raw, "application/json")
    assert '{"a": 1}' in text
    assert note is None


@pytest.mark.unit
def test_extract_html_strips_tags() -> None:
    text, note = extract_plain_text_from_bytes(
        b"<p>Hello <b>world</b></p>",
        "text/html",
    )
    assert "Hello" in text
    assert "world" in text
    assert "<p>" not in text
    assert note is None


@pytest.mark.unit
def test_extract_binary_skips() -> None:
    text, note = extract_plain_text_from_bytes(b"\x00\x01\xff\xfe", "application/octet-stream")
    assert text == ""
    assert note == "binary_or_unsupported_content_type"


@pytest.mark.unit
def test_extract_empty() -> None:
    text, note = extract_plain_text_from_bytes(b"", "text/plain")
    assert text == ""
    assert note == "empty_bytes"
