"""
Deterministic text heuristics for canonical `document_scores` (not ML).

Replaces opaque defaults until real models ship; values are conservative proxies only.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models import DocumentScore


def compute_heuristic_scores(
    body_text: str | None,
) -> tuple[float | None, float | None, dict[str, Any]]:
    """
    Returns (factuality_score, ai_generation_probability, debug payload) in [0, 1] or Nones.
    """
    if body_text is None or not str(body_text).strip():
        return None, None, {"reason": "no_body", "method": "heuristic_v1"}

    text = str(body_text).strip()
    words = re.findall(r"\S+", text)
    n = len(words)
    if n == 0:
        return None, None, {"reason": "no_words", "method": "heuristic_v1"}

    lowered = [w.lower() for w in words]
    uniq = len(set(lowered))
    ratio = uniq / n

    # Low lexical diversity → higher synthetic-text proxy (very rough).
    ai_gen = max(0.0, min(1.0, 1.0 - min(1.0, ratio * 1.15)))
    # Slightly reward diversity as a weak "human-like variety" stand-in for factuality proxy.
    fact = max(0.0, min(1.0, 0.2 + ratio * 0.75))

    payload: dict[str, Any] = {
        "method": "heuristic_v1",
        "word_count": n,
        "char_count": len(text),
        "unique_word_ratio": round(ratio, 4),
    }
    return round(fact, 5), round(ai_gen, 5), payload


def write_heuristic_canonical_score(
    session: Session,
    *,
    document_id: uuid.UUID,
    pipeline_run_id: uuid.UUID | None,
    body_text: str | None,
) -> DocumentScore | None:
    fact, ai_gen, dbg = compute_heuristic_scores(body_text)
    if fact is None and ai_gen is None:
        return None

    session.execute(
        update(DocumentScore)
        .where(DocumentScore.document_id == document_id)
        .values(is_canonical=False)
    )

    row = DocumentScore(
        document_id=document_id,
        pipeline_run_id=pipeline_run_id,
        scorer_name="verifiedsignal_heuristic",
        scorer_version="1.0.0",
        score_schema_version=1,
        is_canonical=True,
        factuality_score=fact,
        ai_generation_probability=ai_gen,
        fallacy_score=None,
        confidence_score=0.35,
        score_payload=dbg,
    )
    session.add(row)
    return row
