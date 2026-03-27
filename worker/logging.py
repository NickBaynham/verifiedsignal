"""Structured logging helpers for the worker."""

from __future__ import annotations

import logging
import os

_LOG_LEVEL = os.environ.get("WORKER_LOG_LEVEL", "INFO")


def configure_logging() -> None:
    logging.basicConfig(
        level=_LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
