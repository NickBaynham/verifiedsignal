# Model write-back (V1)

VerifiedSignal stores **canonical write-back artifacts** in PostgreSQL on top of **versioned knowledge models**. Search and vector indexes remain **derived** and rebuildable; write-back does not require re-indexing for correctness.

## Artifact kinds

| Kind | Purpose |
|------|---------|
| `finding` | Discovered issue, ambiguity, gap |
| `risk` | Risk statement (optional severity/likelihood in `payload_json`) |
| `test_artifact` | Scenario, case, script ref, coverage note (`artifact_subtype` in payload) |
| `execution_result` | Test run outcome (`execution_status` in payload) |
| `evidence_note` | Citation / supplemental evidence |
| `contradiction` | Conflicting references (`conflicting_reference_a` / `_b` in payload) |

## Schema (migration **007**)

Single table **`model_writeback_artifacts`** plus audit **`model_writeback_events`**. Common columns include `knowledge_model_id`, optional `knowledge_model_version_id`, `title`, `summary`, `payload_json`, `origin_type`, `origin_id`, `verification_state`, `confidence_score`, reviewer fields, linkage to documents/assets/other artifacts, and `evidence_refs_json`.

**Trade-off:** one generalized table avoids six parallel DDLs and keeps indexes uniform; type-specific fields live in `payload_json` with Pydantic validation at the API boundary.

## Provenance (`origin_type`)

- `human` — UI or API acting as the logged-in user (default for browser-created rows).
- `agent` — MCP / autonomous agent (default for MCP write tools).
- `imported_system` — External system feed.
- `runtime_evidence` — Operational or automated evidence path.
- `internal_service` — Internal automation (e.g. ingestion helpers).

## Verification (`verification_state`)

- `proposed` — Default for human and agent contributions until reviewed.
- `accepted` / `rejected` — Review outcome.
- `auto_ingested` — Used for trusted runtime/internal paths (e.g. `writeback_ingestion.record_runtime_evidence`).
- `superseded` — Replaced by a newer artifact (optional `supersedes_id`).

Transitions are enforced in `app/services/model_writeback_governance.py`.

## HTTP API (`/api/v1`)

| Method | Path |
|--------|------|
| POST | `/models/{id}/writebacks/findings` |
| POST | `/models/{id}/writebacks/risks` |
| POST | `/models/{id}/writebacks/test-artifacts` |
| POST | `/models/{id}/writebacks/execution-results` |
| POST | `/models/{id}/writebacks/evidence-notes` |
| POST | `/models/{id}/writebacks/contradictions` |
| GET | `/models/{id}/writebacks` (query: `artifact_kind`, `verification_state`, `version_id`, `limit`, `offset`) |
| GET | `/models/{id}/writebacks/{writeback_id}` |
| PATCH | `/models/{id}/writebacks/{writeback_id}/verification` |
| GET | `/models/{id}/activity` |

## MCP tools

Read: `list_writebacks`, `get_writeback`, `list_model_activity`.  
Write: `write_finding`, `write_risk`, `write_test_artifact`, `write_execution_result`, `write_evidence_note`, `write_contradiction` — all default to **`origin_type=agent`** and **`verification_state=proposed`**.

## Internal ingestion (Phase 7)

`app/services/writeback_ingestion.py` exposes:

- `record_runtime_evidence` — `runtime_evidence` + `auto_ingested`
- `record_agent_observation` — agent finding
- `record_execution_outcome` — `internal_service` + `auto_ingested`
- `create_imported_finding` — `imported_system` + `proposed`

Future browser/document agents should call these (or the REST API) rather than writing SQL directly.

## UI

Model detail (`/models/:id`): **Write-back** tab (list, filters, accept/reject proposed items, add finding) and **Activity** tab (timeline).

## Apply migration

```bash
make migrate-007
# or full migrate on empty DB
make migrate
```
