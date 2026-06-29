from pathlib import Path
from typing import Any

from .common import mcp_servers, sync_json_mcp

_TARGET = Path.home() / ".cursor/mcp.json"


def sync(data: dict[str, Any]) -> None:
    sync_json_mcp(_TARGET, mcp_servers(data, "cursor"))
