"""FastAPI entrypoint: synchronous API surface, SSE, auth boundaries."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    collections,
    documents,
    events,
    health,
    info,
    search,
    session_auth,
    users_api,
)
from app.core.config import get_settings
from app.services.queue_backend import close_job_queue
from app.services.storage_service import reset_object_storage

logger = logging.getLogger(__name__)


def _production_like_environment() -> bool:
    env = get_settings().environment.lower()
    return env in ("production", "prod")


def _register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        _request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        logger.error("SQLAlchemy error", exc_info=exc)
        if _production_like_environment():
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        orig = getattr(exc, "orig", None)
        message = str(orig) if orig is not None else str(exc)
        if len(message) > 2000:
            message = message[:2000] + "…"
        return JSONResponse(
            status_code=500,
            content={
                "detail": "database error",
                "error_type": type(exc).__name__,
                "message": message,
            },
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    yield
    await close_job_queue()
    reset_object_storage()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    _register_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(session_auth.router)
    v1 = settings.api_v1_prefix.rstrip("/") or "/api/v1"
    application.include_router(health.router, prefix=v1)
    application.include_router(info.router, prefix=v1)
    application.include_router(documents.router, prefix=v1)
    application.include_router(collections.router, prefix=v1)
    application.include_router(users_api.router, prefix=v1)
    application.include_router(search.router, prefix=v1)
    application.include_router(events.router, prefix=v1)
    return application


app = create_app()
