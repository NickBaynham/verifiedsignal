"""Model write-back REST API (canonical Postgres artifacts)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.dependencies import get_current_user
from app.schemas.model_writeback import (
    ContradictionCreateIn,
    EvidenceNoteCreateIn,
    ExecutionResultCreateIn,
    FindingCreateIn,
    ModelActivityResponse,
    RiskCreateIn,
    TestArtifactCreateIn,
    VerificationPatchIn,
    WritebackListResponse,
    WritebackOut,
)
from app.services import model_writeback_service as wb_svc

router = APIRouter(prefix="/models", tags=["model-writebacks"])


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.post("/{model_id}/writebacks/findings", response_model=WritebackOut, status_code=201)
def post_finding(
    model_id: uuid.UUID,
    body: FindingCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_finding(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.post("/{model_id}/writebacks/risks", response_model=WritebackOut, status_code=201)
def post_risk(
    model_id: uuid.UUID,
    body: RiskCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_risk(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.post("/{model_id}/writebacks/test-artifacts", response_model=WritebackOut, status_code=201)
def post_test_artifact(
    model_id: uuid.UUID,
    body: TestArtifactCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_test_artifact(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.post(
    "/{model_id}/writebacks/execution-results",
    response_model=WritebackOut,
    status_code=201,
)
def post_execution_result(
    model_id: uuid.UUID,
    body: ExecutionResultCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_execution_result(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.post("/{model_id}/writebacks/evidence-notes", response_model=WritebackOut, status_code=201)
def post_evidence_note(
    model_id: uuid.UUID,
    body: EvidenceNoteCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_evidence_note(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.post("/{model_id}/writebacks/contradictions", response_model=WritebackOut, status_code=201)
def post_contradiction(
    model_id: uuid.UUID,
    body: ContradictionCreateIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.create_contradiction(db, auth_sub=user_id, model_id=model_id, body=body)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.get("/{model_id}/writebacks", response_model=WritebackListResponse)
def get_writebacks(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    artifact_kind: str | None = Query(default=None),
    verification_state: str | None = Query(default=None),
    version_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> WritebackListResponse:
    try:
        out = wb_svc.list_writebacks(
            db,
            auth_sub=user_id,
            model_id=model_id,
            artifact_kind=artifact_kind,
            verification_state=verification_state,
            version_id=version_id,
            limit=limit,
            offset=offset,
        )
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out


@router.get("/{model_id}/writebacks/{writeback_id}", response_model=WritebackOut)
def get_writeback(
    model_id: uuid.UUID,
    writeback_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.get_writeback(
            db,
            auth_sub=user_id,
            model_id=model_id,
            writeback_id=writeback_id,
        )
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    if out is None:
        raise HTTPException(status_code=404, detail="Model or write-back not found")
    return out


@router.patch(
    "/{model_id}/writebacks/{writeback_id}/verification",
    response_model=WritebackOut,
)
def patch_writeback_verification(
    model_id: uuid.UUID,
    writeback_id: uuid.UUID,
    body: VerificationPatchIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> WritebackOut:
    try:
        out = wb_svc.patch_verification(
            db,
            auth_sub=user_id,
            model_id=model_id,
            writeback_id=writeback_id,
            body=body,
        )
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    except ValueError as e:
        raise _bad_request(e) from e
    if out is None:
        raise HTTPException(status_code=404, detail="Model or write-back not found")
    return out


@router.get("/{model_id}/activity", response_model=ModelActivityResponse)
def get_model_activity(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> ModelActivityResponse:
    try:
        out = wb_svc.list_model_activity(db, auth_sub=user_id, model_id=model_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Model not found") from None
    if out is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return out
