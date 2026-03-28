.PHONY: help setup lock sync install test test-unit test-integration test-e2e test-api lint format clean config resources docker-build docker-up docker-down docker-test docker-run api-local api-local-prod ci-local ci-local-stop ci-local-postgres ci-local-migrate-sql ci-local-migrate

# Default Python / PDM (override if needed)
PYTHON ?= python3
PDM ?= pdm
DOCKER_COMPOSE ?= docker compose

# Ephemeral Postgres for `make ci-local` (same image/credentials as GitHub Actions).
# Default host port 5433 avoids clashing with Compose Postgres on 5432; override with CI_LOCAL_PG_PORT=5432 if free.
CI_LOCAL_PG_CONTAINER ?= verifiedsignal-ci-postgres
CI_LOCAL_PG_PORT ?= 5433
CI_LOCAL_PG_URL = postgresql://verifiedsignal:verifiedsignal@127.0.0.1:$(CI_LOCAL_PG_PORT)/verifiedsignal

# Host-side service URLs for `make api-local` / `api-local-prod` (pdm run api on your machine while
# Postgres / Redis / MinIO / OpenSearch run in Docker with default published ports).
# Override any piece, e.g. `make api-local LOCAL_API_PG_PORT=5433` or set LOCAL_API_DATABASE_URL entirely.
LOCAL_API_DB_USER ?= verifiedsignal
LOCAL_API_DB_PASSWORD ?= verifiedsignal
LOCAL_API_DB_NAME ?= verifiedsignal
LOCAL_API_PG_PORT ?= 5432
LOCAL_API_REDIS_PORT ?= 6379
LOCAL_API_MINIO_PORT ?= 9000
LOCAL_API_OS_PORT ?= 9200
LOCAL_API_DATABASE_URL ?= postgresql://$(LOCAL_API_DB_USER):$(LOCAL_API_DB_PASSWORD)@127.0.0.1:$(LOCAL_API_PG_PORT)/$(LOCAL_API_DB_NAME)
# HTTP bind for api-local / api-local-prod (override if 8000 is in use, e.g. another uvicorn).
LOCAL_API_PORT ?= 8000

# env(1) prefix applied before `pdm run api` for local host development
API_LOCAL_ENV = env \
	DATABASE_URL='$(LOCAL_API_DATABASE_URL)' \
	REDIS_URL='redis://127.0.0.1:$(LOCAL_API_REDIS_PORT)/0' \
	S3_ENDPOINT_URL='http://127.0.0.1:$(LOCAL_API_MINIO_PORT)' \
	OPENSEARCH_URL='http://127.0.0.1:$(LOCAL_API_OS_PORT)'

help:
	@echo "VerifiedSignal — common targets"
	@echo ""
	@echo "  make setup       Install PDM (if missing) and project dependencies"
	@echo "  make lock        Refresh pdm.lock from pyproject.toml"
	@echo "  make sync        Install exactly what pdm.lock specifies"
	@echo "  make install     Alias for sync"
	@echo "  make test        Run pytest (unit + e2e; integration skips without DATABASE_URL)"
	@echo "  make test-unit   Run pytest -m unit only"
	@echo "  make test-integration  Run pytest -m integration (needs DATABASE_URL + migrations)"
	@echo "  make test-e2e    Run pytest -m e2e (needs docker on PATH)"
	@echo "  make test-api    Run pytest -m api (ASGI smoke tests)"
	@echo "  make lint        Run ruff check"
	@echo "  make format      Run ruff format"
	@echo "  make clean       Remove build and cache artifacts"
	@echo "  make config      Ensure .env from .env.example (idempotent)"
	@echo "  make resources   Placeholder for assets / downloads (extend as needed)"
	@echo "  make docker-build   Build compose images"
	@echo "  make docker-up      Run full stack: Postgres, Redis, MinIO, OpenSearch, Dashboards, app"
	@echo "  make docker-down    Stop app stack"
	@echo "  make docker-test    Run tests in Docker (compose profile: test)"
	@echo "  make docker-run     One-off app container run"
	@echo "  make api-local      Run FastAPI on host with 127.0.0.1 URLs (LOCAL_API_PG_PORT, LOCAL_API_PORT=8000)"
	@echo "  make api-local-prod Same as api-local without --reload"
	@echo "  make ci-local       Ephemeral Postgres:16 + migrations + Ruff + pytest; removes container after (even on failure)"
	@echo "  make ci-local-stop  Remove the ci-local Postgres container (manual cleanup)"

setup: config
	@command -v $(PDM) >/dev/null 2>&1 || { echo "Install PDM: https://pdm-project.org/latest/#installation"; exit 1; }
	$(PDM) install

lock:
	$(PDM) lock

sync:
	$(PDM) sync

install: sync

test:
	$(PDM) run python -m pytest

test-unit:
	$(PDM) run python -m pytest -m unit

test-integration:
	$(PDM) run python -m pytest -m integration

test-e2e:
	$(PDM) run python -m pytest -m e2e

test-api:
	$(PDM) run python -m pytest -m api

lint:
	$(PDM) run python -m ruff check src tests app worker

format:
	$(PDM) run python -m ruff format src tests app worker

clean:
	rm -rf .pytest_cache .ruff_cache .pdm-build dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

config:
	@test -f .env || cp .env.example .env

resources:
	@echo "No resource fetch steps defined yet. Add downloads or asset sync here."

docker-build:
	$(DOCKER_COMPOSE) build

docker-up: config
	$(DOCKER_COMPOSE) up --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-test: config docker-build
	$(DOCKER_COMPOSE) --profile test run --rm test

docker-run: config docker-build
	$(DOCKER_COMPOSE) run --rm app

api-local:
	$(API_LOCAL_ENV) $(PDM) run python -m uvicorn app.main:app --host 0.0.0.0 --port $(LOCAL_API_PORT) --reload

api-local-prod:
	$(API_LOCAL_ENV) $(PDM) run python -m uvicorn app.main:app --host 0.0.0.0 --port $(LOCAL_API_PORT)

ci-local-stop:
	docker rm -f $(CI_LOCAL_PG_CONTAINER) 2>/dev/null || true

ci-local-postgres: ci-local-stop
	docker run -d --name $(CI_LOCAL_PG_CONTAINER) -p $(CI_LOCAL_PG_PORT):5432 \
		-e POSTGRES_USER=verifiedsignal \
		-e POSTGRES_PASSWORD=verifiedsignal \
		-e POSTGRES_DB=verifiedsignal \
		postgres:16-alpine
	until docker exec $(CI_LOCAL_PG_CONTAINER) pg_isready -U verifiedsignal -d verifiedsignal; do sleep 1; done

# Apply migrations to an already-running $(CI_LOCAL_PG_CONTAINER) (used by ci-local without restarting Postgres).
ci-local-migrate-sql:
	docker exec -i $(CI_LOCAL_PG_CONTAINER) psql -U verifiedsignal -d verifiedsignal -v ON_ERROR_STOP=1 \
		< db/migrations/001_initial_schema.up.sql
	docker exec -i $(CI_LOCAL_PG_CONTAINER) psql -U verifiedsignal -d verifiedsignal -v ON_ERROR_STOP=1 \
		< db/migrations/002_intake_document_fields.up.sql

ci-local-migrate: ci-local-postgres ci-local-migrate-sql

# One shell: EXIT trap runs for any failure (including docker bind errors) so the named container is not left behind.
ci-local:
	set -e; \
	trap 'docker rm -f $(CI_LOCAL_PG_CONTAINER) 2>/dev/null || true' EXIT; \
	$(MAKE) ci-local-postgres; \
	$(MAKE) ci-local-migrate-sql; \
	env DATABASE_URL='$(CI_LOCAL_PG_URL)' $(PDM) run python -m ruff check src tests app worker; \
	env DATABASE_URL='$(CI_LOCAL_PG_URL)' $(PDM) run python -m pytest -v --tb=short
