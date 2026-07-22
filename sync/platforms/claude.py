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


_API_SIDECAR = ".managed_api_fields.json"


def _api_enabled(cfg: dict[str, Any]) -> bool:
    api = cfg.get("api")
    if not isinstance(api, dict):
        return True
    return api.get("enabled", True) is True

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
        if key == "api":
            continue  # Engine-handled third-party API toggle
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
    managed: dict[str, Any],
    env: dict[str, Any],
    hooks: dict[str, Any],
    api_enabled: bool,
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

    _apply_api_env(
        settings,
        env,
        xc_dir / _API_SIDECAR,
        api_enabled,
        f"Xcode {settings_path}",
    )

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


def _read_api_record(sidecar_path: Path) -> dict[str, set[str]]:
    raw = read_json_object(sidecar_path)
    return {
        "settingsEnvKeys": set(raw.get("settingsEnvKeys", [])),
        "configKeys": set(raw.get("configKeys", [])),
    }


def _write_api_record(sidecar_path: Path, record: dict[str, set[str]]) -> None:
    write_json(
        sidecar_path,
        {
            "settingsEnvKeys": sorted(record.get("settingsEnvKeys", set())),
            "configKeys": sorted(record.get("configKeys", set())),
        },
    )


def _prune_env_keys(settings: dict[str, Any], keys: set[str]) -> None:
    env = settings.get("env")
    if not isinstance(env, dict):
        return
    for key in keys:
        env.pop(key, None)
    if env:
        settings["env"] = env
    else:
        settings.pop("env", None)


def _apply_api_env(
    settings: dict[str, Any],
    env: dict[str, Any],
    sidecar_path: Path,
    api_enabled: bool,
    label: str,
) -> None:
    """Apply or clean Claude third-party API env vars in a settings dict."""
    api_env = env if isinstance(env, dict) else {}
    current_keys = set(api_env)
    record = _read_api_record(sidecar_path)
    previous_keys = record["settingsEnvKeys"]

    if api_enabled and api_env:
        stale = previous_keys - current_keys
        if stale:
            _prune_env_keys(settings, stale)
        settings["env"] = merge_object(settings.get("env"), api_env)
        record["settingsEnvKeys"] = current_keys
        _write_api_record(sidecar_path, record)
        print(f"Merged API env into {label} ({len(api_env)} vars).")
        return

    stale = previous_keys | current_keys
    if stale:
        _prune_env_keys(settings, stale)
    if previous_keys or sidecar_path.exists():
        record["settingsEnvKeys"] = set()
        _write_api_record(sidecar_path, record)
    if api_enabled:
        print(f"[claude] No API env configured for {label} — cleaned stale managed API env vars.")
    else:
        print(f"[claude] API env disabled for {label} — cleaned managed API env vars.")


def _sync_claude_config(api_enabled: bool) -> None:
    """Set or clean Claude Code's self-managed primary API key path."""
    path = claude_config_json_path()
    config = read_json_object(path)
    sidecar_path = claude_root_dir() / _API_SIDECAR
    record = _read_api_record(sidecar_path)

    if api_enabled:
        config["primaryApiKey"] = "self"
        record["configKeys"].add("primaryApiKey")
        write_json(path, config)
        _write_api_record(sidecar_path, record)
        print(f"Set primaryApiKey in {path}.")
        return

    if config.get("primaryApiKey") == "self":
        config.pop("primaryApiKey", None)
        write_json(path, config)
        print(f"Removed managed primaryApiKey from {path}.")
    if record["configKeys"] or sidecar_path.exists():
        record["configKeys"].discard("primaryApiKey")
        _write_api_record(sidecar_path, record)


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
    api_enabled = _api_enabled(cfg)

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

    # ── 3. config.json — third-party API path, gated by local api.enabled ──
    _sync_claude_config(api_enabled)

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

    # 4a. Merge or clean API env
    env = cfg.get("env", {})
    _apply_api_env(
        settings,
        env,
        claude_root_dir() / _API_SIDECAR,
        api_enabled,
        str(settings_path),
    )

    # 4b. Merge hooks
    config_hooks = _expand_hooks(cfg)
    if config_hooks:
        _install_hook_scripts()
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
        _sync_xcode_claude_settings(managed, env, config_hooks, api_enabled)
