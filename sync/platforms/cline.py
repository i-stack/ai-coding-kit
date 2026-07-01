import shutil
from pathlib import Path
from typing import Any

from .common import mcp_servers, read_json_object, write_json

_STORAGE_SUFFIX = "saoudrizwan.claude-dev/settings/cline_mcp_settings.json"

# Cline can be installed in any of these editors; sync to all that are present.
_CANDIDATE_MCP_PATHS = [
    Path.home() / f"Library/Application Support/{editor}/User/globalStorage/{_STORAGE_SUFFIX}"
    for editor in ("Cursor", "Code", "Code - Insiders")
]

CLINE_SKILLS_DIR = Path.home() / ".cline" / "skills"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _sync_mcp(servers: dict[str, Any]) -> None:
    targets = [p for p in _CANDIDATE_MCP_PATHS if p.parent.exists()]
    if not targets:
        print("[cline] No Cline MCP settings directory found (checked Cursor, Code, Code - Insiders).")
        return
    for path in targets:
        data = read_json_object(path)
        data["mcpServers"] = servers
        write_json(path, data)
        print(f"Replaced MCP servers in {path}.")


def _sync_skills() -> None:
    if not CLAUDE_SKILLS_DIR.exists():
        print(f"[cline] Claude skills directory not found: {CLAUDE_SKILLS_DIR} — skipping skill sync.")
        return

    CLINE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(CLAUDE_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = CLINE_SKILLS_DIR / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {CLINE_SKILLS_DIR}: {', '.join(synced) or '(none)'}.")


def sync(data: dict[str, Any]) -> None:
    _sync_mcp(mcp_servers(data, "cline"))
    _sync_skills()
