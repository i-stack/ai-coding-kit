from pathlib import Path
from typing import Any

from .common import env_for_platform, mcp_servers, merge_object, read_json_object, write_json

CLAUDE_JSON = Path.home() / ".claude.json"
CLAUDE_SETTINGS_JSON = Path.home() / ".claude" / "settings.json"
XCODE_CLAUDE_JSON = Path.home() / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"


def sync_xcode_claude_json(servers: dict[str, Any]) -> None:
    data = read_json_object(XCODE_CLAUDE_JSON)
    projects = data.get("projects")
    if isinstance(projects, dict) and projects:
        for proj in projects.values():
            if isinstance(proj, dict):
                proj["mcpServers"] = merge_object(proj.get("mcpServers"), servers)
        mode = "per-project"
    else:
        data["mcpServers"] = merge_object(data.get("mcpServers"), servers)
        mode = "root"
    write_json(XCODE_CLAUDE_JSON, data)
    print(f"Merged MCP servers into {XCODE_CLAUDE_JSON} ({mode}).")


def sync(data: dict[str, Any]) -> None:
    servers = mcp_servers(data)
    claude = read_json_object(CLAUDE_JSON)
    claude["mcpServers"] = merge_object(claude.get("mcpServers"), servers)
    write_json(CLAUDE_JSON, claude)
    print(f"Merged MCP servers into {CLAUDE_JSON} (other top-level config preserved).")

    sync_xcode_claude_json(servers)

    env = env_for_platform(data, "claude")
    settings = read_json_object(CLAUDE_SETTINGS_JSON)
    settings["env"] = merge_object(settings.get("env"), env)
    write_json(CLAUDE_SETTINGS_JSON, settings)
    print(f"Merged env into {CLAUDE_SETTINGS_JSON} ({len(env)} vars; other keys preserved).")
