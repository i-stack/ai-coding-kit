#!/usr/bin/env python3
"""Unified CLI entrypoint for sync tools.

Usage:
    python3 sync/cli/main.py sync --target all
    python3 sync/cli/main.py verify --target all
    python3 sync/cli/main.py validate-env --mcp-only
    python3 sync/cli/main.py validate-keys --target claude
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SYNC_DIR = Path(__file__).resolve().parents[1]
if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from cli import sync_config, validate_env_schema, validate_platform_keys, verify  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = ("sync", "verify", "validate-env", "validate-keys")
    parser.add_argument("command", choices=commands)

    if not args or args[0] in ("-h", "--help"):
        parser.print_help()
        return 0 if args else 2

    command, remainder = args[0], args[1:]
    if command not in commands:
        parser.error(f"invalid choice: {command!r} (choose from {', '.join(commands)})")

    if command == "sync":
        sync_config.main(remainder)
        return 0
    if command == "verify":
        return verify.main(remainder)
    if command == "validate-env":
        return validate_env_schema.main(remainder)
    if command == "validate-keys":
        return validate_platform_keys.main(remainder)
    return 2


if __name__ == "__main__":
    sys.exit(main())
