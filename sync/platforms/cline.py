import shutil
from typing import Any

from .common import read_json_object, write_json
from .paths import claude_skills_base, cline_mcp_candidate_paths, cline_skills_base


def _sync_mcp(servers: dict[str, Any]) -> None:
    targets = [p for p in cline_mcp_candidate_paths() if p.parent.exists()]
    if not targets:
        print("[cline] No Cline MCP settings directory found (checked Cursor, Code, Code - Insiders).")
        return
    for path in targets:
        data = read_json_object(path)
        data["mcpServers"] = servers
        write_json(path, data)
        print(f"Replaced MCP servers in {path}.")


def _sync_skills() -> None:
    claude_skills_dir = claude_skills_base()
    cline_skills_dir = cline_skills_base()
    if not claude_skills_dir.exists():
        print(f"[cline] Claude skills directory not found: {claude_skills_dir} — skipping skill sync.")
        return

    cline_skills_dir.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(claude_skills_dir.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = cline_skills_dir / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {cline_skills_dir}: {', '.join(synced) or '(none)'}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and skills to Cline (VSCode extension)."""
    _sync_mcp(mcp_servers)
    _sync_skills()
