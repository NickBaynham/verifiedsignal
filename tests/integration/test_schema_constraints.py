"""Integration tests: constraints and relationships on the canonical schema."""

from __future__ import annotations

import uuid

import psycopg.errors
import pytest


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


def _seed_document(db_conn, suffix: str):
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, display_name) VALUES (%s, %s) RETURNING id",
            (f"u_{suffix}@example.com", "U"),
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO organizations (name, slug) VALUES (%s, %s) RETURNING id",
            (f"O {suffix}", f"o-{suffix}"),
        )
        org_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s,%s,%s)",
            (org_id, user_id, "owner"),
        )
        cur.execute(
            "INSERT INTO collections (organization_id, name, slug) VALUES (%s,%s,%s) RETURNING id",
            (org_id, "C", f"c-{suffix}"),
        )
        col_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO documents (collection_id, title, status)
            VALUES (%s, %s, 'active') RETURNING id
            """,
            (col_id, "D"),
        )
        return cur.fetchone()[0]


@pytest.mark.integration
def test_organization_collection_document_hierarchy(db_conn):
    s = _unique_suffix()
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, display_name) VALUES (%s, %s) RETURNING id",
            (f"user_{s}@example.com", "User"),
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO organizations (name, slug) VALUES (%s, %s) RETURNING id",
            (f"Org {s}", f"org-{s}"),
        )
        org_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s, %s, %s)",
            (org_id, user_id, "member"),
        )
        cur.execute(
            """
            INSERT INTO collections (organization_id, name, slug)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (org_id, "Collection", f"col-{s}"),
        )
        collection_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO documents (collection_id, title, external_key, status)
            VALUES (%s, %s, %s, 'active') RETURNING id
            """,
            (collection_id, "Doc", f"ext-{s}"),
        )
        document_id = cur.fetchone()[0]
    assert document_id


@pytest.mark.integration
def test_document_sources_and_pipeline(db_conn):
    s = _unique_suffix()
    document_id = _seed_document(db_conn, s)
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO document_sources (document_id, source_kind, locator)
            VALUES (%s, 'url', %s)
            """,
            (document_id, f"https://example.com/{s}"),
        )
        cur.execute(
            """
            INSERT INTO pipeline_runs (
              document_id, pipeline_name, pipeline_version, status, stage, started_at
            )
            VALUES (%s, 'ingest', '1.0.0', 'running', 'ingest', now())
            RETURNING id
            """,
            (document_id,),
        )
        run_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO pipeline_events (pipeline_run_id, step_index, event_type, stage, payload)
            VALUES (%s, 0, 'started', 'ingest', '{}'::jsonb)
            """,
            (run_id,),
        )
    assert run_id


@pytest.mark.integration
def test_only_one_canonical_score_per_document(db_conn):
    s = _unique_suffix()
    document_id = _seed_document(db_conn, s)
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO document_scores (
              document_id, scorer_name, scorer_version, is_canonical, factuality_score
            )
            VALUES (%s, 'model-a', '1.0.0', true, 0.5)
            """,
            (document_id,),
        )
        with pytest.raises(psycopg.errors.UniqueViolation):
            cur.execute(
                """
                INSERT INTO document_scores (
                  document_id, scorer_name, scorer_version, is_canonical, confidence_score
                )
                VALUES (%s, 'model-a', '1.0.0', true, 0.9)
                """,
                (document_id,),
            )


@pytest.mark.integration
def test_score_columns_reject_out_of_range(db_conn):
    s = _unique_suffix()
    document_id = _seed_document(db_conn, s)
    with db_conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO document_scores (
                  document_id, scorer_name, scorer_version, is_canonical, factuality_score
                )
                VALUES (%s, 'model-a', '1.0.0', false, 1.01)
                """,
                (document_id,),
            )


@pytest.mark.integration
def test_pipeline_run_completed_after_started_enforced(db_conn):
    s = _unique_suffix()
    document_id = _seed_document(db_conn, s)
    with db_conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO pipeline_runs (
                  document_id, pipeline_name, pipeline_version,
                  status, stage, started_at, completed_at
                )
                VALUES (%s, 'p', '1', 'failed', 'ingest',
                        now(), now() - interval '1 hour')
                """,
                (document_id,),
            )
