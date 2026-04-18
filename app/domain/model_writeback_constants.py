"""Allowed values for model write-back artifacts (V1)."""

from __future__ import annotations

ARTIFACT_KINDS = frozenset(
    {
        "finding",
        "risk",
        "test_artifact",
        "execution_result",
        "evidence_note",
        "contradiction",
    }
)

ORIGIN_TYPES = frozenset(
    {
        "human",
        "agent",
        "imported_system",
        "runtime_evidence",
        "internal_service",
    }
)

VERIFICATION_STATES = frozenset(
    {
        "proposed",
        "accepted",
        "rejected",
        "auto_ingested",
        "superseded",
    }
)

TEST_ARTIFACT_SUBTYPES = frozenset(
    {
        "scenario",
        "test_case",
        "script_reference",
        "coverage_note",
    }
)

EXECUTION_STATUSES = frozenset(
    {
        "passed",
        "failed",
        "skipped",
        "error",
        "running",
        "unknown",
    }
)
