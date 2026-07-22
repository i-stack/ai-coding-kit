import copy
from pathlib import Path
from typing import Any

from core.common import (
    merge_object,
    prune_managed_keys_via_sidecar,
    read_json_object,
    write_json,
)
from core.paths import (
    claude_config_json_path,
    claude_hooks_dir_path,
    claude_json_path,
    claude_root_dir,
    claude_settings_json_path,
    xcode_coding_assistant_exists,
    xcode_claude_dir,
    xcode_claude_json_path,
)

# ── Path helpers (re-exported for backward compatibility) ──


def claude_settings_generated_json_path() -> Path:
    return Path.home() / ".claude" / "settings.generated.json"


def _repo_hooks_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "hooks"

# ── Host-specific keys ──
# These keys are kept in env/platforms/claude.json as reference but excluded
# from managed (team-shared) settings — each developer sets them individually.
_HOST_SKIP = {
    # Sync-engine metadata (declared in env/platforms/<platform>.json, not a tool setting)
    "preamble",
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


def _sync_xcode_claude_settings(
    managed: dict[str, Any], env: dict[str, Any], hooks: dict[str, Any]
) -> None:
    """Sync team-shared settings, env, and hooks to Xcode Claude Agent dir."""
    xc_dir = xcode_claude_dir()
    xc_dir.mkdir(parents=True, exist_ok=True)
    _remove_obsolete_generated_settings(xc_dir / "settings.generated.json")

    if managed:
        print(f"Prepared Xcode Claude settings ({len(managed)} team-shared keys).")

    # Merge env and hooks into Xcode settings.json
    settings_path = xc_dir / "settings.json"
    settings = read_json_object(settings_path)

    if managed:
        settings = merge_object(settings, managed)

    if isinstance(env, dict) and env:
        settings["env"] = merge_object(settings.get("env"), env)
        print(f"Merged env into Xcode {settings_path} ({len(env)} vars).")

    if hooks:
        existing = settings.get("hooks", {})
        existing.update(hooks)
        settings["hooks"] = existing
        print(f"Merged hooks into Xcode {settings_path} ({len(hooks)} event(s)).")

    write_json(settings_path, settings)

    # Sidecar recovery for Xcode Claude Agent settings (same mechanism).
    prune_managed_keys_via_sidecar(
        settings_path,
        set(managed.keys()),
        xc_dir / ".managed_settings_keys.json",
    )


def _remove_obsolete_generated_settings(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"Removed obsolete generated settings file: {path}")


def _sync_claude_config() -> None:
    """Force Claude Code to use the self-managed primary API key path."""
    path = claude_config_json_path()
    config = read_json_object(path)
    config["primaryApiKey"] = "self"
    write_json(path, config)
    print(f"Set primaryApiKey in {path}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and Claude Code platform config.

    Steps:
      1. Write ~/.claude.json with MCP servers (preserving other top-level keys).
      2. Sync MCP servers to Xcode Claude Agent (.claude.json).
      3. Set ~/.claude/config.json primaryApiKey to self.
      4. Merge team-shared settings, env, and hooks into ~/.claude/settings.json.
      5. Sync team-shared settings, env, and hooks to Xcode Claude Agent.
      6. Install hook shell scripts.
    """
    root = claude_root_dir()
    if not root.exists():
        print(f"[claude] Claude root not found: {root} — skipping (tool not installed).")
        return

    # ── 1. ~/.claude.json — MCP servers ──
    cj_path = claude_json_path()
    claude = read_json_object(cj_path)
    claude["mcpServers"] = mcp_servers
    write_json(cj_path, claude)
    print(f"Replaced MCP servers in {cj_path} (other top-level config preserved).")

    xcode_available = xcode_coding_assistant_exists()
    if xcode_available:
        # ── 2. Xcode Claude Agent ──
        _sync_xcode_claude_json(mcp_servers)
    else:
        print("[claude] Xcode CodingAssistant path not found — skipping Xcode Claude sync.")

    # ── 3. config.json — avoid Claude Code login prompt with third-party API ──
    _sync_claude_config()

    # ── 4. settings.json — merge team-shared settings, env, and hooks ──
    managed = generate_managed_settings(cfg)
    _remove_obsolete_generated_settings(claude_settings_generated_json_path())
    if managed:
        print(f"Prepared Claude settings ({len(managed)} team-shared keys).")
    else:
        print("[claude] No team-shared settings in platform config.")

    settings_path = claude_settings_json_path()
    settings = read_json_object(settings_path)

    if managed:
        settings = merge_object(settings, managed)

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

    # ── 4e. Sidecar recovery: prune managed keys dropped from the config ──
    # Records which team-shared top-level keys we manage so a key removed from
    # claude.json is cleaned up on the next sync instead of lingering in the
    # developer's ~/.claude/settings.json.
    # Universal payloads (mcpServers/env/hooks) are NOT tracked here, so they
    # are never pruned.
    prune_managed_keys_via_sidecar(
        settings_path,
        set(managed.keys()),
        claude_root_dir() / ".managed_settings_keys.json",
    )

    if xcode_available:
        # ── 5. Xcode Claude Agent — settings ──
        _sync_xcode_claude_settings(managed, env, config_hooks)
