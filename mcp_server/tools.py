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


@mcp.tool()
def list_writebacks(
    model_id: str,
    artifact_kind: str | None = None,
    verification_state: str | None = None,
    version_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List write-back artifacts for a model (filter by kind, verification, version)."""
    try:
        return {
            "ok": True,
            "data": get_adapter().list_writebacks(
                model_id,
                artifact_kind=artifact_kind,
                verification_state=verification_state,
                version_id=version_id,
                limit=limit,
                offset=offset,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def get_writeback(model_id: str, writeback_id: str) -> dict[str, Any]:
    """Fetch a single write-back artifact."""
    try:
        return {"ok": True, "data": get_adapter().get_writeback(model_id, writeback_id)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def list_model_activity(model_id: str) -> dict[str, Any]:
    """Unified timeline: model creation, versions, builds, write-backs, verification events."""
    try:
        return {"ok": True, "data": get_adapter().list_model_activity(model_id)}
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_finding(
    model_id: str,
    title: str,
    model_version_id: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    confidence_score: float | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Add a finding (provenance=agent, verification=proposed unless overridden server-side)."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_finding(
                model_id,
                title,
                model_version_id=model_version_id,
                summary=summary,
                details=details,
                confidence_score=confidence_score,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_risk(
    model_id: str,
    title: str,
    model_version_id: str | None = None,
    details: str | None = None,
    severity: str | None = None,
    likelihood: str | None = None,
    summary: str | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Record a risk on the model."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_risk(
                model_id,
                title,
                model_version_id=model_version_id,
                details=details,
                severity=severity,
                likelihood=likelihood,
                summary=summary,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_test_artifact(
    model_id: str,
    artifact_subtype: str,
    title: str,
    model_version_id: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    related_risk_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Attach a test scenario, case, script reference, or coverage note."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_test_artifact(
                model_id,
                artifact_subtype,
                title,
                model_version_id=model_version_id,
                content=content,
                summary=summary,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                related_risk_id=related_risk_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_execution_result(
    model_id: str,
    title: str,
    status: str,
    model_version_id: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    related_test_artifact_id: str | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Record a test execution outcome (passed/failed/skipped/error/running/unknown)."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_execution_result(
                model_id,
                title,
                status,
                model_version_id=model_version_id,
                summary=summary,
                details=details,
                related_test_artifact_id=related_test_artifact_id,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_evidence_note(
    model_id: str,
    title: str,
    model_version_id: str | None = None,
    details: str | None = None,
    summary: str | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Add supplemental evidence or citation context."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_evidence_note(
                model_id,
                title,
                model_version_id=model_version_id,
                details=details,
                summary=summary,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)


@mcp.tool()
def write_contradiction(
    model_id: str,
    title: str,
    model_version_id: str | None = None,
    details: str | None = None,
    summary: str | None = None,
    related_document_id: str | None = None,
    related_asset_id: str | None = None,
    agent_origin_id: str | None = None,
) -> dict[str, Any]:
    """Record a contradiction between sources or behaviors."""
    try:
        return {
            "ok": True,
            "data": get_adapter().write_contradiction(
                model_id,
                title,
                model_version_id=model_version_id,
                details=details,
                summary=summary,
                related_document_id=related_document_id,
                related_asset_id=related_asset_id,
                agent_origin_id=agent_origin_id,
            ),
        }
    except Exception as e:
        return _tool_error(e)
