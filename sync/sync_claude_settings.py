#!/usr/bin/env python3
"""
Merge env vars from this repo's env/claude/settings.shared.json into Claude Code's
~/.claude/settings.json. Replaces only the "env" key; all other keys
(permissions, hooks, theme, ...) are preserved.

This enables single-source management of Claude Code environment variables
(ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, model mappings, etc.) at the
repository level, synced on demand via sync_all.sh.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "env" / "claude" / "settings.shared.json"
SETTINGS_JSON = Path.home() / ".claude" / "settings.json"


def main():
    if not SRC.exists():
        print(f"Skip Claude settings sync: {SRC} not found.")
        return

    shared_env = json.loads(SRC.read_text(encoding="utf-8"))
    if not isinstance(shared_env, dict):
        print(f"ERROR: {SRC} must contain a JSON object (env dict), got {type(shared_env).__name__}.")
        return

    if SETTINGS_JSON.exists():
        data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    else:
        data = {}
        print(f"NOTE: {SETTINGS_JSON} does not exist yet; creating it.")

    data["env"] = dict(shared_env)

    SETTINGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Updated env in {SETTINGS_JSON} "
        f"({len(shared_env)} vars replaced; other keys preserved)."
    )


if __name__ == "__main__":
    main()