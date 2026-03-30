"""Collection-level aggregates: OpenSearch facets + Postgres score rollups."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Document, DocumentScore
from app.schemas.collection import (
    CollectionAnalyticsOut,
    CollectionPostgresStatsOut,
    FacetBucketOut,
)
from app.services.document_access import resolve_accessible_collection_ids
from app.services.opensearch_document_index import facet_aggregation_sync
from app.services.search_filters import SearchFilters


def _postgres_collection_stats(
    session: Session,
    collection_id: uuid.UUID,
) -> CollectionPostgresStatsOut:
    doc_count = session.scalar(
        select(func.count()).select_from(Document).where(Document.collection_id == collection_id)
    )
    doc_count = int(doc_count or 0)

    scored_count = session.scalar(
        select(func.count(DocumentScore.id))
        .join(Document, Document.id == DocumentScore.document_id)
        .where(
            Document.collection_id == collection_id,
            DocumentScore.is_canonical.is_(True),
        )
    )
    scored_count = int(scored_count or 0)

    avg_f = session.scalar(
        select(func.avg(DocumentScore.factuality_score))
        .join(Document, Document.id == DocumentScore.document_id)
        .where(
            Document.collection_id == collection_id,
            DocumentScore.is_canonical.is_(True),
            DocumentScore.factuality_score.isnot(None),
        )
    )
    avg_ai = session.scalar(
        select(func.avg(DocumentScore.ai_generation_probability))
        .join(Document, Document.id == DocumentScore.document_id)
        .where(
            Document.collection_id == collection_id,
            DocumentScore.is_canonical.is_(True),
            DocumentScore.ai_generation_probability.isnot(None),
        )
    )

    suspicious = session.scalar(
        select(func.count())
        .select_from(DocumentScore)
        .join(Document, Document.id == DocumentScore.document_id)
        .where(
            Document.collection_id == collection_id,
            DocumentScore.is_canonical.is_(True),
            or_(
                DocumentScore.ai_generation_probability > 0.65,
                DocumentScore.factuality_score < 0.45,
            ),
        )
    )
    suspicious = int(suspicious or 0)

    return CollectionPostgresStatsOut(
        document_count=doc_count,
        scored_documents=scored_count,
        avg_factuality=float(avg_f) if avg_f is not None else None,
        avg_ai_probability=float(avg_ai) if avg_ai is not None else None,
        suspicious_count=suspicious,
    )


async def get_collection_analytics(
    session: Session,
    *,
    auth_sub: str,
    collection_id: uuid.UUID,
    settings: Settings | None = None,
) -> CollectionAnalyticsOut:
    settings = settings or get_settings()
    allowed = resolve_accessible_collection_ids(session, auth_sub, settings)
    if collection_id not in allowed:
        raise HTTPException(status_code=403, detail="collection not accessible")

    filters = SearchFilters(
        collection_ids=(str(collection_id),),
        content_type=None,
        status=None,
        ingest_source=None,
        tags_all=(),
    )
    raw: dict[str, Any] = await asyncio.to_thread(
        facet_aggregation_sync,
        filters=filters,
        settings=settings,
    )

    facets_out: dict[str, list[FacetBucketOut]] | None = None
    if raw.get("facets"):
        facets_out = {}
        for k, buckets in raw["facets"].items():
            facets_out[k] = [
                FacetBucketOut(
                    key=str(b.get("key")) if b.get("key") is not None else None,
                    count=int(b.get("count", 0)),
                )
                for b in (buckets or [])
            ]

    pg = _postgres_collection_stats(session, collection_id)

    return CollectionAnalyticsOut(
        collection_id=collection_id,
        index_total=int(raw.get("total") or 0),
        index_status=str(raw.get("index_status") or ""),
        index_message=raw.get("message"),
        facets=facets_out,
        postgres=pg,
    )
