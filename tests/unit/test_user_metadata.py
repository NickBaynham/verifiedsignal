"""Unit tests: intake user_metadata validation and index helpers."""

from __future__ import annotations

import pytest
from app.services.exceptions import IntakeValidationError
from app.services.user_metadata import (
    extract_metadata_label,
    extract_tags_for_index,
    flatten_metadata_for_search_text,
    parse_metadata_json_string,
    validate_user_metadata,
)


@pytest.mark.unit
def test_validate_user_metadata_tags_and_label():
    m = validate_user_metadata({"tags": ["a", "b"], "label": "  x  "})
    assert m["tags"] == ["a", "b"]
    assert extract_tags_for_index(m) == ["a", "b"]
    assert extract_metadata_label(m) == "x"


@pytest.mark.unit
def test_validate_rejects_bad_tags():
    with pytest.raises(IntakeValidationError, match="tags"):
        validate_user_metadata({"tags": "not-a-list"})


@pytest.mark.unit
def test_parse_metadata_json_string():
    assert parse_metadata_json_string(None) is None
    assert parse_metadata_json_string("") is None
    d = parse_metadata_json_string('{"tags":["z"]}')
    assert d == {"tags": ["z"]}


@pytest.mark.unit
def test_flatten_metadata_for_search_text():
    t = flatten_metadata_for_search_text({"note": "hello", "n": 1, "skip": []})
    assert "hello" in t
    assert "1" in t
