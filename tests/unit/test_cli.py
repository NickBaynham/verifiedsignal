"""Unit tests for the CLI (no external services)."""

from __future__ import annotations

import sys

import pytest

from veridoc.cli import main


@pytest.mark.unit
def test_main_runs(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["veridoc"])
    main()
    out = capsys.readouterr().out
    assert "veridoc" in out


@pytest.mark.unit
def test_main_respects_config_dir_env(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["veridoc"])
    monkeypatch.setenv("VERIDOC_CONFIG_DIR", "/tmp/veridoc-cfg")
    main()
    assert "/tmp/veridoc-cfg" in capsys.readouterr().out
