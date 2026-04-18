"""API schemas for model write-back (V1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.model_writeback_constants import (
    EXECUTION_STATUSES,
    TEST_ARTIFACT_SUBTYPES,
    VERIFICATION_STATES,
)


def _non_empty_str(v: str) -> str:
    s = v.strip()
    if not s:
        msg = "must not be empty"
        raise ValueError(msg)
    return s


class EvidenceRefIn(BaseModel):
    """Structured evidence pointer (extensible)."""

    kind: str = Field(default="uri", max_length=64)
    ref: str = Field(..., max_length=4096)
    label: str | None = Field(default=None, max_length=512)
    extra: dict[str, Any] = Field(default_factory=dict)


class WritebackProvenanceIn(BaseModel):
    """Optional provenance override (API / services). Defaults applied in service layer."""

    origin_type: str | None = None
    origin_id: str | None = Field(default=None, max_length=512)
    verification_state: str | None = None


class WritebackCreateBase(BaseModel):
    model_version_id: uuid.UUID | None = None
    summary: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    related_document_id: uuid.UUID | None = None
    related_asset_id: uuid.UUID | None = None
    evidence_refs: list[EvidenceRefIn] = Field(default_factory=list)
    provenance: WritebackProvenanceIn | None = None


class FindingCreateIn(WritebackCreateBase):
    title: str
    details: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)


class RiskCreateIn(WritebackCreateBase):
    title: str
    details: str | None = None
    severity: str | None = Field(default=None, max_length=64)
    likelihood: str | None = Field(default=None, max_length=64)

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)


class TestArtifactCreateIn(WritebackCreateBase):
    artifact_subtype: str
    title: str
    content: str | None = None
    related_risk_id: uuid.UUID | None = None

    @field_validator("artifact_subtype", mode="before")
    @classmethod
    def _subtype(cls, v: str) -> str:
        s = _non_empty_str(v)
        if s not in TEST_ARTIFACT_SUBTYPES:
            msg = f"invalid artifact_subtype: {s!r}"
            raise ValueError(msg)
        return s

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)


class ExecutionResultCreateIn(WritebackCreateBase):
    title: str
    status: str
    details: str | None = None
    related_test_artifact_id: uuid.UUID | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v: str) -> str:
        s = _non_empty_str(v)
        if s not in EXECUTION_STATUSES:
            msg = f"invalid execution status: {s!r}"
            raise ValueError(msg)
        return s


class EvidenceNoteCreateIn(WritebackCreateBase):
    title: str
    details: str | None = None
    citation: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)


class ContradictionCreateIn(WritebackCreateBase):
    title: str
    details: str | None = None
    conflicting_reference_a: dict[str, Any] = Field(default_factory=dict)
    conflicting_reference_b: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v: str) -> str:
        return _non_empty_str(v)


class VerificationPatchIn(BaseModel):
    verification_state: str
    review_note: str | None = Field(default=None, max_length=8000)

    @field_validator("verification_state", mode="before")
    @classmethod
    def _vs(cls, v: str) -> str:
        s = _non_empty_str(v)
        if s not in VERIFICATION_STATES:
            msg = f"invalid verification_state: {s!r}"
            raise ValueError(msg)
        return s


class WritebackOut(BaseModel):
    id: uuid.UUID
    knowledge_model_id: uuid.UUID
    knowledge_model_version_id: uuid.UUID | None
    artifact_kind: str
    title: str
    summary: str | None
    payload_json: dict[str, Any]
    origin_type: str
    origin_id: str | None
    verification_state: str
    confidence_score: float | None
    reviewer_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    supersedes_id: uuid.UUID | None
    related_document_id: uuid.UUID | None
    related_asset_id: uuid.UUID | None
    related_writeback_id: uuid.UUID | None
    related_entity_id: uuid.UUID | None
    related_claim_id: uuid.UUID | None
    evidence_refs_json: list[Any] | dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row: Any) -> WritebackOut:
        ev = row.evidence_refs_json
        if not isinstance(ev, list):
            ev = []
        conf = row.confidence_score
        return cls(
            id=row.id,
            knowledge_model_id=row.knowledge_model_id,
            knowledge_model_version_id=row.knowledge_model_version_id,
            artifact_kind=row.artifact_kind,
            title=row.title,
            summary=row.summary,
            payload_json=dict(row.payload_json or {}),
            origin_type=row.origin_type,
            origin_id=row.origin_id,
            verification_state=row.verification_state,
            confidence_score=float(conf) if conf is not None else None,
            reviewer_id=row.reviewer_id,
            reviewed_at=row.reviewed_at,
            review_note=row.review_note,
            supersedes_id=row.supersedes_id,
            related_document_id=row.related_document_id,
            related_asset_id=row.related_asset_id,
            related_writeback_id=row.related_writeback_id,
            related_entity_id=row.related_entity_id,
            related_claim_id=row.related_claim_id,
            evidence_refs_json=ev,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class WritebackListResponse(BaseModel):
    items: list[WritebackOut]
    knowledge_model_id: uuid.UUID
    limit: int
    offset: int


class ModelActivityItemOut(BaseModel):
    id: str
    occurred_at: datetime
    event_type: str
    title: str
    summary: str | None = None
    knowledge_model_version_id: uuid.UUID | None = None
    artifact_kind: str | None = None
    artifact_id: uuid.UUID | None = None
    verification_state: str | None = None
    origin_type: str | None = None
    origin_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ModelActivityResponse(BaseModel):
    items: list[ModelActivityItemOut]
    knowledge_model_id: uuid.UUID
