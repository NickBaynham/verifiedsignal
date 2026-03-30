"""
HTTP remote document scorer — POST JSON to an operator-controlled endpoint.

Contract: see docs/scoring-http.md
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator

log = logging.getLogger("verifiedsignal.score_http")

HTTP_SCORER_NAME = "verifiedsignal_http"
HTTP_REQUEST_SCHEMA_VERSION = 1
HTTP_RESPONSE_SCHEMA_VERSION = 1


class RemoteScoreResult(BaseModel):
    """Validated subset of the remote JSON body mapped onto document_scores columns."""

    factuality_score: float | None = None
    ai_generation_probability: float | None = None
    fallacy_score: float | None = None
    confidence_score: float | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "factuality_score",
        "ai_generation_probability",
        "fallacy_score",
        "confidence_score",
    )
    @classmethod
    def _clamp_unit_interval(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0.0 or v > 1.0:
            raise ValueError("scores must be within [0, 1]")
        return v


class ScoringRetryableError(Exception):
    """Transient failure — ARQ should retry the job."""


class ScoringPermanentError(Exception):
    """Non-retryable scoring failure (record terminal row and exit successfully)."""


def content_fingerprint(*, body_text: str | None, content_sha256: bytes | None) -> str:
    """Stable idempotency key: prefer DB hash, else SHA-256 of UTF-8 body."""
    if content_sha256:
        return content_sha256.hex()
    raw = (body_text or "").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_request_payload(
    *,
    document_id: str,
    title: str | None,
    body_text: str,
    content_type: str | None,
    fingerprint: str,
    max_body_chars: int,
) -> dict[str, Any]:
    truncated = body_text if len(body_text) <= max_body_chars else body_text[:max_body_chars]
    return {
        "schema_version": HTTP_REQUEST_SCHEMA_VERSION,
        "document_id": document_id,
        "title": title,
        "body_text": truncated,
        "body_text_truncated": len(body_text) > max_body_chars,
        "content_type": content_type,
        "content_fingerprint": fingerprint,
    }


def parse_remote_score_body(data: dict[str, Any]) -> RemoteScoreResult:
    ver = data.get("schema_version", HTTP_RESPONSE_SCHEMA_VERSION)
    if ver != HTTP_RESPONSE_SCHEMA_VERSION:
        raise ScoringPermanentError(f"unsupported response schema_version: {ver!r}")
    known = {
        "schema_version",
        "factuality_score",
        "ai_generation_probability",
        "fallacy_score",
        "confidence_score",
        "metadata",
    }
    extra = {k: v for k, v in data.items() if k not in known}
    meta = data.get("metadata")
    if isinstance(meta, dict):
        extra["remote_metadata"] = meta
    try:
        return RemoteScoreResult(
            factuality_score=data.get("factuality_score"),
            ai_generation_probability=data.get("ai_generation_probability"),
            fallacy_score=data.get("fallacy_score"),
            confidence_score=data.get("confidence_score"),
            extra=extra,
        )
    except ValidationError as e:
        raise ScoringPermanentError(f"invalid remote scores: {e}") from e


def post_remote_score(
    *,
    url: str,
    bearer_token: str | None,
    payload: dict[str, Any],
    timeout_s: float,
) -> tuple[int, dict[str, Any], float]:
    """
    POST JSON to the remote scorer. Returns (status_code, parsed_json_or_empty, latency_ms).

    Raises ScoringRetryableError on network / 5xx / rate limits.
    Raises ScoringPermanentError on 4xx (except retryable) or invalid success body.
    """
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    started = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise ScoringRetryableError("remote scorer timeout") from e
    except httpx.RequestError as e:
        raise ScoringRetryableError(f"remote scorer request error: {e}") from e

    latency_ms = (time.perf_counter() - started) * 1000.0
    code = resp.status_code
    if code in (408, 429) or code >= 500:
        raise ScoringRetryableError(f"remote scorer HTTP {code}")
    if code != 200:
        snippet = resp.text[:500] if resp.text else ""
        raise ScoringPermanentError(f"remote scorer HTTP {code}: {snippet}")

    try:
        body = resp.json()
    except Exception as e:
        raise ScoringPermanentError("remote scorer returned non-JSON body") from e
    if not isinstance(body, dict):
        raise ScoringPermanentError("remote scorer JSON must be an object")

    return code, body, latency_ms
