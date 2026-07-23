from pathlib import Path
from typing import Any

from core.common import (
    api_enabled as _api_enabled,
    prune_managed_keys_via_sidecar,
    read_json_object,
    write_json,
)
from core.paths import (
    gemini_root_dir,
    gemini_settings_path,
    xcode_coding_assistant_exists,
    xcode_gemini_dir,
)

# Internal/platform keys that should NOT appear in the managed settings.json.
# These are consumed by the sync engine/orchestrator, not by Gemini CLI itself.
_INTERNAL_SKIP = {"export_env_to_zshrc", "_comment", "preamble", "api"}

# Keys owned by the syncer that are gated by the local api.enabled toggle.
# When API sync is disabled, these API/model fields are neither written nor
# merged, and are pruned from the target via the managed-keys sidecar.
_API_MODEL_FIELDS = {"model"}


def _extract_settings(cfg: dict[str, Any], api_enabled: bool = True) -> dict[str, Any]:
    """Extract Gemini CLI settings from platform config, stripping internal keys.

    When ``api_enabled`` is False, API/model-owned fields (e.g. ``model``) are
    also excluded so they are neither merged nor left lingering in settings.json.
    """
    skip = set(_INTERNAL_SKIP)
    if not api_enabled:
        skip |= _API_MODEL_FIELDS
    return {k: v for k, v in cfg.items() if k not in skip}


def _deep_merge(existing: dict[str, Any], managed: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge managed settings into existing, preserving per-developer customizations.

    Dict values are merged recursively, with managed values overriding existing
    values at the same path. This lets developers keep custom sibling keys
    inside nested Gemini settings objects while the shared config still wins
    for managed fields.
    """
    result = dict(existing)
    for key, value in managed.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _sync_settings(
    path: Path,
    managed_settings: dict[str, Any],
    mcp_servers: dict[str, Any],
    sidecar_path: Path,
) -> None:
    """Write managed settings + MCP servers into a Gemini settings.json target.

    Preserves any developer-added keys by deep-merging managed settings
    on top of the existing file. A sidecar at ``sidecar_path`` records which
    top-level keys are managed, so a key dropped from the config is pruned on
    the next sync.
    """
    existing = read_json_object(path)
    merged = _deep_merge(existing, managed_settings)
    merged["mcpServers"] = mcp_servers
    write_json(path, merged)
    print(f"Synced Gemini settings to {path}.")
    prune_managed_keys_via_sidecar(path, set(managed_settings.keys()), sidecar_path)


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and platform config to Gemini CLI (native + Xcode).

    Writes to:
      - ~/.gemini/settings.json          (Gemini CLI native config)
      - ~/Library/Developer/Xcode/CodingAssistant/gemini/settings.json  (Xcode target)

    Environment variables (GEMINI_API_KEY, GOOGLE_GEMINI_BASE_URL) are exported
    to ~/.zshrc by the orchestrator via the export_env_to_zshrc mechanism
    defined in env/platforms/gemini.json.
    """
    root = gemini_root_dir()
    if not root.exists():
        print(f"[gemini] Gemini root not found: {root} — skipping (tool not installed).")
        return

    api_enabled = _api_enabled(cfg)
    managed = _extract_settings(cfg, api_enabled)

    # ── Native Gemini CLI target ──
    _sync_settings(
        gemini_settings_path(),
        managed,
        mcp_servers,
        gemini_root_dir() / ".managed_settings_keys.json",
    )

    # ── Xcode CodingAssistant target ──
    if not xcode_coding_assistant_exists():
        print("[gemini] Xcode CodingAssistant path not found — skipping Xcode Gemini sync.")
        return

    xc = xcode_gemini_dir()
    xc.mkdir(parents=True, exist_ok=True)
    _sync_settings(
        xc / "settings.json",
        managed,
        mcp_servers,
        xc / ".managed_settings_keys.json",
    )
