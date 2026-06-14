#!/usr/bin/env python3
"""
Sync env/config.json into Cursor, Codex, Claude Code, and Xcode.

The source stays outside this directory because it is runtime configuration, not
sync tool code. Platform-specific rendering lives in sync/platforms/.
"""
import argparse
from collections.abc import Callable
from typing import Any

from platforms import claude, codex, cursor
from platforms.common import load_config

SyncFn = Callable[[dict[str, Any]], None]

TARGETS: dict[str, SyncFn] = {
    "cursor": cursor.sync,
    "codex": codex.sync,
    "claude": claude.sync,
}


def sync_all(data: dict[str, Any]) -> None:
    for sync in TARGETS.values():
        sync(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    choices = ("all", *TARGETS.keys())
    parser.add_argument("--target", choices=choices, default="all", help="Target platform to sync.")
    args = parser.parse_args()

    data = load_config()
    if data is None:
        return

    if args.target == "all":
        sync_all(data)
    else:
        TARGETS[args.target](data)


if __name__ == "__main__":
    main()
