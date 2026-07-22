"""Sync engine for Qwen Code platform.

Mirrors ``~/.qwen/settings.json``: writes the managed top-level fields
``security`` / ``modelProviders`` / ``model`` and ``env`` into
``~/.qwen/settings.json``, and copies skills from ``~/.claude/skills/`` to
``~/.qwen/skills/``.

Model definitions (``~/.qwen/models.json``) are **not** managed by this syncer
— Qwen owns that file directly.

API fields are gated by ``api.enabled`` (missing ``api`` block defaults to
enabled). When ``api.enabled=false``:
- the managed ``env`` key is removed;
- the managed ``security`` / ``modelProviders`` / ``model`` fields are removed
  (ownership-aware — ``modelProviders`` entries are merged/cleaned per ``id``).

``$version`` is a Qwen-internal marker and is **never** written or overwritten
by the syncer — every write reads the existing file and merges only owned keys.
"""
import shutil
from typing import Any

from core.common import read_json_object, write_json
from core.paths import (
    claude_skills_base,
    qwen_root_dir,
    qwen_settings_json_path,
    qwen_skills_base,
)

# Top-level qwen.json keys that map into ~/.qwen/settings.json.
SETTINGS_KEYS = ("security", "modelProviders", "model")


def _api_enabled(cfg: dict[str, Any]) -> bool:
    """Qwen third-party API sync toggle.

    Like Claude and CodeBuddy, a missing ``api`` block or missing
    ``api.enabled`` defaults to enabled so the historical always-sync behavior
    is preserved. Only an explicit ``false`` disables synced API fields
    (``env`` and the ``security`` / ``modelProviders`` / ``model`` fields).
    """
    api = cfg.get("api")
    if not isinstance(api, dict):
        return True
    return api.get("enabled", True) is True


def _merge_model_entries(
    existing_entries: list[Any], config_entries: list[dict[str, Any]]
) -> list[Any]:
    """Merge config-managed model-provider entries into existing entries by id.

    - Config-managed entries (identified by ``id``) appear first in config order.
    - Existing entries with the same id are silently updated (config wins).
    - User-added entries not in config are preserved after config entries.
    - Non-dict entries with no id are preserved at the very end.
    """
    if not config_entries:
        return existing_entries

    config_by_id: dict[str, dict[str, Any]] = {}
    for m in config_entries:
        if isinstance(m, dict) and "id" in m:
            config_by_id[m["id"]] = m

    result: list[Any] = []

    # Config-managed entries first (in config order)
    for m in config_entries:
        if isinstance(m, dict) and "id" in m:
            result.append(m)

    # User-added entries from existing (not in config), preserving order
    for m in existing_entries:
        if not isinstance(m, dict) or "id" not in m:
            continue
        mid = m["id"]
        if mid not in config_by_id:
            result.append(m)

    # Trailing nonstandard entries
    for m in existing_entries:
        if not isinstance(m, dict) or "id" not in m:
            result.append(m)

    return result


def _merge_settings_block(existing: dict[str, Any], config_block: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge the managed settings fields into existing settings.json.

    - ``modelProviders`` is merged per-provider-type by entry ``id`` (config
      wins; user entries preserved).
    - ``security`` and ``model`` are owned by the config (replaced wholesale).
    - ``$version`` and any other existing top-level key are preserved.
    """
    result = dict(existing)

    for key, value in config_block.items():
        if key == "$version":
            # Qwen-internal marker — never managed by the syncer.
            continue
        if key == "modelProviders" and isinstance(value, dict):
            existing_mp = existing.get("modelProviders")
            if not isinstance(existing_mp, dict):
                existing_mp = {}
            new_mp = dict(existing_mp)
            for provider, entries in value.items():
                if not isinstance(entries, list):
                    continue
                existing_entries = existing_mp.get(provider)
                if not isinstance(existing_entries, list):
                    existing_entries = []
                new_mp[provider] = _merge_model_entries(existing_entries, entries)
            result["modelProviders"] = new_mp
        else:
            result[key] = value

    return result


def _clean_settings_block(existing: dict[str, Any], config_block: dict[str, Any]) -> bool:
    """Ownership-aware removal of managed settings fields.

    Returns True when any managed field was actually removed. ``$version`` and
    unrelated user keys are never touched.
    """
    removed = False

    mp = existing.get("modelProviders")
    config_mp = config_block.get("modelProviders")
    if isinstance(mp, dict) and isinstance(config_mp, dict):
        new_mp: dict[str, Any] = {}
        for provider, entries in mp.items():
            if not isinstance(entries, list):
                new_mp[provider] = entries
                continue
            config_ids = {
                e["id"]
                for e in config_mp.get(provider, [])
                if isinstance(e, dict) and "id" in e
            }
            kept = [
                e
                for e in entries
                if not (isinstance(e, dict) and e.get("id") in config_ids)
            ]
            if kept:
                new_mp[provider] = kept
            else:
                removed = True  # provider fully removed
        if new_mp != mp:
            removed = True
        if new_mp:
            existing["modelProviders"] = new_mp
        else:
            existing.pop("modelProviders", None)

    for key in ("model", "security"):
        if key in config_block and key in existing:
            del existing[key]
            removed = True

    return removed


def _sync_env(env: dict[str, Any], api_enabled: bool) -> None:
    """Merge or clean managed env vars in ~/.qwen/settings.json.

    When ``api_enabled`` is true, the env keys declared in the platform config
    are merged into the settings ``env`` object; other keys (including
    ``$version``) are preserved.

    When ``api_enabled`` is false, only the env keys the syncer manages are
    removed (ownership-aware cleanup) — never unrelated user keys.
    """
    if not env:
        return
    path = qwen_settings_json_path()
    existing = read_json_object(path)
    existing_env = existing.get("env")
    if not isinstance(existing_env, dict):
        existing_env = {}

    if api_enabled:
        merged_env = dict(existing_env)
        merged_env.update(env)
        existing["env"] = merged_env
        write_json(path, existing)
        keys = ", ".join(env.keys())
        print(f"[qwen] Synced env keys to {path}: {keys}.")
        return

    # API sync disabled: remove only the env keys we manage.
    removed = False
    new_env = dict(existing_env)
    for key in env:
        if key in new_env:
            del new_env[key]
            removed = True
    if removed:
        if new_env:
            existing["env"] = new_env
        else:
            existing.pop("env", None)
        write_json(path, existing)
        print(
            f"[qwen] API sync disabled — removed managed env keys from {path}: "
            f"{', '.join(env.keys())}."
        )
    else:
        print("[qwen] API sync disabled — no managed env keys to clean.")


def _sync_settings_block(cfg: dict[str, Any], api_enabled: bool) -> None:
    """Merge or clean the managed settings fields in ~/.qwen/settings.json.

    The fields (``security`` / ``modelProviders`` / ``model``) are owned by the
    config and gated by ``api.enabled``. ``$version`` is always preserved.

    When ``api_enabled`` is false, the managed fields are removed (ownership-
    aware) so the provider config no longer drives Qwen; re-enabling restores
    them.
    """
    settings_block = {k: cfg[k] for k in SETTINGS_KEYS if k in cfg}
    if not settings_block:
        # No managed settings fields: nothing to merge or clean.
        return

    path = qwen_settings_json_path()
    existing = read_json_object(path)

    if api_enabled:
        merged = _merge_settings_block(existing, settings_block)
        write_json(path, merged)
        print(f"[qwen] Synced settings to {path} (security/modelProviders/model).")
        return

    # API sync disabled: remove only the managed settings fields.
    if _clean_settings_block(existing, settings_block):
        write_json(path, existing)
        print(f"[qwen] API sync disabled — removed managed settings fields from {path}.")
    else:
        print("[qwen] API sync disabled — no managed settings fields to clean.")


def _sync_skills() -> None:
    claude_skills_dir = claude_skills_base()
    qwen_skills_dir = qwen_skills_base()
    if not claude_skills_dir.exists():
        print(f"[qwen] Claude skills directory not found: {claude_skills_dir} — skipping skill sync.")
        return

    qwen_skills_dir.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(claude_skills_dir.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = qwen_skills_dir / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"[qwen] Synced {len(synced)} skills to {qwen_skills_dir}: {', '.join(synced) or '(none)'}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync env vars, settings fields, and skills to Qwen Code.

    Qwen Code does not use MCP servers in the same way as other
    platforms — the mcp_servers parameter is accepted but ignored. Model
    definitions (``~/.qwen/models.json``) are owned by Qwen itself and are not
    synced by this engine.
    """
    root = qwen_root_dir()
    if not root.exists():
        print(f"[qwen] Qwen root not found: {root} — skipping (tool not installed).")
        return

    api_enabled = _api_enabled(cfg)
    _sync_env(cfg.get("env", {}), api_enabled)
    _sync_settings_block(cfg, api_enabled)
    _sync_skills()
