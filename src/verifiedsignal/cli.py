"""CLI entry point for VerifiedSignal."""

from __future__ import annotations

import argparse
import os

from verifiedsignal import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="verifiedsignal",
        description="VerifiedSignal — Document Intelligence Platform",
    )
    parser.add_argument(
        "--config-dir",
        default=os.environ.get("VERIFIEDSIGNAL_CONFIG_DIR", "config"),
        help=(
            "Directory containing application configuration "
            "(default: config or VERIFIEDSIGNAL_CONFIG_DIR)"
        ),
    )
    args = parser.parse_args()
    print(f"verifiedsignal {__version__} (config dir: {args.config_dir})")


if __name__ == "__main__":
    main()
