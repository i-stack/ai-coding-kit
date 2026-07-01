import shutil
from pathlib import Path
from typing import Any

from .common import mcp_servers, platform_config, read_json_object, sync_json_mcp, write_json

MCP_TARGET = Path.home() / ".codebuddy" / "mcp.json"
MODELS_TARGET = Path.home() / ".codebuddy" / "models.json"
CODEBUDDY_SKILLS_DIR = Path.home() / ".codebuddy" / "skills"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _sync_models(data: dict[str, Any]) -> None:
    cfg = platform_config(data, "codebuddy")
    models = cfg.get("models")
    available_models = cfg.get("availableModels")

    if models is None and available_models is None:
        print("[codebuddy] No models config found — skipping model sync.")
        return

    existing = read_json_object(MODELS_TARGET)
    if models is not None:
        existing["models"] = models
    if available_models is not None:
        existing["availableModels"] = available_models
    write_json(MODELS_TARGET, existing)
    print(f"Replaced models in {MODELS_TARGET}.")


def _sync_skills() -> None:
    if not CLAUDE_SKILLS_DIR.exists():
        print(f"[codebuddy] Claude skills directory not found: {CLAUDE_SKILLS_DIR} — skipping skill sync.")
        return

    CODEBUDDY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(CLAUDE_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = CODEBUDDY_SKILLS_DIR / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {CODEBUDDY_SKILLS_DIR}: {', '.join(synced) or '(none)'}.")


def sync(data: dict[str, Any]) -> None:
    sync_json_mcp(MCP_TARGET, mcp_servers(data, "codebuddy"))
    _sync_models(data)
    _sync_skills()