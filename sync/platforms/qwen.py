"""Sync engine for Qwen Code platform.

Writes DASHSCOPE_API_KEY into ~/.qwen/settings.json env and syncs skills
from ~/.claude/skills/ to ~/.qwen/skills/.
"""
import shutil
from typing import Any

from core.common import read_json_object, write_json
from core.paths import (
    claude_skills_base,
    qwen_root_dir,
    qwen_settings_json_path,
    qwen_skills_base,
)


def _sync_env(env: dict[str, Any]) -> None:
    """Merge managed env vars into ~/.qwen/settings.json.

    Preserves all other keys in the settings file. Only the env
    keys declared in the platform config are overwritten; any
    pre-existing env keys not in the config are left untouched.
    """
    if not env:
        return
    path = qwen_settings_json_path()
    existing = read_json_object(path)
    existing_env = existing.get("env")
    if not isinstance(existing_env, dict):
        existing_env = {}
    merged_env = dict(existing_env)
    merged_env.update(env)
    existing["env"] = merged_env
    write_json(path, existing)
    keys = ", ".join(env.keys())
    print(f"[qwen] Synced env keys to {path}: {keys}.")


def _sync_skills() -> None:
    claude_skills_dir = claude_skills_base()
    qwen_skills_dir = qwen_skills_base()
    if not claude_skills_dir.exists():
        print(f"[qwen] Claude skills directory not found: {claude_skills_dir} — skipping skill sync.")
        return

    qwen_skills_dir.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(claude_skills_dir.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = qwen_skills_dir / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"[qwen] Synced {len(synced)} skills to {qwen_skills_dir}: {', '.join(synced) or '(none)'}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync env vars and skills to Qwen Code.

    Qwen Code does not use MCP servers in the same way as other
    platforms — the mcp_servers parameter is accepted but ignored.
    """
    root = qwen_root_dir()
    if not root.exists():
        print(f"[qwen] Qwen root not found: {root} — skipping (tool not installed).")
        return

    _sync_env(cfg.get("env", {}))
    _sync_skills()
