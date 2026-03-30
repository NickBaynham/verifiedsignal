"""Validate and normalize `documents.user_metadata` at intake; derive index fields."""

from __future__ import annotations

import json
from typing import Any

from app.services.exceptions import IntakeValidationError

_MAX_JSON_BYTES = 16_384
_MAX_TAGS = 64
_MAX_TAG_LEN = 64
_MAX_TOP_LEVEL_KEYS = 48


def parse_metadata_json_string(raw: str | None) -> dict[str, Any] | None:
    """Parse optional multipart form field ``metadata`` (JSON object string)."""
    if raw is None or str(raw).strip() == "":
        return None
    try:
        val = json.loads(raw)
    except json.JSONDecodeError as e:
        raise IntakeValidationError("metadata must be valid JSON") from e
    if not isinstance(val, dict):
        raise IntakeValidationError("metadata JSON must be an object")
    return val


def validate_user_metadata(raw: dict[str, Any] | None) -> dict[str, Any]:
    """
    Enforce size and shape; return a plain dict safe for JSONB.

    Convention: ``tags`` — list of short strings; ``label`` — single string facet.
    """
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raise IntakeValidationError("metadata must be a JSON object")
    if len(raw) > _MAX_TOP_LEVEL_KEYS:
        raise IntakeValidationError("metadata has too many keys")
    try:
        blob = json.dumps(raw, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise IntakeValidationError("metadata must be JSON-serializable") from e
    if len(blob.encode("utf-8")) > _MAX_JSON_BYTES:
        raise IntakeValidationError("metadata JSON exceeds size limit")

    tags = raw.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            raise IntakeValidationError("metadata.tags must be a list")
        if len(tags) > _MAX_TAGS:
            raise IntakeValidationError("metadata.tags has too many entries")
        for t in tags:
            if not isinstance(t, str):
                raise IntakeValidationError("metadata.tags entries must be strings")
            if len(t.strip()) > _MAX_TAG_LEN:
                raise IntakeValidationError("metadata.tags entry too long")

    label = raw.get("label")
    if label is not None and not isinstance(label, str):
        raise IntakeValidationError("metadata.label must be a string")
    if isinstance(label, str) and len(label) > 256:
        raise IntakeValidationError("metadata.label too long")

    return raw


def extract_tags_for_index(meta: dict[str, Any]) -> list[str]:
    t = meta.get("tags")
    if not isinstance(t, list):
        return []
    out: list[str] = []
    for x in t:
        if isinstance(x, str):
            s = x.strip()
            if s:
                out.append(s[:_MAX_TAG_LEN])
    return out[:_MAX_TAGS]


def extract_metadata_label(meta: dict[str, Any]) -> str | None:
    label = meta.get("label")
    if isinstance(label, str):
        s = label.strip()
        return s[:256] if s else None
    return None


def flatten_metadata_for_search_text(meta: dict[str, Any], *, max_chars: int = 8000) -> str:
    """Concatenate primitive string/number values for a secondary text field."""
    parts: list[str] = []
    for _k, v in sorted(meta.items(), key=lambda kv: kv[0]):
        if isinstance(v, str):
            parts.append(v.strip())
        elif isinstance(v, (int, float, bool)):
            parts.append(str(v))
    text = " ".join(p for p in parts if p)
    return text[:max_chars]
