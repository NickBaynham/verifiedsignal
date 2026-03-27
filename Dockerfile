# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PDM_CHECK_UPDATE=false \
    PDM_USE_VENV=true

RUN pip install --no-cache-dir --root-user-action=ignore pdm

WORKDIR /app

COPY pyproject.toml pdm.lock README.md ./
COPY src ./src
COPY app ./app
COPY worker ./worker
COPY tests ./tests
COPY db ./db
COPY config ./config

ENV PYTHONPATH=/app

RUN pdm install --frozen

# Default: HTTP API (override in Compose for worker or tests).
CMD ["pdm", "run", "api-prod"]
