"""Validate that platform config keys are properly covered.

Checks that every key in env/platforms/*.json is either:
  - Synced to the target (not in _HOST_SKIP)
  - Explicitly excluded via _HOST_SKIP or internal keys

This prevents new platform config keys from silently leaking into
settings or being silently dropped without being categorized.

Usage:
    python3 sync/cli/main.py validate-keys                 # check all platforms
    python3 sync/cli/main.py validate-keys --target claude # check one platform
"""
import json
from pathlib import Path

SYNC_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SYNC_DIR.parent

from platforms.claude import _HOST_SKIP as CLAUDE_HOST_SKIP
from platforms.codex import _HOST_SKIP as CODEX_HOST_SKIP
from cli.validate_env_schema import COMMON_PLATFORM_FIELDS, known_fields_for_platform

# Keys that are handled by the sync engine itself (not synced to settings)
ENGINE_HANDLED_KEYS = COMMON_PLATFORM_FIELDS | {"hooks", "_hostSettings"}
ENGINE_HANDLED_BY_PLATFORM = {
    "continue": {"path", "recall"},
}

def load_platform_json(platform: str) -> dict:
    path = REPO_ROOT / "env" / "platforms" / f"{platform}.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_host_skip(platform: str) -> set[str]:
    """Return the _HOST_SKIP set for a given platform."""
    mapping = {
        "claude": CLAUDE_HOST_SKIP,
        "codex": CODEX_HOST_SKIP,
    }
    return mapping.get(platform, set())


def check_platform(platform: str) -> list[str]:
    """Check a single platform's key coverage. Returns list of warnings.

    A key is properly categorized when it is one of:
      - internal (starts with '_'),
      - engine-handled (e.g. env, hooks, export_env_to_zshrc, _hostSettings),
      - declared in the platform's _HOST_SKIP (excluded from team settings),
      - a known team-shared key for this platform.

    Any other key (unknown/typo, or a host-specific key missing from _HOST_SKIP)
    produces a warning through the schema allowlist, making the check
    fail-closed instead of relying on another hand-maintained host-specific
    list.
    """
    cfg = load_platform_json(platform)
    if not cfg:
        return [f"  {platform}: no config file found"]

    warnings: list[str] = []
    host_skip = get_host_skip(platform)
    engine_handled = ENGINE_HANDLED_KEYS | ENGINE_HANDLED_BY_PLATFORM.get(platform, set())
    known_fields = known_fields_for_platform(platform)

    synced: set[str] = set()
    skip_count = 0
    engine_count = 0
    for key in sorted(cfg):
        if key.startswith("_"):
            continue
        if key in engine_handled:
            engine_count += 1
            continue
        if key in host_skip:
            skip_count += 1
            continue
        if key not in known_fields:
            warnings.append(
                f"  {platform}: key '{key}' is not in the schema allowlist and not in "
                f"_HOST_SKIP — UNCATEGORIZED (typo or missing classification?)."
            )
            continue
        synced.add(key)

    total = len([k for k in cfg if not k.startswith("_")])
    if warnings:
        print(
            f"  {platform}: {len(warnings)} issue(s) — {len(synced)} synced, "
            f"{skip_count} host-skipped, {engine_count} engine-handled ({total} total)"
        )
    else:
        print(
            f"  {platform}: OK — {len(synced)} synced, {skip_count} host-skipped, "
            f"{engine_count} engine-handled ({total} total)"
        )
    return warnings


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="all", help="Platform to check (default: all)")
    args = parser.parse_args(argv)

    if args.target == "all":
        platforms_dir = REPO_ROOT / "env" / "platforms"
        platforms = sorted(f.stem for f in platforms_dir.glob("*.json"))
    else:
        platforms = [args.target]

    all_warnings: list[str] = []
    for platform in platforms:
        warnings = check_platform(platform)
        all_warnings.extend(warnings)

    if all_warnings:
        print("\nWARNINGS:")
        for w in all_warnings:
            print(w)
        return 1
    else:
        print("\nAll platform keys are properly categorized.")
        return 0
