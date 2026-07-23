from typing import Any

from core.common import sync_json_mcp
from core.paths import cursor_mcp_path


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Write MCP servers to ~/.cursor/mcp.json."""
    sync_json_mcp(cursor_mcp_path(), mcp_servers)
