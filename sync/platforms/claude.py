import copy
from pathlib import Path
from typing import Any

from .common import merge_object, read_json_object, write_json

# ── Path helpers (functions so they respect HOME env var at runtime) ──


def claude_json_path() -> Path:
    return Path.home() / ".claude.json"


def claude_settings_json_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def claude_settings_generated_json_path() -> Path:
    return Path.home() / ".claude" / "settings.generated.json"


def claude_hooks_dir_path() -> Path:
    return Path.home() / ".claude" / "hooks"


def xcode_claude_json_path() -> Path:
    return Path.home() / "Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json"


def _repo_hooks_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "hooks"

# ── Host-specific keys ──
# These keys are kept in env/platforms/claude.json as reference but excluded
# from managed (team-shared) settings — each developer sets them individually.
_HOST_SKIP = {
    # Personal UI/UX preferences
    "apiKeyHelper",
    "theme",
    "tui",
    "editorMode",
    "preferredNotifChannel",
    "statusLine",
    "voice",
    "voiceEnabled",
    "viewMode",
    "prefersReducedMotion",
    "syntaxHighlightingDisabled",
    "terminalProgressBarEnabled",
    "wheelScrollAccelerationEnabled",
    "axScreenReaderRender",
    "showTurnDuration",
    "showThinkingSummaries",
    "showClearContextOnPlanAccept",
    "autoScrollEnabled",
    "spinnerTipsEnabled",
    "spinnerTipsOverride",
    "spinnerVerbs",
    "companyAnnouncements",
    "footerLinksRegexes",
    "language",
    "ultracode",
    "fastModePerSessionOptIn",
    # Host-specific tooling & paths
    "autoConnectIde",
    "autoInstallIdeExtension",
    "externalEditorContext",
    "fileSuggestion",
    "feedbackSurveyRate",
    "cleanupPeriodDays",
    "defaultShell",
    "prUrlTemplate",
    "autoUpdatesChannel",
    "sshConfigs",
    "worktree",
    "plansDirectory",
    "autoMemoryDirectory",
    # Agent / teammate preferences
    "teammateMode",
    "teammateDefaultModel",
    "disableAgentView",
    "agent",
    "agentPushNotifEnabled",
    "inputNeededNotifEnabled",
    "remoteControlAtStartup",
    # Cloud auth helpers (host-specific)
    "awsAuthRefresh",
    "awsCredentialExport",
    "gcpAuthRefresh",
    "otelHeadersHelper",
    # Managed-only keys (only in managed-settings.json, not user settings)
    "claudeMd",
    "claudeMdExcludes",
    "policyHelper",
    # Misc personal
    "skipWebFetchPreflight",
}


def _install_hook_scripts() -> None:
    """Install hook shell scripts from repo hooks/ into ~/.claude/hooks/."""
    repo_dir = _repo_hooks_dir()
    if not repo_dir.exists():
        return
    hooks_dir = claude_hooks_dir_path()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for script in sorted(repo_dir.glob("*.sh")):
        dest = hooks_dir / script.name
        dest.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
        dest.chmod(0o755)
        print(f"Installed hook script: {dest}")


def _expand_hooks(cfg: dict[str, Any]) -> dict[str, Any]:
    """Expand ~ paths in hook command entries from platform config."""
    raw: dict[str, Any] = cfg.get("hooks", {})
    expanded: dict[str, Any] = {}
    for event, entries in raw.items():
        expanded_entries: list[dict[str, Any]] = []
        for entry in entries:
            hooks_list: list[dict[str, Any]] = []
            for hook in entry.get("hooks", []):
                h = dict(hook)
                if "command" in h:
                    h["command"] = str(Path(h["command"]).expanduser())
                hooks_list.append(h)
            expanded_entries.append({**entry, "hooks": hooks_list})
        expanded[event] = expanded_entries
    return expanded


def generate_managed_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    """Generate managed (team-shared) settings dict from platform config.

    Excludes host-specific keys (_HOST_SKIP) and keys handled separately
    (env, hooks, internal keys) so each developer can set those individually.
    """
    managed: dict[str, Any] = {}
    for key, value in cfg.items():
        if key in _HOST_SKIP:
            continue
        if key.startswith("_"):
            continue  # Internal / reference keys (_comment, _hostSettings, etc.)
        if key == "env":
            continue  # Merged separately into settings.json
        if key == "hooks":
            continue  # Handled via _expand_hooks + merge
        if key == "export_env_to_zshrc":
            continue  # Handled by orchestrator
        managed[key] = copy.deepcopy(value)
    return managed


def _sync_xcode_claude_json(servers: dict[str, Any]) -> None:
    """Sync MCP servers into Xcode Claude Agent config."""
    path = xcode_claude_json_path()
    data = read_json_object(path)
    projects = data.get("projects")
    if isinstance(projects, dict) and projects:
        for proj in projects.values():
            if isinstance(proj, dict):
                proj["mcpServers"] = servers
        mode = "per-project"
    else:
        data["mcpServers"] = servers
        mode = "root"
    write_json(path, data)
    print(f"Replaced MCP servers in {path} ({mode}).")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and Claude Code platform config.

    Steps:
      1. Write ~/.claude.json with MCP servers (preserving other top-level keys).
      2. Sync Xcode Claude Agent config.
      3. Generate ~/.claude/settings.generated.json for team-shared settings.
      4. Merge env and hooks into ~/.claude/settings.json.
      5. Install hook shell scripts.
    """
    # ── 1. ~/.claude.json — MCP servers ──
    cj_path = claude_json_path()
    claude = read_json_object(cj_path)
    claude["mcpServers"] = mcp_servers
    write_json(cj_path, claude)
    print(f"Replaced MCP servers in {cj_path} (other top-level config preserved).")

    # ── 2. Xcode Claude Agent ──
    _sync_xcode_claude_json(mcp_servers)

    # ── 3. settings.generated.json — team-shared settings ──
    managed = generate_managed_settings(cfg)
    gen_path = claude_settings_generated_json_path()
    gen_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(gen_path, managed)
    if managed:
        print(f"Wrote {gen_path} ({len(managed)} team-shared keys).")
    else:
        print(f"[claude] No team-shared settings to generate — {gen_path} unchanged.")

    # ── 4. settings.json — merge env and hooks into user settings ──
    settings_path = claude_settings_json_path()
    settings = read_json_object(settings_path)

    # 4a. Merge env
    env = cfg.get("env", {})
    if isinstance(env, dict) and env:
        settings["env"] = merge_object(settings.get("env"), env)
        print(f"Merged env into {settings_path} ({len(env)} vars; other keys preserved).")
    else:
        print("[claude] No env vars in platform config — skipping env merge.")

    # 4b. Install hook scripts
    _install_hook_scripts()

    # 4c. Merge hooks
    config_hooks = _expand_hooks(cfg)
    if config_hooks:
        existing_hooks: dict[str, Any] = settings.get("hooks", {})
        existing_hooks.update(config_hooks)
        settings["hooks"] = existing_hooks
        print(f"Merged hooks into {settings_path} ({len(config_hooks)} event(s)).")

    write_json(settings_path, settings)
