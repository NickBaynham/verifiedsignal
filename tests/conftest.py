"""Shared pytest configuration and fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root (contains pyproject.toml)."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def docker_available() -> bool:
    return shutil.which("docker") is not None
