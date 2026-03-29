"""Domain errors for intake and storage."""

from __future__ import annotations

import uuid


class IntakeValidationError(ValueError):
    """Invalid client input (filename, size, collection, etc.)."""


class StorageUploadError(Exception):
    """Object storage upload failed after canonical metadata may exist."""

    def __init__(self, message: str, *, document_id: uuid.UUID | None = None) -> None:
        super().__init__(message)
        self.document_id: uuid.UUID | None = document_id
