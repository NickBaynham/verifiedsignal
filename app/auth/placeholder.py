"""
Placeholder auth: wire JWT / API keys / OIDC here.

Routes can depend on `get_optional_user` until real enforcement exists.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Header


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """
    Returns a minimal principal. When `authorization` is absent, the subject is anonymous.
    """
    return {
        "sub": None,
        "anonymous": authorization is None,
        "authorization_present": authorization is not None,
    }
