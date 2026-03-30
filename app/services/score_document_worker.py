"""
Background scoring: stub row, or HTTP remote scorer (idempotency + optional canonical promotion).

Pipeline stage writes heuristic `verifiedsignal_heuristic` (canonical unless promoted below).
Runs when `ENQUEUE_SCORE_AFTER_PIPELINE=true`.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Document, DocumentScore
from app.db.session import get_session_factory
from app.services.score_http_remote import (
    HTTP_SCORER_NAME,
    ScoringPermanentError,
    ScoringRetryableError,
    build_request_payload,
    content_fingerprint,
    parse_remote_score_body,
    post_remote_score,
)

log = logging.getLogger("verifiedsignal.score_document")

STUB_SCORER_NAME = "verifiedsignal_stub"
STUB_SCORER_VERSION = "0.1.0"


def _sha_bytes(blob: object | None) -> bytes | None:
    if blob is None:
        return None
    if isinstance(blob, memoryview):
        return blob.tobytes()
    return bytes(blob)


def run_score_document_sync(document_id: str) -> None:
    SessionLocal = get_session_factory()
    session: Session = SessionLocal()
    try:
        _run_score_document(session, uuid.UUID(document_id), settings=get_settings())
        session.commit()
    except ScoringRetryableError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _terminal_http_attempt_exists(session: Session, document_id: uuid.UUID, fp: str) -> bool:
    rows = session.scalars(
        select(DocumentScore).where(
            DocumentScore.document_id == document_id,
            DocumentScore.scorer_name == HTTP_SCORER_NAME,
        )
    ).all()
    for row in rows:
        pl = row.score_payload or {}
        if pl.get("content_fingerprint") != fp:
            continue
        if pl.get("job_status") in ("completed", "failed_terminal"):
            return True
    return False


def _demote_all_canonical(session: Session, document_id: uuid.UUID) -> None:
    session.execute(
        update(DocumentScore)
        .where(DocumentScore.document_id == document_id)
        .values(is_canonical=False)
    )


def _insert_stub_row(session: Session, doc: Document, *, note: str) -> None:
    row = DocumentScore(
        document_id=doc.id,
        pipeline_run_id=None,
        scorer_name=STUB_SCORER_NAME,
        scorer_version=STUB_SCORER_VERSION,
        score_schema_version=1,
        is_canonical=False,
        score_payload={
            "kind": "stub",
            "status": "stub",
            "note": note,
            "job_status": "completed",
            "content_fingerprint": content_fingerprint(
                body_text=doc.body_text,
                content_sha256=_sha_bytes(doc.content_sha256),
            ),
        },
    )
    session.add(row)
    log.info("score_document_stub_insert document_id=%s", doc.id)


def _run_http_scorer(session: Session, doc: Document, settings: Settings) -> None:
    url = (settings.score_http_url or "").strip()
    if not url:
        log.warning("score_async_backend=http but SCORE_HTTP_URL empty; using stub")
        _insert_stub_row(
            session,
            doc,
            note="SCORE_HTTP_URL not set; configure remote scorer or use score_async_backend=stub",
        )
        return

    fp = content_fingerprint(
        body_text=doc.body_text,
        content_sha256=_sha_bytes(doc.content_sha256),
    )
    if _terminal_http_attempt_exists(session, doc.id, fp):
        log.info("score_document_idempotent_skip document_id=%s fingerprint=%s", doc.id, fp[:16])
        return

    body_text = doc.body_text or ""
    req = build_request_payload(
        document_id=str(doc.id),
        title=doc.title,
        body_text=body_text,
        content_type=doc.content_type,
        fingerprint=fp,
        max_body_chars=settings.score_http_max_body_chars,
    )

    try:
        _code, resp_body, latency_ms = post_remote_score(
            url=url,
            bearer_token=(settings.score_http_bearer_token or None),
            payload=req,
            timeout_s=settings.score_http_timeout_s,
        )
        parsed = parse_remote_score_body(resp_body)
    except ScoringPermanentError as e:
        log.warning("score_document_permanent_error document_id=%s err=%s", doc.id, e)
        session.add(
            DocumentScore(
                document_id=doc.id,
                pipeline_run_id=None,
                scorer_name=HTTP_SCORER_NAME,
                scorer_version=settings.score_http_scorer_version,
                score_schema_version=1,
                is_canonical=False,
                factuality_score=None,
                ai_generation_probability=None,
                fallacy_score=None,
                confidence_score=None,
                score_payload={
                    "kind": "http_remote_v1",
                    "job_status": "failed_terminal",
                    "content_fingerprint": fp,
                    "error": str(e),
                    "latency_ms": None,
                },
            )
        )
        return

    if settings.score_api_promote_canonical:
        _demote_all_canonical(session, doc.id)

    session.add(
        DocumentScore(
            document_id=doc.id,
            pipeline_run_id=None,
            scorer_name=HTTP_SCORER_NAME,
            scorer_version=settings.score_http_scorer_version,
            score_schema_version=1,
            is_canonical=settings.score_api_promote_canonical,
            factuality_score=parsed.factuality_score,
            ai_generation_probability=parsed.ai_generation_probability,
            fallacy_score=parsed.fallacy_score,
            confidence_score=parsed.confidence_score,
            score_payload={
                "kind": "http_remote_v1",
                "job_status": "completed",
                "content_fingerprint": fp,
                "latency_ms": round(latency_ms, 3),
                "request": {
                    "schema_version": req["schema_version"],
                    "body_text_truncated": req["body_text_truncated"],
                },
                "response": {**parsed.extra, "parsed_scores": parsed.model_dump(exclude={"extra"})},
            },
        )
    )
    log.info(
        "score_document_http_ok document_id=%s promote_canonical=%s",
        doc.id,
        settings.score_api_promote_canonical,
    )


def _run_score_document(session: Session, document_id: uuid.UUID, *, settings: Settings) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        log.warning("score_document_missing document_id=%s", document_id)
        return

    backend = settings.score_async_backend.strip().lower()
    if backend == "http":
        _run_http_scorer(session, doc, settings)
        return

    # default: stub
    _insert_stub_row(
        session,
        doc,
        note="score_async_backend=stub (set to http + SCORE_HTTP_URL for remote API scoring)",
    )
