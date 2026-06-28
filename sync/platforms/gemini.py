from pathlib import Path
from typing import Any

from .common import mcp_servers, read_json_object, write_json

GEMINI_SETTINGS_JSON = Path.home() / ".gemini" / "settings.json"


def sync(data: dict[str, Any]) -> None:
    servers = mcp_servers(data)
    settings = read_json_object(GEMINI_SETTINGS_JSON)
    settings["mcpServers"] = servers
    write_json(GEMINI_SETTINGS_JSON, settings)
    print(f"Replaced MCP servers in {GEMINI_SETTINGS_JSON} (other keys preserved).")
