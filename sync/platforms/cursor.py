from typing import Any

from .common import mcp_servers, merge_object, read_json_object, write_json


def sync(data: dict[str, Any]) -> None:
    from pathlib import Path

    target = Path.home() / ".cursor/mcp.json"
    existing = read_json_object(target)
    existing["mcpServers"] = merge_object(existing.get("mcpServers"), mcp_servers(data))
    write_json(target, existing)
    print(f"Merged Cursor MCP config into {target}.")
