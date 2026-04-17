"""MCP resources — read-only canonical model context (verifiedsignal:// URIs)."""

from __future__ import annotations

import json

from mcp_server.adapters.models_adapter import format_json_for_mcp
from mcp_server.adapters.verifiedsignal_client import VerifiedSignalAPIError
from mcp_server.runtime import get_adapter, mcp


def _err(e: VerifiedSignalAPIError) -> str:
    return json.dumps({"error": str(e), "status_code": e.status_code}, indent=2)


@mcp.resource("verifiedsignal://collections")
def resource_collections() -> str:
    """List all collections the authenticated user can access."""
    try:
        return format_json_for_mcp(get_adapter().list_collections())
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://collections/{collection_id}")
def resource_collection(collection_id: str) -> str:
    """Collection workspace summary."""
    try:
        return format_json_for_mcp(get_adapter().get_collection(collection_id))
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://collections/{collection_id}/models")
def resource_collection_models(collection_id: str) -> str:
    """Knowledge models in a collection."""
    try:
        return format_json_for_mcp(get_adapter().list_collection_models(collection_id))
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://models/{model_id}")
def resource_model(model_id: str) -> str:
    """Knowledge model overview + latest summary_json on detail."""
    try:
        return format_json_for_mcp(get_adapter().get_model(model_id))
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://models/{model_id}/latest")
def resource_model_latest(model_id: str) -> str:
    """Latest version row (by version_number) + summary."""
    try:
        ad = get_adapter()
        vid = ad.get_latest_version_id(model_id)
        if not vid:
            return format_json_for_mcp({"model_id": model_id, "error": "no_versions"})
        ver = ad.get_model_version(model_id, vid)
        summary = ad.get_model_summary(model_id, version_id=vid)
        return format_json_for_mcp({"model_id": model_id, "version": ver, "summary": summary})
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://models/{model_id}/versions/{version_id}")
def resource_model_version(model_id: str, version_id: str) -> str:
    """Single model version (canonical snapshot + build_profile_json)."""
    try:
        return format_json_for_mcp(get_adapter().get_model_version(model_id, version_id))
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://models/{model_id}/versions/{version_id}/assets")
def resource_model_version_assets(model_id: str, version_id: str) -> str:
    """Documents/assets included in this version."""
    try:
        return format_json_for_mcp(get_adapter().get_model_assets(model_id, version_id))
    except VerifiedSignalAPIError as e:
        return _err(e)


@mcp.resource("verifiedsignal://models/{model_id}/versions/{version_id}/summary")
def resource_model_version_summary(model_id: str, version_id: str) -> str:
    """summary_json for this version (canonical build output)."""
    try:
        return format_json_for_mcp(get_adapter().get_model_summary(model_id, version_id=version_id))
    except VerifiedSignalAPIError as e:
        return _err(e)
