from typing import Any

from .common import mcp_servers, read_json_object, write_json


def sync(data: dict[str, Any]) -> None:
    from pathlib import Path

    target = Path.home() / ".cursor/mcp.json"
    if target.is_symlink():
        target.unlink()
    existing = read_json_object(target)
    existing["mcpServers"] = mcp_servers(data)
    write_json(target, existing)
    print(f"Replaced Cursor MCP config in {target}.")
