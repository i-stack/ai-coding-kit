from pathlib import Path
from typing import Any

import os

from core.common import (
    api_enabled as _api_enabled,
    load_secrets,
    merge_managed_dict,
    prune_managed_keys_via_sidecar,
    read_json_object,
    resolve_secrets,
    write_json,
)
from core.paths import (
    gemini_root_dir,
    gemini_settings_path,
    xcode_coding_assistant_exists,
    xcode_gemini_dir,
    xcode_gemini_dotgemini_dir,
    xcode_gemini_env_path,
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
    existing_mcp = merged.get("mcpServers")
    merged["mcpServers"] = merge_managed_dict(
        existing_mcp if isinstance(existing_mcp, dict) else {}, mcp_servers
    )
    write_json(path, merged)
    print(f"Synced Gemini settings to {path}.")
    prune_managed_keys_via_sidecar(path, set(managed_settings.keys()), sidecar_path)


def _ensure_gemini_md_symlink(dotgemini: Path) -> None:
    """Step 3: symlink ~/.gemini/GEMINI.md into the Xcode .gemini dir.

    A symlink (rather than a copy) keeps a single source of truth: edits to the
    user's ~/.gemini/GEMINI.md propagate automatically. We gracefully handle an
    existing symlink (refresh target), an existing real file (leave it untouched
    unless it already points at the source), and a missing source (warn + skip).
    """
    source = gemini_root_dir() / "GEMINI.md"
    if not source.exists():
        print("[gemini] ~/.gemini/GEMINI.md not found — skipping GEMINI.md symlink for Xcode.")
        return
    link = dotgemini / "GEMINI.md"
    # Already a correct symlink to the source: nothing to do.
    if link.is_symlink() and os.path.realpath(link) == os.path.realpath(source):
        return
    # Replace any existing file/symlink at the target.
    if link.exists() or link.is_symlink():
        link.unlink()
    os.symlink(source, link)
    print(f"[gemini] Symlinked GEMINI.md -> {link} (source: {source}).")


def _sync_xcode_env_file(dotgemini: Path, cfg: dict[str, Any]) -> None:
    """Step 4: create .env in the Xcode .gemini dir from export_env_to_zshrc.

    The platform config's ``export_env_to_zshrc`` block holds {VAR: value} pairs
    (values may contain ${secret} placeholders). We resolve placeholders against
    env/secrets.json, then write/merge them into the .env file as KEY="value"
    lines. Existing lines NOT managed by the sync (any other keys) are preserved.
    """
    export = cfg.get("export_env_to_zshrc")
    if not isinstance(export, dict) or not export:
        print("[gemini] No export_env_to_zshrc block — skipping .env for Xcode.")
        return

    secrets = load_secrets()
    resolved = resolve_secrets(export, secrets)
    unresolved = [v for v in resolved.values() if isinstance(v, str) and "${" in v]
    if unresolved:
        print("[gemini] ⚠ .env: unresolved placeholders remain — check env/secrets.json.")

    env_path = dotgemini / ".env"
    existing: dict[str, str] = {}
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            existing[key.strip()] = val.strip().strip('"').strip("'")

    # Overlay managed vars on top of any developer-customized ones.
    merged = dict(existing)
    for k, v in resolved.items():
        if isinstance(v, str):
            merged[k] = v

    lines = [f'{k}="{v}"' for k, v in merged.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[gemini] Synced .env for Xcode at {env_path} ({len(merged)} vars).")


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

    # ── Steps 2-4: nested .gemini dir, GEMINI.md symlink, .env ──
    dotgemini = xcode_gemini_dotgemini_dir()
    dotgemini.mkdir(parents=True, exist_ok=True)  # step 2
    _ensure_gemini_md_symlink(dotgemini)          # step 3
    _sync_xcode_env_file(dotgemini, cfg)          # step 4
