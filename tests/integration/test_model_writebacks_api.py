"""Integration: model write-back APIs (Postgres migration 007)."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_writebacks_create_list_verify_activity(intake_api_client) -> None:
    lst = intake_api_client.get("/api/v1/collections").json()
    inbox = next(c for c in lst["collections"] if c["slug"] == "default-inbox")
    cid = inbox["id"]

    up = intake_api_client.post(
        "/api/v1/documents",
        files={"file": ("wb_doc.txt", b"writeback scope", "text/plain")},
        data={"collection_id": cid},
    )
    assert up.status_code == 200, up.text
    did = up.json()["document_id"]

    create = intake_api_client.post(
        f"/api/v1/collections/{cid}/models",
        json={
            "name": "WB Model",
            "model_type": "summary",
            "selected_document_ids": [did],
        },
    )
    assert create.status_code == 201, create.text
    mid = create.json()["knowledge_model"]["id"]
    vid = create.json()["version"]["id"]

    empty = intake_api_client.get(f"/api/v1/models/{mid}/writebacks")
    assert empty.status_code == 200
    assert empty.json()["items"] == []

    f = intake_api_client.post(
        f"/api/v1/models/{mid}/writebacks/findings",
        json={"title": "Race in settlement", "details": "Observed under concurrent load"},
    )
    assert f.status_code == 201, f.text
    fj = f.json()
    assert fj["artifact_kind"] == "finding"
    assert fj["verification_state"] == "proposed"
    wid = fj["id"]

    listed = intake_api_client.get(
        f"/api/v1/models/{mid}/writebacks",
        params={"artifact_kind": "finding"},
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    one = intake_api_client.get(f"/api/v1/models/{mid}/writebacks/{wid}")
    assert one.status_code == 200
    assert one.json()["title"] == "Race in settlement"

    patch = intake_api_client.patch(
        f"/api/v1/models/{mid}/writebacks/{wid}/verification",
        json={"verification_state": "accepted", "review_note": "lgtm"},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["verification_state"] == "accepted"

    act = intake_api_client.get(f"/api/v1/models/{mid}/activity")
    assert act.status_code == 200
    types = {x["event_type"] for x in act.json()["items"]}
    assert "writeback_created" in types
    assert "model_created" in types

    risk = intake_api_client.post(
        f"/api/v1/models/{mid}/writebacks/risks",
        json={
            "title": "Webhook replay",
            "severity": "high",
            "model_version_id": vid,
            "related_document_id": did,
        },
    )
    assert risk.status_code == 201, risk.text

    bad_ver = intake_api_client.patch(
        f"/api/v1/models/{mid}/writebacks/{wid}/verification",
        json={"verification_state": "rejected"},
    )
    assert bad_ver.status_code == 400
