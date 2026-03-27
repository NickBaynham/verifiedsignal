"""Document submission (enqueue background processing)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.placeholder import get_optional_user
from app.schemas.document import DocumentCreate, DocumentSubmitResponse
from app.services.document_service import submit_document_for_processing

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentSubmitResponse)
async def create_document(
    body: DocumentCreate,
    _user: dict = Depends(get_optional_user),
) -> DocumentSubmitResponse:
    """
    Accept a document description and enqueue `process_document` on the worker queue.

    Auth is a placeholder dependency today; later enforce org/collection scope here.
    """
    _ = _user
    result = await submit_document_for_processing(
        title=body.title,
        source_uri=body.source_uri,
        metadata=body.metadata,
    )
    return DocumentSubmitResponse(**result)
