# Tests

Pytest is organized by **markers** (see `pyproject.toml`):

| Marker | Scope | Requirements |
|--------|--------|----------------|
| **`unit`** | CLI, package metadata, migrations on disk, worker pipeline sim, event hub, document queue | None |
| **`integration`** | Postgres schema **or** FastAPI routes (with stubbed DB health + fake queue via `api_client`) | Schema tests: **`DATABASE_URL`** + applied migrations. API route tests: none (fixture stubs infra). |
| **`e2e`** | `docker compose config` + ASGI smoke (`test_api_http`) | **`docker`** on `PATH` for compose test only |
| **`api`** | ASGI smoke (`TestClient`, multi-route) | None |

## Commands

```bash
make test                 # full pytest (skips only what markers/env exclude)
make test-unit
make test-integration
make test-e2e
make test-api
```

## Integration tests and Postgres

Schema integration tests (`test_schema_*.py`) connect with **`psycopg`** using **`DATABASE_URL`**. They **do not** apply migrations; your pipeline (or you locally) must run the SQL in `db/migrations/` first.

API integration tests (`test_api_routes.py`) use the shared **`api_client`** fixture: fake ARQ queue (`USE_FAKE_QUEUE=true`), patched DB health, and cleaned global state after each test.

## Integration tests and `api_client`

Defined in **`tests/conftest.py`**. Patches **`app.api.routes.health.check_database_connection`** so `/health` reports **ok** without a live Postgres (route modules bind their own reference to that function).

## CI

GitHub Actions runs **`pdm run pytest`** (all markers) plus Ruff on **`src`**, **`tests`**, **`app`**, and **`worker`**.
