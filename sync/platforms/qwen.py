"""Sync engine for Qwen Code platform.

Writes DASHSCOPE_API_KEY into ~/.qwen/settings.json env, syncs model
definitions (``models`` + ``availableModels``) into ~/.qwen/models.json, and
copies skills from ~/.claude/skills/ to ~/.qwen/skills/.

Model sync mirrors CodeBuddy: API model fields are gated by ``api.enabled``
(missing ``api`` block defaults to enabled). When ``api.enabled=false``, the
managed ``availableModels`` list is set to ``[]`` (CodeBuddy special handling —
provider model definitions stay so they can be re-enabled, but nothing is shown
in the model picker) while ``models`` is not merged.
"""
import shutil
from typing import Any

from core.common import read_json_object, write_json
from core.paths import (
    claude_skills_base,
    qwen_models_path,
    qwen_root_dir,
    qwen_settings_json_path,
    qwen_skills_base,
)


def _api_enabled(cfg: dict[str, Any]) -> bool:
    """Qwen third-party API sync toggle.

    Like Claude and CodeBuddy, a missing ``api`` block or missing
    ``api.enabled`` defaults to enabled so the historical always-sync behavior
    is preserved. Only an explicit ``false`` disables synced API fields
    (``env`` and model definitions).
    """
    api = cfg.get("api")
    if not isinstance(api, dict):
        return True
    return api.get("enabled", True) is True


def _validate_model_entries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("platforms.qwen.models must be a list.")

    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"platforms.qwen.models[{index}] must be an object.")
        model_id = entry.get("id")
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(f"platforms.qwen.models[{index}].id must be a non-empty string.")
    return value


def _validate_available_models(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("platforms.qwen.availableModels must be a list.")

    for index, model_id in enumerate(value):
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(
                f"platforms.qwen.availableModels[{index}] must be a non-empty string."
            )
    return value


def _merge_model_entries(
    existing_entries: list[Any], config_entries: list[dict[str, Any]]
) -> list[Any]:
    """Merge config-managed model entries into existing entries by id.

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

    # Trailing non-standard entries
    for m in existing_entries:
        if not isinstance(m, dict) or "id" not in m:
            result.append(m)

    return result


def _merge_available_models(
    existing_available: list[Any], config_available: list[Any]
) -> list[Any]:
    """Merge config-managed availableModels with user-added entries.

    - Config-managed IDs appear first and replace any existing duplicates.
    - User-added IDs not in the config are preserved after config entries.
    """
    if not config_available:
        return existing_available

    config_ids = set(config_available)
    # User-added IDs not managed by our config
    user_ids = [m for m in existing_available if m not in config_ids]
    return list(config_available) + user_ids


def _sync_env(env: dict[str, Any], api_enabled: bool) -> None:
    """Merge or clean managed env vars in ~/.qwen/settings.json.

    When ``api_enabled`` is true, the env keys declared in the platform config
    are merged into the settings ``env`` object; other keys are preserved.

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


def _sync_models(cfg: dict[str, Any]) -> None:
    api_enabled = _api_enabled(cfg)
    models = cfg.get("models")
    available_models = cfg.get("availableModels")
    models_path = qwen_models_path()

    # No model config at all: clean up any previously synced managed keys.
    if models is None and available_models is None:
        existing = read_json_object(models_path)
        removed = False
        for key in ("models", "availableModels"):
            if key in existing:
                existing.pop(key, None)
                removed = True
        if removed:
            write_json(models_path, existing)
            print(f"[qwen] Removed managed models config from {models_path} (model config absent).")
        else:
            print("[qwen] No models config found — skipping model sync.")
        return

    existing = read_json_object(models_path)

    # API sync disabled: do not sync API fields. CodeBuddy special handling —
    # empty availableModels (key preserved) rather than removing it, so synced
    # models are disabled from selection without dropping provider definitions.
    # Config-managed model definitions are left untouched (not synced, not
    # removed); "do not sync" means we skip merging, not that we delete.
    if not api_enabled:
        existing["availableModels"] = []
        write_json(models_path, existing)
        print(f"[qwen] API sync disabled — availableModels cleared in {models_path}.")
        return

    if models is not None:
        models = _validate_model_entries(models)
        existing_entries = existing.get("models")
        if not isinstance(existing_entries, list):
            existing_entries = []
        existing["models"] = _merge_model_entries(existing_entries, models)

    if available_models is not None:
        available_models = _validate_available_models(available_models)
        existing_avail = existing.get("availableModels")
        if not isinstance(existing_avail, list):
            existing_avail = []
        existing["availableModels"] = _merge_available_models(existing_avail, available_models)

    write_json(models_path, existing)
    print(f"Merged models into {models_path}.")


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
    """Sync env vars, model definitions, and skills to Qwen Code.

    Qwen Code does not use MCP servers in the same way as other
    platforms — the mcp_servers parameter is accepted but ignored.
    """
    root = qwen_root_dir()
    if not root.exists():
        print(f"[qwen] Qwen root not found: {root} — skipping (tool not installed).")
        return

    api_enabled = _api_enabled(cfg)
    _sync_env(cfg.get("env", {}), api_enabled)
    _sync_models(cfg)
    _sync_skills()
