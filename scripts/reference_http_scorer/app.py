"""
Reference HTTP scorer for local / operator testing.

Contract: docs/scoring-http.md (schema_version 1 request + response).

Run from repository root:

  PYTHONPATH=scripts uvicorn reference_http_scorer.app:app --host 127.0.0.1 --port 9100

Then set on the worker host:

  ENQUEUE_SCORE_AFTER_PIPELINE=true
  SCORE_ASYNC_BACKEND=http
  SCORE_HTTP_URL=http://127.0.0.1:9100/score

Optional: REFERENCE_SCORER_BEARER_TOKEN=secret — require Authorization: Bearer …
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

EXPECTED_REQUEST_SCHEMA = 1
RESPONSE_SCHEMA = 1


class ScoreRequestV1(BaseModel):
    schema_version: int
    document_id: str
    title: str | None = None
    body_text: str = ""
    body_text_truncated: bool = False
    content_type: str | None = None
    content_fingerprint: str = ""


app = FastAPI(
    title="VerifiedSignal reference HTTP scorer",
    version="0.1.0",
    description="POST /score — mirrors docs/scoring-http.md for copy-paste integration tests.",
)


def _scores_from_demo(body_text: str, fingerprint: str) -> dict[str, Any]:
    """Deterministic, boring scores so operators can spot rows in DB."""
    n = max(1, len(body_text))
    # Map length + fingerprint nibbles into [0.15, 0.85] to stay away from clamps.
    h = int(fingerprint[:8], 16) % 97 if len(fingerprint) >= 8 else 42
    base = 0.15 + (h % 70) / 100.0
    factuality = min(0.92, base + (n % 7) * 0.01)
    ai_prob = min(0.88, 0.2 + (n % 11) * 0.05)
    fallacy = min(0.75, 0.15 + (h % 5) * 0.1)
    confidence = min(0.9, 0.5 + (n % 5) * 0.08)
    return {
        "schema_version": RESPONSE_SCHEMA,
        "factuality_score": round(factuality, 4),
        "ai_generation_probability": round(ai_prob, 4),
        "fallacy_score": round(fallacy, 4),
        "confidence_score": round(confidence, 4),
        "metadata": {
            "scorer": "reference_http_scorer",
            "note": "Replace with your model; this service is for wiring tests only.",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score")
def score(
    body: ScoreRequestV1,
    authorization: str | None = Header(default=None, convert_underscores=False),
) -> dict[str, Any]:
    expected = os.environ.get("REFERENCE_SCORER_BEARER_TOKEN", "").strip()
    if expected:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing Authorization: Bearer")
        token = authorization.removeprefix("Bearer ").strip()
        if token != expected:
            raise HTTPException(status_code=403, detail="invalid bearer token")

    if body.schema_version != EXPECTED_REQUEST_SCHEMA:
        raise HTTPException(
            status_code=400,
            detail=(
                f"unsupported schema_version: {body.schema_version} "
                f"(expected {EXPECTED_REQUEST_SCHEMA})"
            ),
        )

    return _scores_from_demo(body.body_text, body.content_fingerprint)
