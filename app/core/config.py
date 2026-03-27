"""Application configuration (environment-driven)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "veridoc-api"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"

    database_url: str = Field(
        default="postgresql://veridoc:veridoc@localhost:5432/veridoc",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )

    # When true, skip Redis/ARQ and use in-process fake queue (tests + local without Redis).
    use_fake_queue: bool = Field(default=False, validation_alias="USE_FAKE_QUEUE")

    opensearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="OPENSEARCH_URL",
    )

    # Must match worker `WorkerSettings.queue_name` / `VERIDOC_ARQ_QUEUE`.
    arq_queue_name: str = Field(default="veridoc:jobs", validation_alias="VERIDOC_ARQ_QUEUE")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
