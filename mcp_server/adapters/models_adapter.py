"""
Knowledge-model access layer — normalized dicts for MCP resources/tools.

Uses VerifiedSignalClient (HTTP). This keeps MCP decoupled from SQLAlchemy and
matches how remote MCP would call the same API later.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp_server.adapters.verifiedsignal_client import VerifiedSignalClient

log = logging.getLogger(__name__)


def _pick_latest_version_id(versions_payload: dict[str, Any]) -> str | None:
    items = versions_payload.get("items") or []
    if not items:
        return None
    sorted_items = sorted(items, key=lambda x: int(x.get("version_number") or 0), reverse=True)
    vid = sorted_items[0].get("id")
    return str(vid) if vid else None


class ModelsAdapter:
    """High-level operations for collections and knowledge models."""

    def __init__(self, client: VerifiedSignalClient) -> None:
        self._c = client

    def list_collections(self) -> dict[str, Any]:
        return self._c.list_collections()

    def get_collection(self, collection_id: str) -> dict[str, Any]:
        return self._c.get_collection(collection_id)

    def list_collection_models(self, collection_id: str) -> dict[str, Any]:
        return self._c.list_collection_models(collection_id)

    def get_model(self, model_id: str) -> dict[str, Any]:
        return self._c.get_model(model_id)

    def list_model_versions(self, model_id: str) -> dict[str, Any]:
        return self._c.list_model_versions(model_id)

    def get_model_version(self, model_id: str, version_id: str) -> dict[str, Any]:
        return self._c.get_model_version(model_id, version_id)

    def get_model_assets(self, model_id: str, version_id: str) -> dict[str, Any]:
        return self._c.get_model_version_assets(model_id, version_id)

    def get_latest_version_id(self, model_id: str) -> str | None:
        data = self._c.list_model_versions(model_id)
        return _pick_latest_version_id(data)

    def get_model_summary(
        self,
        model_id: str,
        *,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Return canonical summary for a version (from version row), or model detail's
        summary when pointing at latest.
        """
        vid = version_id or self.get_latest_version_id(model_id)
        if not vid:
            detail = self._c.get_model(model_id)
            return {
                "model_id": model_id,
                "version_id": None,
                "summary_json": detail.get("summary_json"),
                "source": "model_detail",
            }
        ver = self._c.get_model_version(model_id, vid)
        return {
            "model_id": model_id,
            "version_id": vid,
            "summary_json": ver.get("summary_json"),
            "build_status": ver.get("build_status"),
            "version_number": ver.get("version_number"),
            "source": "model_version",
        }

    def search_model_placeholder(
        self,
        model_id: str,
        query: str,
        *,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        """
        V1 placeholder: substring search over summary_json (canonical) + asset titles.

        No vector/chunk search — replace with dedicated model retrieval when available.
        """
        q = (query or "").strip().lower()
        vid = version_id or self.get_latest_version_id(model_id)
        if not vid:
            return {
                "model_id": model_id,
                "version_id": None,
                "matches": [],
                "note": "No versions found; search_model placeholder only.",
            }
        summary = self.get_model_summary(model_id, version_id=vid)
        assets = self._c.get_model_version_assets(model_id, vid)
        items = assets.get("items") or []

        matches: list[dict[str, Any]] = []
        blob = json.dumps(summary.get("summary_json") or {}, default=str).lower()
        if q and q in blob:
            matches.append(
                {"field": "summary_json", "snippet": "Query matched inside summary_json."},
            )
        for a in items:
            title = (a.get("title") or "") + " " + (a.get("original_filename") or "")
            if q and q in title.lower():
                matches.append(
                    {
                        "field": "asset_title",
                        "document_id": a.get("document_id"),
                        "title": a.get("title"),
                    }
                )
        return {
            "model_id": model_id,
            "version_id": vid,
            "query": query,
            "matches": matches,
            "implementation": "placeholder_substring_on_summary_and_asset_titles",
        }

    def compare_model_versions(
        self,
        model_id: str,
        left_version_id: str,
        right_version_id: str,
    ) -> dict[str, Any]:
        left = self._c.get_model_version(model_id, left_version_id)
        right = self._c.get_model_version(model_id, right_version_id)
        left_assets = self._c.get_model_version_assets(model_id, left_version_id)
        right_assets = self._c.get_model_version_assets(model_id, right_version_id)
        l_items = left_assets.get("items") or []
        r_items = right_assets.get("items") or []
        l_docs = {str(x.get("document_id")) for x in l_items if x.get("document_id")}
        r_docs = {str(x.get("document_id")) for x in r_items if x.get("document_id")}

        l_sum = left.get("summary_json")
        r_sum = right.get("summary_json")
        l_keys = set(l_sum.keys()) if isinstance(l_sum, dict) else set()
        r_keys = set(r_sum.keys()) if isinstance(r_sum, dict) else set()

        return {
            "model_id": model_id,
            "left": {
                "version_id": left_version_id,
                "version_number": left.get("version_number"),
                "build_status": left.get("build_status"),
            },
            "right": {
                "version_id": right_version_id,
                "version_number": right.get("version_number"),
                "build_status": right.get("build_status"),
            },
            "summary_json_keys_only_in_left": sorted(l_keys - r_keys),
            "summary_json_keys_only_in_right": sorted(r_keys - l_keys),
            "document_ids_only_in_left": sorted(l_docs - r_docs),
            "document_ids_only_in_right": sorted(r_docs - l_docs),
            "document_ids_in_both": sorted(l_docs & r_docs),
            "note": (
                "Structural diff only (keys + asset sets). "
                "Deeper semantic diff is future work."
            ),
        }

    @staticmethod
    def _agent_provenance(
        *,
        origin_id: str | None = None,
        verification_state: str = "proposed",
    ) -> dict[str, Any]:
        p: dict[str, Any] = {"origin_type": "agent", "verification_state": verification_state}
        if origin_id:
            p["origin_id"] = origin_id
        return p

    def list_writebacks(
        self,
        model_id: str,
        *,
        artifact_kind: str | None = None,
        verification_state: str | None = None,
        version_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if artifact_kind:
            params["artifact_kind"] = artifact_kind
        if verification_state:
            params["verification_state"] = verification_state
        if version_id:
            params["version_id"] = version_id
        return self._c.list_model_writebacks(model_id, params=params)

    def get_writeback(self, model_id: str, writeback_id: str) -> dict[str, Any]:
        return self._c.get_model_writeback(model_id, writeback_id)

    def list_model_activity(self, model_id: str) -> dict[str, Any]:
        return self._c.get_model_activity(model_id)

    def write_finding(
        self,
        model_id: str,
        title: str,
        *,
        model_version_id: str | None = None,
        summary: str | None = None,
        details: str | None = None,
        confidence_score: float | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if summary is not None:
            body["summary"] = summary
        if details is not None:
            body["details"] = details
        if confidence_score is not None:
            body["confidence_score"] = confidence_score
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_finding(model_id, body)

    def write_risk(
        self,
        model_id: str,
        title: str,
        *,
        model_version_id: str | None = None,
        details: str | None = None,
        severity: str | None = None,
        likelihood: str | None = None,
        summary: str | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if summary is not None:
            body["summary"] = summary
        if details is not None:
            body["details"] = details
        if severity:
            body["severity"] = severity
        if likelihood:
            body["likelihood"] = likelihood
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_risk(model_id, body)

    def write_test_artifact(
        self,
        model_id: str,
        artifact_subtype: str,
        title: str,
        *,
        model_version_id: str | None = None,
        content: str | None = None,
        summary: str | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        related_risk_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "artifact_subtype": artifact_subtype,
            "title": title,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if content is not None:
            body["content"] = content
        if summary is not None:
            body["summary"] = summary
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if related_risk_id:
            body["related_risk_id"] = related_risk_id
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_test_artifact(model_id, body)

    def write_execution_result(
        self,
        model_id: str,
        title: str,
        status: str,
        *,
        model_version_id: str | None = None,
        summary: str | None = None,
        details: str | None = None,
        related_test_artifact_id: str | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "status": status,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if summary is not None:
            body["summary"] = summary
        if details is not None:
            body["details"] = details
        if related_test_artifact_id:
            body["related_test_artifact_id"] = related_test_artifact_id
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_execution_result(model_id, body)

    def write_evidence_note(
        self,
        model_id: str,
        title: str,
        *,
        model_version_id: str | None = None,
        details: str | None = None,
        summary: str | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        citation: dict[str, Any] | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if summary is not None:
            body["summary"] = summary
        if details is not None:
            body["details"] = details
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if citation:
            body["citation"] = citation
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_evidence_note(model_id, body)

    def write_contradiction(
        self,
        model_id: str,
        title: str,
        *,
        model_version_id: str | None = None,
        details: str | None = None,
        summary: str | None = None,
        related_document_id: str | None = None,
        related_asset_id: str | None = None,
        conflicting_reference_a: dict[str, Any] | None = None,
        conflicting_reference_b: dict[str, Any] | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        agent_origin_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "provenance": self._agent_provenance(origin_id=agent_origin_id),
        }
        if model_version_id:
            body["model_version_id"] = model_version_id
        if summary is not None:
            body["summary"] = summary
        if details is not None:
            body["details"] = details
        if related_document_id:
            body["related_document_id"] = related_document_id
        if related_asset_id:
            body["related_asset_id"] = related_asset_id
        if conflicting_reference_a:
            body["conflicting_reference_a"] = conflicting_reference_a
        if conflicting_reference_b:
            body["conflicting_reference_b"] = conflicting_reference_b
        if evidence_refs:
            body["evidence_refs"] = evidence_refs
        return self._c.post_writeback_contradiction(model_id, body)


def format_json_for_mcp(data: Any) -> str:
    """Claude-friendly pretty JSON."""
    return json.dumps(data, indent=2, default=str, sort_keys=True)
