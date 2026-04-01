#!/usr/bin/env bash
# Minimal reference scorer for ENQUEUE_SCORE_AFTER_PIPELINE + SCORE_ASYNC_BACKEND=http.
# See docs/scoring-http.md ("Reference HTTP scorer").
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT}/scripts"
cd "$ROOT"
exec python -m uvicorn reference_http_scorer.app:app --host 127.0.0.1 --port 9100 "$@"
