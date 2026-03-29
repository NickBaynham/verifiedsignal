"""Resolve which collections a caller may read (documents in those collections are visible)."""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings


def resolve_accessible_collection_ids(
    session: Session,
    auth_sub: str,
    settings: Settings,
) -> list[uuid.UUID]:
    """
    JWT `sub` is matched to `users.id` (UUID) or `users.external_sub` (string).

    If a row exists, return collection ids for orgs that user belongs to.

    If no user row exists (typical local dev before user sync), fall back to
    `VERIFIEDSIGNAL_DEFAULT_COLLECTION_ID` only so intake + listing work without seeding users.
    """
    uid: uuid.UUID | None = None
    try:
        uid = uuid.UUID(auth_sub.strip())
    except ValueError:
        pass

    row = None
    if uid is not None:
        row = session.execute(
            text("SELECT id FROM users WHERE id = :uid OR external_sub = :sub"),
            {"uid": uid, "sub": auth_sub.strip()},
        ).fetchone()
    else:
        row = session.execute(
            text("SELECT id FROM users WHERE external_sub = :sub"),
            {"sub": auth_sub.strip()},
        ).fetchone()

    if row is None:
        if settings.default_collection_id is not None:
            return [settings.default_collection_id]
        return []

    user_id = row[0]
    cols = session.execute(
        text(
            """
            SELECT c.id FROM collections c
            INNER JOIN organization_members om ON c.organization_id = om.organization_id
            WHERE om.user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchall()
    return [r[0] for r in cols]
