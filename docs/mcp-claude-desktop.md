# VerifiedSignal MCP server (Claude Desktop)

Local [**Model Context Protocol**](https://modelcontextprotocol.io/) server that exposes **canonical knowledge models** from VerifiedSignal (Postgres-backed versions, `summary_json`, included documents). It talks to the **same REST API** as the web UI (`/api/v1`), not to OpenSearch directly, so model context stays aligned with the system of record.

## Prerequisites

- Python **3.11+** and project deps installed (`pdm install` or equivalent).
- VerifiedSignal **API running** and reachable (e.g. Docker `app` on `http://127.0.0.1:8000`).
- A valid **Bearer JWT** for your user (`VERIFIEDSIGNAL_ACCESS_TOKEN`). Use the same access token the SPA stores after login (e.g. from browser devtools / session), or obtain it via your normal auth flow.

## Install

From the repository root:

```bash
pdm install
```

The `mcp` package is declared in `pyproject.toml`.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VERIFIEDSIGNAL_API_URL` | No | API origin, default `http://127.0.0.1:8000` |
| `VERIFIEDSIGNAL_ACCESS_TOKEN` | Yes | Bearer JWT for `/api/v1` |
| `VERIFIEDSIGNAL_LOG_LEVEL` | No | Default `WARNING` |

## Run (stdio)

```bash
cd /path/to/verifiedsignal
pdm run mcp-server
# or
pdm run python -m mcp_server.main
```

Run from the **repository root** so the `mcp_server` package resolves (`package-dir` is `src` for the main distro; this tree keeps `mcp_server` next to `app/`).

The process speaks **stdio** MCP — do not run it in an interactive terminal expecting logs; Claude Desktop spawns it as a subprocess.

## Claude Desktop configuration

Add a **local MCP server** entry (path depends on OS). Use the official Anthropic docs for the current file location; typically a JSON file such as `claude_desktop_config.json` with an `mcpServers` object.

Example (adjust paths and use your token source — **do not commit secrets**):

```json
{
  "mcpServers": {
    "verifiedsignal": {
      "command": "pdm",
      "args": ["run", "python", "-m", "mcp_server.main"],
      "cwd": "/absolute/path/to/verifiedsignal",
      "env": {
        "VERIFIEDSIGNAL_API_URL": "http://127.0.0.1:8000",
        "VERIFIEDSIGNAL_ACCESS_TOKEN": "YOUR_JWT_HERE",
        "VERIFIEDSIGNAL_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

If you prefer the project venv interpreter directly:

```json
{
  "mcpServers": {
    "verifiedsignal": {
      "command": "/absolute/path/to/verifiedsignal/.venv/bin/python",
      "args": ["-m", "mcp_server.main"],
      "cwd": "/absolute/path/to/verifiedsignal",
      "env": {
        "VERIFIEDSIGNAL_API_URL": "http://127.0.0.1:8000",
        "VERIFIEDSIGNAL_ACCESS_TOKEN": "YOUR_JWT_HERE"
      }
    }
  }
}
```

Restart Claude Desktop after editing config.

## What is exposed

### Resources (`verifiedsignal://…`)

FastMCP exposes **one static resource** (`verifiedsignal://collections`) plus **URI templates** for the paths below (same URIs when expanded).

| URI pattern | Content |
|-------------|---------|
| `verifiedsignal://collections` | `GET /api/v1/collections` |
| `verifiedsignal://collections/{collection_id}` | Collection summary |
| `verifiedsignal://collections/{collection_id}/models` | Models in collection |
| `verifiedsignal://models/{model_id}` | Model detail |
| `verifiedsignal://models/{model_id}/latest` | Latest version + summary |
| `verifiedsignal://models/{model_id}/versions/{version_id}` | Version row |
| `.../assets` | Included documents |
| `.../summary` | `summary_json` for the version |

### Tools

- `list_collections`
- `list_models` (`collection_id`)
- `get_model` (`model_id`)
- `get_model_version` (`model_id`, `version_id` optional)
- `get_model_assets` (`model_id`, `version_id` optional)
- `get_model_summary` (`model_id`, `version_id` optional)
- `search_model` (`model_id`, `query`, `version_id` optional) — **V1 placeholder** (substring over `summary_json` + asset titles)
- `compare_model_versions` (`model_id`, `left_version_id`, `right_version_id`)

No mutation / write-back tools in V1.

### Prompts

- `summarize_model`
- `analyze_model_for_risks`
- `design_tests_from_model`
- `explain_model_scope`

## Example questions (for Claude)

- “List my VerifiedSignal collections using the verifiedsignal MCP server.”
- “Summarize the latest version of model `{uuid}` with summarize_model / get_model_summary.”
- “Design tests from the Test Knowledge model `{uuid}` with a focus on refunds.”
- “Compare version 1 and version 2 of model `{uuid}` with compare_model_versions.”

## Troubleshooting

- **`Missing VERIFIEDSIGNAL_ACCESS_TOKEN`**: Export the variable or set it in the Claude MCP `env` block.
- **`401` / `API error`**: Token expired or wrong API URL; refresh login and update JWT.
- **`relation "knowledge_models" does not exist`**: Apply DB migration **006** (`make migrate-006`).
- **Server exits immediately**: Usually misconfigured `command`/`cwd`; run `pdm run python scripts/verify_mcp_smoke.py` from the repo root to verify registration.

## V1 limitations & future work

- **search_model** is a placeholder; replace with dedicated model-aware retrieval when the backend supports it.
- **Transport**: stdio only for local Claude Desktop; remote/streamable HTTP can be added later.
- **Auth**: long-lived token in env; future OAuth / rotating tokens can wrap the HTTP client.
- **Write-back** tools (risks, test artifacts) are intentionally out of scope until governed APIs exist.

## Smoke test

```bash
pdm run python scripts/verify_mcp_smoke.py
```
