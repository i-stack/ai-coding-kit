from pathlib import Path
from typing import Any

from .common import gemini_settings_path, read_json_object, write_json, xcode_gemini_dir

# Internal/platform keys that should NOT appear in the managed settings.json.
# These are consumed by the sync engine/orchestrator, not by Gemini CLI itself.
_INTERNAL_SKIP = {"export_env_to_zshrc", "_comment"}


def _extract_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract Gemini CLI settings from platform config, stripping internal keys."""
    return {k: v for k, v in cfg.items() if k not in _INTERNAL_SKIP}


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


def _sync_settings(path: Path, managed_settings: dict[str, Any], mcp_servers: dict[str, Any]) -> None:
    """Write managed settings + MCP servers into a Gemini settings.json target.

    Preserves any developer-added keys by deep-merging managed settings
    on top of the existing file.
    """
    existing = read_json_object(path)
    merged = _deep_merge(existing, managed_settings)
    merged["mcpServers"] = mcp_servers
    write_json(path, merged)
    print(f"Synced Gemini settings to {path}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and platform config to Gemini CLI (native + Xcode).

    Writes to:
      - ~/.gemini/settings.json          (Gemini CLI native config)
      - ~/Library/Developer/Xcode/CodingAssistant/gemini/settings.json  (Xcode target)

    Environment variables (GEMINI_API_KEY, GOOGLE_GEMINI_BASE_URL) are exported
    to ~/.zshrc by the orchestrator via the export_env_to_zshrc mechanism
    defined in env/platforms/gemini.json.
    """
    managed = _extract_settings(cfg)

    # ── Native Gemini CLI target ──
    _sync_settings(gemini_settings_path(), managed, mcp_servers)

    # ── Xcode CodingAssistant target ──
    xc = xcode_gemini_dir()
    xc.mkdir(parents=True, exist_ok=True)
    _sync_settings(xc / "settings.json", managed, mcp_servers)
