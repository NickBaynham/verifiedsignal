"""MCP tools — callable operations over canonical knowledge models."""

from __future__ import annotations

from typing import Any

from mcp_server.adapters.verifiedsignal_client import VerifiedSignalAPIError
from mcp_server.runtime import get_adapter, mcp


def _tool_error(e: Exception) -> dict[str, Any]:
    if isinstance(e, VerifiedSignalAPIError):
        return {"ok": False, "error": str(e), "status_code": e.status_code}
    return {"ok": False, "error": str(e)}


@mcp.tool()
def list_collections() -> dict[str, Any]:
    """List VerifiedSignal collections available to the current user."""
    try:
        return {"ok": True, "data": get_adapter().list_collections()}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def list_models(collection_id: str) -> dict[str, Any]:
    """List knowledge models in a collection."""
    try:
        return {"ok": True, "data": get_adapter().list_collection_models(collection_id)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def get_model(model_id: str) -> dict[str, Any]:
    """Get knowledge model metadata and latest version summary (from model detail)."""
    try:
        return {"ok": True, "data": get_adapter().get_model(model_id)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def get_model_version(model_id: str, version_id: str | None = None) -> dict[str, Any]:
    """
    Get a model version. If version_id is omitted, uses the latest version by version_number.
    """
    try:
        ad = get_adapter()
        vid = version_id or ad.get_latest_version_id(model_id)
        if not vid:
            return {"ok": False, "error": "No versions for this model."}
        return {"ok": True, "data": ad.get_model_version(model_id, vid)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def get_model_assets(model_id: str, version_id: str | None = None) -> dict[str, Any]:
    """List documents/assets for a model version (latest if version_id omitted)."""
    try:
        ad = get_adapter()
        vid = version_id or ad.get_latest_version_id(model_id)
        if not vid:
            return {"ok": False, "error": "No versions for this model."}
        return {"ok": True, "data": ad.get_model_assets(model_id, vid)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def get_model_summary(model_id: str, version_id: str | None = None) -> dict[str, Any]:
    """Return canonical summary_json for the version (latest if version_id omitted)."""
    try:
        return {
            "ok": True,
            "data": get_adapter().get_model_summary(model_id, version_id=version_id),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def search_model(model_id: str, query: str, version_id: str | None = None) -> dict[str, Any]:
    """
    V1 placeholder search: substring match over summary_json and asset titles/filenames.
    Replace with dedicated model-aware retrieval when the backend supports it.
    """
    try:
        return {
            "ok": True,
            "data": get_adapter().search_model_placeholder(
                model_id, query, version_id=version_id
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def compare_model_versions(
    model_id: str,
    left_version_id: str,
    right_version_id: str,
) -> dict[str, Any]:
    """Compare two versions: summary_json keys + included document id sets (structural)."""
    try:
        return {
            "ok": True,
            "data": get_adapter().compare_model_versions(
                model_id, left_version_id, right_version_id
            ),
        }
    except Exception as e:
        return _tool_error(e)
