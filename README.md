# veridoc

A document intelligence platform. This repository uses **Python** with **[PDM](https://pdm-project.org/latest/)** for dependencies, a **Makefile** for setup and common tasks, and **Docker Compose** to run the app and local infrastructure in containers.

## What’s included so far

This repo is an **early scaffold** with the following in place:

- **Application** — Python **3.11+**, `src/veridoc/` package layout, a small **CLI** (`pdm run python -m veridoc`, `pdm run veridoc`, `--config-dir` / `VERIDOC_CONFIG_DIR`).
- **PDM** — `pyproject.toml`, committed **`pdm.lock`**, **`pdm-backend`** build, dev tools in the **`dev`** dependency group (**pytest**, **pytest-cov**, **ruff**).
- **Makefile** — `setup`, `lock` / `sync`, `test` / `test-unit` / `test-integration` / `test-e2e`, `lint`, `format`, `clean`, `config`, `resources` (placeholder), and Docker-related targets.
- **Tests** — **`pytest`** with markers **`unit`**, **`integration`** (Postgres + migrations via **`DATABASE_URL`**), **`e2e`** (Compose file validation). Dev dependency **`psycopg`** for DB integration tests. See **[`tests/README.md`](tests/README.md)**.
- **CI** — **[`.github/workflows/ci.yml`](.github/workflows/ci.yml)** runs Ruff, applies migrations to a **Postgres 16** service, runs **unit + integration** tests, then **e2e** (`docker compose config`).
- **Docker** — **`Dockerfile`** (Python 3.12, PDM, `pdm install --frozen`), **`.dockerignore`**.
- **Docker Compose** — local stack:
  - **PostgreSQL** — canonical relational data  
  - **Redis** — pub/sub, cache, worker coordination (AOF on)  
  - **MinIO** — S3-compatible object storage (API + console)  
  - **OpenSearch** + **OpenSearch Dashboards** — search/analytics UI  
  - **app** — veridoc container (waits for infra health checks)  
  - **test** — pytest in a one-off container (**profile:** `test`, not started by default)
- **Configuration** — **`.env.example`** (ports, DB/Redis/S3/OpenSearch URLs), **`config/application.example.yml`**, **`config/`** mounted read-only into the app container.
- **Canonical database schema** — SQL migrations under **`db/migrations/`** (users, organizations, collections, documents, sources, pipeline runs/events, document scores). See **[`db/README.md`](db/README.md)** for how to apply them and architectural notes (Postgres as source of truth, OpenSearch as disposable index).

## Prerequisites

- **Python** 3.11 or newer
- **[PDM](https://pdm-project.org/latest/#installation)** on your `PATH` (`pdm --version`)
- **GNU Make**
- **Docker** and **Docker Compose** v2 (`docker compose version`) if you use the container workflow

## Quick start (local)

1. Clone the repository and enter the project directory.

2. Install dependencies and create a local `.env` from the example (if `.env` does not exist):

   ```bash
   make setup
   ```

   If PDM is not installed, follow the [official PDM installation guide](https://pdm-project.org/latest/#installation) and run `make setup` again.

3. Run the CLI:

   ```bash
   pdm run python -m veridoc
   ```

   Or use the console script:

   ```bash
   pdm run veridoc
   ```

4. Run tests and linters:

   ```bash
   make test
   make lint
   ```

   Integration tests need **`DATABASE_URL`** and an applied migration (see [`tests/README.md`](tests/README.md)). Without that, `make test` still passes by **skipping** integration cases.

## Useful commands

### Local development

| Command | Purpose |
|--------|---------|
| `make` / `make help` | Print Makefile targets |
| `make setup` | `make config` + `pdm install` |
| `make config` | Create `.env` from `.env.example` if missing |
| `make lock` | Refresh `pdm.lock` after dependency changes |
| `make sync` | Install exactly what `pdm.lock` specifies |
| `make test` | Pytest (unit + e2e; integration skips if `DATABASE_URL` unset) |
| `make test-unit` | `pytest -m unit` |
| `make test-integration` | `pytest -m integration` (requires `DATABASE_URL` + migrations) |
| `make test-e2e` | `pytest -m e2e` (requires `docker` on `PATH`) |
| `make lint` | Ruff check |
| `make format` | Ruff format |
| `make clean` | Drop local build/caches (`.pytest_cache`, `.ruff_cache`, etc.) |
| `make resources` | Placeholder for future asset downloads |

| Command | Purpose |
|--------|---------|
| `pdm run pytest` | Same as `make test` |
| `pdm run pytest -m "unit or integration"` | Typical CI subset (with `DATABASE_URL` set) |
| `pdm run pytest --cov=veridoc` | Tests with coverage (pytest-cov installed) |
| `pdm run ruff check src tests` | Same as `make lint` |
| `pdm run ruff format src tests` | Same as `make format` |

### Docker and Compose

| Command | Purpose |
|--------|---------|
| `make docker-build` | Build the **app** image (`veridoc:local`) |
| `make docker-up` | `make config`, then **`docker compose up --build`** (full stack in the **foreground**) |
| `make docker-down` | `docker compose down` (stops services; keeps volumes) |
| `make docker-test` | `make config`, build, then **`docker compose --profile test run --rm test`** (pytest in Docker) |
| `make docker-run` | `make config`, build, then **`docker compose run --rm app`** (one-off app; Compose starts dependencies) |

| Command | Purpose |
|--------|---------|
| `docker compose up -d` | Full stack in the **background** |
| `docker compose up -d postgres redis minio opensearch opensearch-dashboards` | **Infrastructure only** (no `app` container) |
| `docker compose up -d --build app` | Rebuild and start **app** plus its dependencies |
| `docker compose ps` | Service status |
| `docker compose logs -f app` | Follow logs for `app` (replace `app` with any service name) |
| `docker compose logs -f opensearch opensearch-dashboards` | Follow OpenSearch-related logs |
| `docker compose --profile test run --rm test` | Pytest container without going through Make |
| `docker compose run --rm app pdm run veridoc -- --help` | One-off command inside the app image |
| `docker compose down -v` | Stop and **remove named volumes** (wipes Postgres/Redis/MinIO/OpenSearch data) |
| `docker compose pull` | Pull newer infra images (MinIO, OpenSearch, etc.) |
| `docker compose exec -T postgres psql -U veridoc -d veridoc -v ON_ERROR_STOP=1 < db/migrations/001_initial_schema.up.sql` | Apply initial DB schema (from repo root; see [`db/README.md`](db/README.md)) |

### Local URLs (default ports)

| Service | URL |
|--------|-----|
| MinIO console | [http://localhost:9001](http://localhost:9001) |
| MinIO S3 API | `http://localhost:9000` |
| OpenSearch REST | [http://localhost:9200](http://localhost:9200) |
| OpenSearch Dashboards | [http://localhost:5601](http://localhost:5601) |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

## Makefile reference

Run `make` or `make help` to print this list from the Makefile.

| Target | Description |
|--------|-------------|
| `make setup` | Runs `make config`, then `pdm install` (requires `pdm` on `PATH`) |
| `make lock` | Regenerates `pdm.lock` from `pyproject.toml` |
| `make sync` / `make install` | Installs exactly what `pdm.lock` specifies |
| `make test` | `pdm run pytest` (see `make test-unit`, `test-integration`, `test-e2e`) |
| `make test-unit` | `pdm run pytest -m unit` |
| `make test-integration` | `pdm run pytest -m integration` |
| `make test-e2e` | `pdm run pytest -m e2e` |
| `make lint` | `pdm run ruff check src tests` |
| `make format` | `pdm run ruff format src tests` |
| `make clean` | Removes common build and cache directories |
| `make config` | Copies `.env.example` → `.env` only if `.env` is missing |
| `make resources` | Placeholder for future asset or download steps |
| `make docker-build` | `docker compose build` |
| `make docker-up` | `make config`, then **`docker compose up --build`** (Postgres, Redis, MinIO, OpenSearch, Dashboards, **app**) |
| `make docker-down` | `docker compose down` |
| `make docker-test` | `make config`, build image, then run the `test` service (pytest in Docker) |
| `make docker-run` | `make config`, build image, then one-off `app` container |

Make variables **`PDM`** and **`DOCKER_COMPOSE`** default to `pdm` and `docker compose`; override them if your install paths or Compose wrapper differ.

## PDM without Make

Typical commands:

```bash
pdm install              # install project + dev dependencies from lockfile
pdm lock                 # update pdm.lock after changing pyproject.toml
pdm add <package>        # add a runtime dependency
pdm add -dG dev <pkg>    # add a dev dependency to the `dev` group
pdm run pytest
pdm run ruff check src tests
pdm run ruff format src tests
```

Runtime dependencies live under `[project]` in `pyproject.toml`. Development tools (pytest, ruff, etc.) live in `[dependency-groups]` under `dev`.

## Docker Compose

The stack is defined in `docker-compose.yml`. **`make docker-up`** (or `docker compose up`) starts every service below except **`test`**, which uses the **`test`** profile.

| Service | Role | Default host port |
|--------|------|-------------------|
| **postgres** | Canonical relational data (PostgreSQL 16) | `5432` |
| **redis** | Pub/sub, caching, worker coordination (Redis 7, AOF on) | `6379` |
| **minio** | S3-compatible object storage (API + web console) | `9000` (API), `9001` (console) |
| **opensearch** | Search and analytics (single-node; `DISABLE_SECURITY_PLUGIN=true` for local dev only) | `9200` |
| **opensearch-dashboards** | OpenSearch Dashboards UI | `5601` |
| **app** | veridoc application (`pdm run python -m veridoc`) | (none; use `docker compose logs`) |
| **test** | Runs `pytest` in a one-off container (`profile: test`) | — |

The **app** service waits for **postgres**, **redis**, **minio**, and **opensearch** to pass their health checks before starting. Connection defaults are wired through environment variables (see **`.env.example`**); inside the Compose network the app receives URLs such as `postgresql://…@postgres:5432/…`, `redis://redis:6379/0`, `http://minio:9000`, and `http://opensearch:9200`.

**OpenSearch:** the cluster runs with the security plugin disabled via `DISABLE_SECURITY_PLUGIN=true` in Compose—suitable only for trusted local machines; do not expose these ports on a network. On **Linux**, if the node fails to start, raise `vm.max_map_count` (for example `sudo sysctl -w vm.max_map_count=262144`). See the [OpenSearch Docker install notes](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/).

**MinIO:** open `http://localhost:9001` and sign in with `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` from `.env` (defaults match the example file). Create a bucket named like `S3_BUCKET` (`veridoc` by default) when you begin storing objects.

`.env` is optional: **`app`** and **`test`** use `env_file` with `required: false`. Compose still applies defaults from `docker-compose.yml` when variables are unset. Run **`make config`** to create `.env` from **`.env.example`** so host port overrides and credentials stay consistent.

For a consolidated command list, see **[Useful commands](#useful-commands)** above.

## Configuration and environment

- **`.env.example`** — template for local and Compose-related variables (Postgres, Redis, MinIO/S3, OpenSearch ports, `DATABASE_URL`, `REDIS_URL`, etc.). **`make config`** copies it to **`.env`** when `.env` is missing.
- **`VERIDOC_CONFIG_DIR`** — directory the CLI treats as the config root (default `config` if unset). Under Compose it is set to `/app/config` inside the container.
- **`config/`** — mount point for configuration files. **`config/application.example.yml`** is a sample; copy or adapt it for your own `application.yml` (or other files) as the product grows.
- **Database** — apply **`db/migrations/001_initial_schema.up.sql`** against your Postgres (see [`db/README.md`](db/README.md)). **`DATABASE_URL`** in `.env` should point at that database.

Do not commit secrets. `.env` is gitignored.

## Project layout

```
├── Makefile
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .env.example
├── pyproject.toml
├── pdm.lock
├── .github/workflows/      # CI (Postgres service + pytest + ruff + e2e)
├── db/
│   ├── README.md           # schema docs + apply/rollback examples
│   └── migrations/         # *.up.sql / *.down.sql
├── src/veridoc/            # application package
├── tests/                  # pytest (unit / integration / e2e); see tests/README.md
└── config/                 # runtime configuration (mounted in Docker)
```

## License

See [LICENSE](LICENSE).
