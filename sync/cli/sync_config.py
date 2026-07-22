"""
Sync MCP servers and platform configs into native formats.

Sources:
  env/mcp/*.json          — MCP server definitions (platform-agnostic)
  env/platforms/*.json    — platform-specific configs (follow each platform's spec)

Adding a new platform requires only:
  1. env/platforms/<name>.json  — platform config and sync metadata
  2. sync/platforms/<name>.py   — (optional) custom renderer; must export
                                  sync(mcp_servers, platform_cfg) -> None

If no renderer module exists and the JSON declares an ``mcp_target`` path,
the platform is synced via the generic JSON-MCP writer. No registration needed.

Path override: add an ``"install_root"`` field to env/platforms/<name>.json to override
the default Mac install root for that platform. Supports ``~`` expansion.
"""
import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import argparse

from core import paths as _paths
from core.common import (
    discover_platforms,
    filter_mcp_for_platform,
    load_all_mcp,
    load_platform_config,
    clear_env_block,
    sync_env_to_zshrc,
    sync_json_mcp,
)
from core.paths import platform_install_root, platform_is_installed

# sync_fn signature: (mcp_servers: dict, platform_cfg: dict) -> None
SyncFn = Callable[[dict[str, Any], dict[str, Any]], None]


# ── Renderer auto-discovery ───────────────────────────────────────────────────

def _load_renderer(name: str) -> SyncFn | None:
    """Dynamically load sync/platforms/<name>.py and return its sync() function.

    Module name uses underscores (``continue_`` is not needed because importlib
    does not parse module names as Python keywords). Returns None when no module
    exists or the module lacks a ``sync`` callable.
    """
    module_name = f"platforms.{name.replace('-', '_')}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            # A *dependency* inside the renderer failed to import — propagate so
            # the error is visible rather than silently degrading to generic sync.
            raise
        return None
    fn = getattr(module, "sync", None)
    return fn if callable(fn) else None


def _make_json_mcp_renderer(target_path: Path, platform_name: str) -> SyncFn:
    def _sync(mcp_servers: dict[str, Any], _platform_cfg: dict[str, Any]) -> None:
        sync_json_mcp(target_path, mcp_servers)
    return _sync


def _auto_discover_targets() -> dict[str, SyncFn]:
    """Build the full target map from env/platforms/*.json.

    For each platform:
      1. If sync/platforms/<name>.py exists and exports sync() → use it.
      2. Elif JSON declares mcp_target → use generic JSON-MCP writer.
      3. Else → warn and skip.
    """
    all_targets: dict[str, SyncFn] = {}
    for name in discover_platforms():
        renderer = _load_renderer(name)
        if renderer is not None:
            all_targets[name] = renderer
            continue

        cfg = load_platform_config(name)
        mcp_target = cfg.get("mcp_target")
        if mcp_target:
            target_path = Path(mcp_target).expanduser()
            all_targets[name] = _make_json_mcp_renderer(target_path, name)
            print(f"[sync] Auto-discovered JSON-MCP platform: {name} -> {target_path}")
        else:
            print(
                f"[warn] platform '{name}' has no renderer module "
                f"(sync/platforms/{name}.py) and no 'mcp_target' — skipped."
            )
    return all_targets


# ── Path injection ────────────────────────────────────────────────────────────

def _inject_path_override(name: str, platform_cfg: dict[str, Any]) -> None:
    """If platform JSON declares an ``install_root`` field, inject it into paths._PATH_OVERRIDES.

    This must be called BEFORE any path resolution so that all derived helpers
    (codex_root_dir, claude_root_dir, etc.) transparently use the custom root.
    Existing renderer modules require no changes.

    ``install_root`` in the platform JSON takes effect only when the platform is
    not already present in _PATH_OVERRIDES (secrets.json has higher priority).
    """
    json_path = platform_cfg.get("install_root")
    if not (json_path and isinstance(json_path, str) and json_path.strip()):
        return
    try:
        resolved = Path(json_path).expanduser()
    except (KeyError, RuntimeError):
        return

    # Ensure secrets.json is loaded first so its entries take priority over
    # the JSON install_root. _load_path_overrides() is idempotent/cached.
    _paths._load_path_overrides()
    # Only inject when not already overridden (secrets.json has higher priority
    # than the platform JSON's install_root field for per-machine overrides).
    if name not in _paths._PATH_OVERRIDES:
        _paths._PATH_OVERRIDES[name] = resolved


# ── Per-platform orchestration ────────────────────────────────────────────────

def _auto_export_env_to_zshrc(platform: str, platform_cfg: dict[str, Any]) -> None:
    # API fields are gated by the local api.enabled toggle: when disabled, do
    # not sync API env vars and clean any previously-synced managed block.
    api = platform_cfg.get("api")
    if isinstance(api, dict) and api.get("enabled", True) is False:
        clear_env_block(platform)
        return
    env = platform_cfg.get("export_env_to_zshrc")
    if not isinstance(env, dict) or not env:
        return
    sync_env_to_zshrc(platform, env)


def _effective_platform_config(platform: str) -> dict[str, Any]:
    cfg = load_platform_config(platform)
    return dict(cfg)


def _resolve_install_root_for_sync(name: str, platform_cfg: dict[str, Any]) -> Path | None:
    """Return the effective install root, falling back to ~/.{name} for new platforms."""
    root = platform_install_root(name)
    if root is not None:
        return root
    json_path = platform_cfg.get("install_root")
    if json_path and isinstance(json_path, str) and json_path.strip():
        try:
            return Path(json_path).expanduser()
        except (KeyError, RuntimeError):
            pass
    # New platform without a paths.py entry and no JSON path: use ~/.{name}
    return Path.home() / f".{name}"


def _sync_one_platform(
    name: str, fn: SyncFn, mcp_all: dict[str, Any]
) -> None:
    platform_cfg = _effective_platform_config(name)

    # Inject JSON path override BEFORE any path resolution so all derived helpers
    # in the renderer transparently use the custom root.
    _inject_path_override(name, platform_cfg)

    root = _resolve_install_root_for_sync(name, platform_cfg)
    if root is not None and not root.exists():
        # platform_is_installed() checks root.exists(); replicate that logic here
        # so new platforms (not in _INSTALL_ROOTS) are also skipped when absent.
        known = platform_install_root(name) is not None
        if known and not platform_is_installed(name):
            print(f"[sync] Platform '{name}' root not found: {root} — skipping (tool not installed).")
            return
        if not known and not root.exists():
            print(f"[sync] Platform '{name}' path not found: {root} — skipping.")
            return

    mcp_servers = filter_mcp_for_platform(mcp_all, name)
    fn(mcp_servers, platform_cfg)
    _auto_export_env_to_zshrc(name, platform_cfg)


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    mcp_all = load_all_mcp()
    if not mcp_all:
        print("[sync] No MCP servers found in env/mcp/ — continuing with empty MCP config.")

    all_targets = _auto_discover_targets()
    if not all_targets:
        print("[sync] No sync targets discovered — check env/platforms/.")
        return

    valid = sorted(all_targets.keys())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        default="all",
        metavar="TARGET",
        help=f"Platform to sync. One of: all, {', '.join(valid)}",
    )
    args = parser.parse_args(argv)

    if args.target == "all":
        for name in valid:
            _sync_one_platform(name, all_targets[name], mcp_all)
    elif args.target in all_targets:
        _sync_one_platform(args.target, all_targets[args.target], mcp_all)
    else:
        print(
            f"[error] Unknown target '{args.target}'. Valid: all, {', '.join(valid)}",
            file=sys.stderr,
        )
        raise SystemExit(1)
