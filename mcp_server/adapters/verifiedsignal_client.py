"""HTTP client for VerifiedSignal /api/v1 (Bearer auth)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


class VerifiedSignalAPIError(Exception):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class VerifiedSignalClient:
    """Thin synchronous httpx wrapper for VerifiedSignal REST API."""

    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        timeout_seconds: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = access_token.strip()
        kwargs: dict = {
            "base_url": self._base,
            "timeout": timeout_seconds,
            "headers": {
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
            },
        }
        if transport is not None:
            kwargs["transport"] = transport
        self._client = httpx.Client(**kwargs)

    def close(self) -> None:
        self._client.close()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Perform request; return parsed JSON or None for 204."""
        url = path if path.startswith("/") else f"/{path}"
        log.debug("vs_api %s %s", method, url)
        try:
            r = self._client.request(method, url, params=params, json=json_body)
        except httpx.RequestError as e:
            raise VerifiedSignalAPIError(f"HTTP request failed: {e}") from e

        if r.status_code == 204:
            return None

        if r.status_code >= 400:
            body_preview = (r.text or "")[:2000]
            raise VerifiedSignalAPIError(
                f"API error {r.status_code}: {body_preview}",
                status_code=r.status_code,
                body=r.text,
            )

        if not r.content:
            return None
        return r.json()

    def list_collections(self) -> dict[str, Any]:
        return self.request_json("GET", "/api/v1/collections")

    def get_collection(self, collection_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/api/v1/collections/{collection_id}")

    def list_collection_models(self, collection_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/api/v1/collections/{collection_id}/models")

    def get_model(self, model_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/api/v1/models/{model_id}")

    def list_model_versions(self, model_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/api/v1/models/{model_id}/versions")

    def get_model_version(self, model_id: str, version_id: str) -> dict[str, Any]:
        return self.request_json(
            "GET",
            f"/api/v1/models/{model_id}/versions/{version_id}",
        )

    def get_model_version_assets(self, model_id: str, version_id: str) -> dict[str, Any]:
        return self.request_json(
            "GET",
            f"/api/v1/models/{model_id}/versions/{version_id}/assets",
        )

    def list_model_writebacks(
        self,
        model_id: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request_json(
            "GET",
            f"/api/v1/models/{model_id}/writebacks",
            params=params,
        )

    def get_model_writeback(self, model_id: str, writeback_id: str) -> dict[str, Any]:
        return self.request_json(
            "GET",
            f"/api/v1/models/{model_id}/writebacks/{writeback_id}",
        )

    def get_model_activity(self, model_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/api/v1/models/{model_id}/activity")

    def post_writeback_finding(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/findings",
            json_body=body,
        )

    def post_writeback_risk(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/risks",
            json_body=body,
        )

    def post_writeback_test_artifact(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/test-artifacts",
            json_body=body,
        )

    def post_writeback_execution_result(
        self, model_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/execution-results",
            json_body=body,
        )

    def post_writeback_evidence_note(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/evidence-notes",
            json_body=body,
        )

    def post_writeback_contradiction(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json(
            "POST",
            f"/api/v1/models/{model_id}/writebacks/contradictions",
            json_body=body,
        )
