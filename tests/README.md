# Tests

Pytest is organized by **markers** (see `pyproject.toml`):

| Marker | Scope | Requirements |
|--------|--------|----------------|
| **`unit`** | CLI, package metadata, migration files on disk | None |
| **`integration`** | Postgres schema metadata, FKs, CHECKs, unique partial index | **`DATABASE_URL`** pointing at Postgres where **`001_initial_schema.up.sql`** has been applied |
| **`e2e`** | `docker compose config` | **`docker`** on `PATH` |

## Commands

```bash
make test                 # everything pytest collects (integration skips without DATABASE_URL)
make test-unit
make test-integration     # export DATABASE_URL=... first; see below
make test-e2e
```

## Integration tests and Postgres

Integration tests connect with **`psycopg`** using **`DATABASE_URL`**. They **do not** apply migrations; your pipeline (or you locally) must run the SQL in `db/migrations/` first.

**Local (Compose Postgres on port 5432):** if another Postgres already listens on `5432`, either stop it or map Compose to another host port (e.g. `5433:5432` in `docker-compose.yml`) and set `DATABASE_URL` accordingly.

Example:

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U veridoc -d veridoc -v ON_ERROR_STOP=1 \
  < db/migrations/001_initial_schema.up.sql
export DATABASE_URL=postgresql://veridoc:veridoc@localhost:5432/veridoc
make test-integration
```

CI applies migrations and runs **`pytest -m "unit or integration"`** — see `.github/workflows/ci.yml`.
