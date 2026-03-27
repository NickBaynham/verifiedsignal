"""FastAPI entrypoint: synchronous API surface, SSE, auth boundaries."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import documents, events, health, info, search
from app.core.config import get_settings
from app.services.queue_backend import close_job_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    yield
    await close_job_queue()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    v1 = settings.api_v1_prefix.rstrip("/") or "/api/v1"
    application.include_router(health.router, prefix=v1)
    application.include_router(info.router, prefix=v1)
    application.include_router(documents.router, prefix=v1)
    application.include_router(search.router, prefix=v1)
    application.include_router(events.router, prefix=v1)
    return application


app = create_app()
