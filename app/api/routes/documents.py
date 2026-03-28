"""Document intake: multipart upload, canonical Postgres row, storage, enqueue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_object_storage_dep
from app.auth.dependencies import get_current_user
from app.schemas.document import IntakeResponse
from app.services.document_service import run_file_intake
from app.services.exceptions import IntakeValidationError, StorageUploadError
from app.services.storage_service import ObjectStorage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(user_id: str = Depends(get_current_user)) -> dict:
    """List documents (stub; requires valid access token)."""
    return {"items": [], "user_id": user_id}


@router.post("", response_model=IntakeResponse)
def upload_document(
    file: UploadFile = File(..., description="Raw file bytes for intake"),
    collection_id: str | None = Form(
        default=None,
        description=(
            "Target collection UUID; "
            "defaults to VERIFIEDSIGNAL_DEFAULT_COLLECTION_ID when omitted"
        ),
    ),
    title: str | None = Form(
        default=None,
        description="Optional display title (defaults to filename)",
    ),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage_dep),
    _user_id: str = Depends(get_current_user),
) -> IntakeResponse:
    """
    Phase 1 intake: validate, insert canonical `documents` row (`created`), upload to S3/MinIO,
    finalize to `queued` with `document_sources`, enqueue `process_document`.

    Sync handler so `asyncio.run` inside storage/queue helpers is safe (runs on a worker thread).
    """
    _ = _user_id
    raw = file.file.read()
    try:
        payload = run_file_intake(
            db,
            file_bytes=raw,
            original_filename=file.filename or "upload",
            content_type=file.content_type,
            title=title,
            collection_id_param=collection_id,
            storage=storage,
        )
    except IntakeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except StorageUploadError as e:
        did = e.document_id
        raise HTTPException(
            status_code=502,
            detail={
                "message": "object storage upload failed",
                "error": str(e),
                "document_id": str(did) if did is not None else None,
            },
        ) from e

    return IntakeResponse(**payload)
