from pathlib import Path
from typing import Any

from .common import sync_env_to_zshrc, sync_json_mcp

_TARGET = Path.home() / ".gemini/settings.json"


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and env vars to Gemini CLI."""
    sync_json_mcp(_TARGET, mcp_servers)
    env = cfg.get("env", {})
    if isinstance(env, dict) and env:
        sync_env_to_zshrc("gemini", env)
