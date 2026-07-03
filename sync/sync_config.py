#!/usr/bin/env python3
"""
Sync MCP servers and platform configs into native formats.

Sources:
  env/mcp/*.json          — MCP server definitions (platform-agnostic)
  env/platforms/*.json    — platform-specific configs (follow each platform's spec)

Platforms are auto-discovered from env/platforms/; adding a new platform only
requires a config file and (if complex rendering is needed) a renderer module.
"""
import argparse
import sys
from collections.abc import Callable
from typing import Any

from platforms import claude, cline, codebuddy, codex, cursor, gemini
from platforms.common import discover_platforms, filter_mcp_for_platform, load_all_mcp, load_platform_config, sync_env_to_zshrc

# continue.py contains 'continue' keyword which can't be a Python import name.
import importlib as _importlib
_continue = _importlib.import_module("platforms.continue")

# sync_fn signature: (mcp_servers: dict, platform_cfg: dict) -> None
SyncFn = Callable[[dict[str, Any], dict[str, Any]], None]

# Platforms that have custom renderer logic (not pure JSON-MCP).
# Registered here, discovered from env/platforms/ for pure JSON-MCP platforms.
RENDERERS: dict[str, SyncFn] = {
    "cursor": cursor.sync,
    "codebuddy": codebuddy.sync,
    "codex": codex.sync,
    "claude": claude.sync,
    "gemini": gemini.sync,
    "cline": cline.sync,
    "continue": _continue.sync,
}


def _auto_discover_targets() -> dict[str, SyncFn]:
    """Build the full target map: registered renderers + auto-discovered JSON-MCP platforms."""
    all_targets: dict[str, SyncFn] = dict(RENDERERS)
    discovered = discover_platforms()

    # Platforms that are config-only (no sync target) — skip silently
    _config_only = {"rag-gateway"}

    for name in discovered:
        if name in all_targets:
            continue  # already has a custom renderer
        if name in _config_only:
            continue  # config-only platform, not a sync target
        cfg = load_platform_config(name)
        mcp_target = cfg.get("mcp_target")
        if not mcp_target:
            print(f"[warn] platform '{name}' has no custom renderer and no 'mcp_target' — skipped.")
            continue

        from pathlib import Path as _Path
        from platforms.common import sync_json_mcp as _sync_json_mcp

        target_path = _Path(mcp_target).expanduser()

        def _make_sync(p: _Path, pname: str) -> SyncFn:
            def _s(mcp_servers: dict[str, Any], _platform_cfg: dict[str, Any]) -> None:
                _sync_json_mcp(p, mcp_servers)
            return _s

        all_targets[name] = _make_sync(target_path, name)
        print(f"[sync] Auto-discovered JSON-MCP platform: {name} -> {target_path}")

    return all_targets


def _auto_export_env_to_zshrc(platform: str, platform_cfg: dict[str, Any]) -> None:
    """Automatically write env vars to ~/.zshrc if platform config declares
    an export_env_to_zshrc block.

    Convention: env/platforms/<platform>.json may contain:

        "export_env_to_zshrc": {
            "VAR_NAME": "value"
        }

    Each key in the object is treated as an env var to export.
    When present, the orchestrator calls sync_env_to_zshrc() so that each
    platform's sync() doesn't need to handle zshrc manually.
    """
    env = platform_cfg.get("export_env_to_zshrc")
    if not isinstance(env, dict) or not env:
        return
    sync_env_to_zshrc(platform, env)


def main() -> None:
    mcp_all = load_all_mcp()
    if not mcp_all:
        print("[sync] No MCP servers found in env/mcp/ — continuing with empty MCP config.")

    all_targets = _auto_discover_targets()
    if not all_targets:
        print("[sync] No sync targets discovered — check env/platforms/.")
        return

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
        for name in valid:
            fn = all_targets[name]
            mcp_servers = filter_mcp_for_platform(mcp_all, name)
            platform_cfg = load_platform_config(name)
            fn(mcp_servers, platform_cfg)
            _auto_export_env_to_zshrc(name, platform_cfg)
    elif args.target in all_targets:
        fn = all_targets[args.target]
        mcp_servers = filter_mcp_for_platform(mcp_all, args.target)
        platform_cfg = load_platform_config(args.target)
        fn(mcp_servers, platform_cfg)
        _auto_export_env_to_zshrc(args.target, platform_cfg)
    else:
        print(f"[error] Unknown target '{args.target}'. Valid: all, {', '.join(valid)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
