from pathlib import Path
from typing import Any

from .common import filter_mcp_for_platform, load_all_mcp, load_platform_config, sync_json_mcp

_TARGET = Path.home() / ".cursor/mcp.json"


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Write MCP servers to ~/.cursor/mcp.json."""
    sync_json_mcp(_TARGET, mcp_servers)
