"""Unit tests for the CLI (no external services)."""

from __future__ import annotations

import sys

import pytest

from verifiedsignal.cli import main


@pytest.mark.unit
def test_main_runs(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["verifiedsignal"])
    main()
    out = capsys.readouterr().out
    assert "verifiedsignal" in out


@pytest.mark.unit
def test_main_respects_config_dir_env(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["verifiedsignal"])
    monkeypatch.setenv("VERIFIEDSIGNAL_CONFIG_DIR", "/tmp/verifiedsignal-cfg")
    main()
    assert "/tmp/verifiedsignal-cfg" in capsys.readouterr().out
