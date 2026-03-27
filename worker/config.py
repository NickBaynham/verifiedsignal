"""Worker configuration (env vars)."""

from __future__ import annotations

import os

from arq.connections import RedisSettings


def build_redis_settings() -> RedisSettings:
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return RedisSettings.from_dsn(url)


# Queue name must match API `Settings.arq_queue_name` / `create_pool(..., default_queue_name=...)`.
QUEUE_NAME = os.environ.get("VERIDOC_ARQ_QUEUE", "veridoc:jobs")

redis_settings = build_redis_settings()
