#!/usr/bin/env python3
"""
Merge MCP servers from this repo's mcp-servers.json into Claude Code user config.
Updates only mcpServers; does not overwrite other keys in the config.

Targets:
- ~/.claude.json (terminal / standalone Claude Code)
- ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json
  (Claude Agent inside Xcode: merges into each entry under "projects" -> mcpServers)
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC = REPO_ROOT / "mcp-servers.json"
CLAUDE_JSON = Path.home() / ".claude.json"
XCODE_CLAUDE_JSON = Path.home() / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"


def merge_mcp_servers_dict(existing: dict, servers: dict) -> dict:
    """Same keys from mcp-servers.json overwrite; other keys in existing stay."""
    return {**existing, **servers}


def merge_xcode_claude_json(servers: dict) -> None:
    """Xcode-only Claude Agent config: MCP is stored per project path under \"projects\"."""
    path = XCODE_CLAUDE_JSON
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}

    projects = data.get("projects")
    if isinstance(projects, dict) and projects:
        for proj in projects.values():
            if isinstance(proj, dict):
                proj["mcpServers"] = merge_mcp_servers_dict(proj.get("mcpServers") or {}, servers)
    else:
        data["mcpServers"] = merge_mcp_servers_dict(data.get("mcpServers") or {}, servers)

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Updated MCP servers in {path} "
        f"({'per-project' if isinstance(projects, dict) and projects else 'root'} merge)."
    )


def main():
    if not SRC.exists():
        print(f"Skip Claude sync: {SRC} not found.")
        return
    servers = json.loads(SRC.read_text(encoding="utf-8")).get("mcpServers", {})

    if CLAUDE_JSON.exists():
        data = json.loads(CLAUDE_JSON.read_text(encoding="utf-8"))
    else:
        data = {}

    data["mcpServers"] = merge_mcp_servers_dict(data.get("mcpServers") or {}, servers)

    CLAUDE_JSON.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated MCP servers in {CLAUDE_JSON} (merge, no overwrite of other config).")

    merge_xcode_claude_json(servers)


if __name__ == "__main__":
    main()
