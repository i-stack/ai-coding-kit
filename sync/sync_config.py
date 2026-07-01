#!/usr/bin/env python3
"""
Sync env/config.json into Cursor, Codex, Claude Code, Cline, and Xcode.

The source stays outside this directory because it is runtime configuration, not
sync tool code. Platform-specific rendering lives in sync/platforms/.

Platforms with complex rendering (Claude, Codex, Cline) are registered in TARGETS.
Simple JSON-MCP platforms can be declared directly in env/config.json without code:

    "platforms": {
        "zed": { "type": "json-mcp", "path": "~/.config/zed/mcp.json" }
    }
"""
import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from platforms import claude, cline, codebuddy, codex, cursor, gemini, continue_platform
from platforms.common import load_config, mcp_servers, read_json_object, write_json

SyncFn = Callable[[dict[str, Any]], None]

TARGETS: dict[str, SyncFn] = {
    "cursor": cursor.sync,
    "codebuddy": codebuddy.sync,
    "codex": codex.sync,
    "claude": claude.sync,
    "gemini": gemini.sync,
    "cline": cline.sync,
    "continue": continue_platform.sync,
}


def _build_declarative_targets(data: dict[str, Any]) -> dict[str, SyncFn]:
    """Return sync functions for platforms declared as type=json-mcp in config.

    Example config entry:
        "platforms": {
            "zed": { "type": "json-mcp", "path": "~/.config/zed/mcp.json" }
        }
    """
    result: dict[str, SyncFn] = {}
    for name, cfg in data.get("platforms", {}).items():
        if not isinstance(cfg, dict) or cfg.get("type") != "json-mcp":
            continue
        path_str = cfg.get("path", "")
        if not path_str:
            print(f"[warn] platforms.{name} is type=json-mcp but missing 'path' — skipped.")
            continue
        target_path = Path(path_str).expanduser()

        def make_sync(p: Path, pname: str) -> SyncFn:
            def _sync(d: dict[str, Any]) -> None:
                if p.is_symlink():
                    p.unlink()
                existing = read_json_object(p)
                existing["mcpServers"] = mcp_servers(d, pname)
                write_json(p, existing)
                print(f"Replaced MCP servers in {p}.")

            return _sync

        result[name] = make_sync(target_path, name)
    return result


def _warn_orphans(data: dict[str, Any], all_targets: dict[str, SyncFn]) -> None:
    """Warn about platforms that have config entries but no sync handler."""
    for name, cfg in data.get("platforms", {}).items():
        if name in all_targets:
            continue
        if isinstance(cfg, dict) and cfg.get("type") == "json-mcp":
            continue
        print(f"[warn] platforms.{name} has config but no sync handler — skipped.")


def main() -> None:
    data = load_config()
    if data is None:
        return

    declarative = _build_declarative_targets(data)
    all_targets: dict[str, SyncFn] = {**TARGETS, **declarative}

    _warn_orphans(data, all_targets)

    valid = sorted(all_targets.keys())
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--target",
        default="all",
        metavar="TARGET",
        help=f"Platform to sync. One of: all, {', '.join(valid)}",
    )
    args = parser.parse_args()

    if args.target == "all":
        for sync in all_targets.values():
            sync(data)
    elif args.target in all_targets:
        all_targets[args.target](data)
    else:
        print(f"[error] Unknown target '{args.target}'. Valid: all, {', '.join(valid)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
