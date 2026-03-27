"""Unit tests for package metadata and repository layout."""

from __future__ import annotations

import importlib.metadata

import pytest


@pytest.mark.unit
def test_version_matches_pyproject():
    import veridoc

    dist_version = importlib.metadata.version("veridoc")
    assert veridoc.__version__ == dist_version


@pytest.mark.unit
def test_migration_files_exist(repo_root):
    up = repo_root / "db" / "migrations" / "001_initial_schema.up.sql"
    down = repo_root / "db" / "migrations" / "001_initial_schema.down.sql"
    assert up.is_file(), f"missing {up}"
    assert down.is_file(), f"missing {down}"
    assert "CREATE TABLE users" in up.read_text()
    assert "DROP TABLE IF EXISTS users" in down.read_text()
