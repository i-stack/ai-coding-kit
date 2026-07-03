from pathlib import Path
from typing import Any

from .common import merge_object, read_json_object, write_json

CLAUDE_JSON = Path.home() / ".claude.json"
CLAUDE_SETTINGS_JSON = Path.home() / ".claude" / "settings.json"
CLAUDE_HOOKS_DIR = Path.home() / ".claude" / "hooks"
XCODE_CLAUDE_JSON = Path.home() / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"
REPO_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"


def _install_hook_scripts() -> None:
    if not REPO_HOOKS_DIR.exists():
        return
    CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for script in sorted(REPO_HOOKS_DIR.glob("*.sh")):
        dest = CLAUDE_HOOKS_DIR / script.name
        dest.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
        dest.chmod(0o755)
        print(f"Installed hook script: {dest}")


def _expand_hooks(cfg: dict[str, Any]) -> dict[str, Any]:
    raw: dict[str, Any] = cfg.get("hooks", {})
    expanded: dict[str, Any] = {}
    for event, entries in raw.items():
        expanded_entries = []
        for entry in entries:
            hooks_list = []
            for hook in entry.get("hooks", []):
                h = dict(hook)
                if "command" in h:
                    h["command"] = str(Path(h["command"]).expanduser())
                hooks_list.append(h)
            expanded_entries.append({**entry, "hooks": hooks_list})
        expanded[event] = expanded_entries
    return expanded


def _sync_xcode_claude_json(servers: dict[str, Any]) -> None:
    data = read_json_object(XCODE_CLAUDE_JSON)
    projects = data.get("projects")
    if isinstance(projects, dict) and projects:
        for proj in projects.values():
            if isinstance(proj, dict):
                proj["mcpServers"] = servers
        mode = "per-project"
    else:
        data["mcpServers"] = servers
        mode = "root"
    write_json(XCODE_CLAUDE_JSON, data)
    print(f"Replaced MCP servers in {XCODE_CLAUDE_JSON} ({mode}).")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and Claude platform config."""
    # Write ~/.claude.json
    claude = read_json_object(CLAUDE_JSON)
    claude["mcpServers"] = mcp_servers
    write_json(CLAUDE_JSON, claude)
    print(f"Replaced MCP servers in {CLAUDE_JSON} (other top-level config preserved).")

    # Xcode Claude Agent
    _sync_xcode_claude_json(mcp_servers)

    # Write ~/.claude/settings.json
    settings = read_json_object(CLAUDE_SETTINGS_JSON)

    env = cfg.get("env", {})
    if isinstance(env, dict) and env:
        settings["env"] = merge_object(settings.get("env"), env)
        print(f"Merged env into {CLAUDE_SETTINGS_JSON} ({len(env)} vars; other keys preserved).")
    else:
        print(f"[claude] No env vars in platform config — skipping env merge.")

    # Install hook scripts
    _install_hook_scripts()

    # Merge hooks from platform config
    config_hooks = _expand_hooks(cfg)
    if config_hooks:
        existing_hooks: dict[str, Any] = settings.get("hooks", {})
        existing_hooks.update(config_hooks)
        settings["hooks"] = existing_hooks
        print(f"Merged hooks into {CLAUDE_SETTINGS_JSON} ({len(config_hooks)} event(s)).")

    write_json(CLAUDE_SETTINGS_JSON, settings)
