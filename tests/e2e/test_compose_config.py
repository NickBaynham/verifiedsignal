"""E2E-style checks that do not require a running stack (Compose file validity)."""

from __future__ import annotations

import subprocess

import pytest


@pytest.mark.e2e
def test_docker_compose_config_valid(repo_root, docker_available):
    if not docker_available:
        pytest.skip("docker not on PATH")
    result = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
