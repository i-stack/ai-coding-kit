import shutil
from pathlib import Path
from typing import Any

from . import recall
from .common import read_json_object, sync_json_mcp, write_json
from .paths import (
    claude_skills_base,
    codebuddy_mcp_path,
    codebuddy_models_path,
    codebuddy_root_dir,
    codebuddy_skills_base,
)

# ── Global historical recall (end-to-end recall, same mechanism as Claude Code) ──
# Injected into ~/.codebuddy/CODEBUDDY.md — CodeBuddy's global always-on context
# file — so every CodeBuddy session gets the managed historical-recall block.
# Rendered from the SAME template the bash sync-agent-preamble.sh uses for the
# CodeBuddy recall-only target, so both paths produce byte-identical output.
_RECALL_BEGIN = "<!-- managed-block:historical-recall:begin"
_RECALL_END = "<!-- managed-block:historical-recall:end"


def _repo_root() -> Path:
    """Repo root: sync/platforms/<this file> -> parents[2]."""
    return Path(__file__).resolve().parents[2]


def _render_recall_block(codebuddy_skills_dir: Path) -> str | None:
    """Render the historical-recall managed block from the shared template.

    Delegates to sync.platforms.recall (the single source of truth shared with
    the Bash preamble writer and continue.py) so every path stays byte-consistent.
    """
    cli_path = str(
        (
            _repo_root()
            / "skills-engineering"
            / "plan-reviews"
            / "dist"
            / "cli.js"
        ).resolve()
    )
    return recall.render_recall_block(
        str(codebuddy_skills_dir / "historical-recall") + "/", cli_path
    )


def _merge_recall_block(target: Path, block: str) -> None:
    """Idempotently merge the historical-recall managed block into CODEBUDDY.md.

    Delegates to sync.platforms.recall (shared with the Bash preamble writer).
    """
    recall.merge_recall_block_markdown(target, block)


def _validate_model_entries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("platforms.codebuddy.models must be a list.")

    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"platforms.codebuddy.models[{index}] must be an object.")
        model_id = entry.get("id")
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(f"platforms.codebuddy.models[{index}].id must be a non-empty string.")
    return value


def _validate_available_models(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("platforms.codebuddy.availableModels must be a list.")

    for index, model_id in enumerate(value):
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(
                f"platforms.codebuddy.availableModels[{index}] must be a non-empty string."
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


def _sync_models(cfg: dict[str, Any]) -> None:
    models = cfg.get("models")
    available_models = cfg.get("availableModels")
    models_path = codebuddy_models_path()

    # A disabled platform (enabled=false) clears the managed model keys while
    # preserving any developer-added siblings (e.g. "meta"). The orchestrator
    # forwards `enabled` to the renderer instead of passing an empty config.
    if cfg.get("enabled") is False or (models is None and available_models is None):
        existing = read_json_object(models_path)
        removed = False
        for key in ("models", "availableModels"):
            if key in existing:
                existing.pop(key, None)
                removed = True
        if removed:
            write_json(models_path, existing)
            print(f"[codebuddy] Removed managed models config from {models_path} (platform disabled).")
        else:
            print("[codebuddy] No models config found — skipping model sync.")
        return

    existing = read_json_object(models_path)

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
    codebuddy_skills_dir = codebuddy_skills_base()
    if not claude_skills_dir.exists():
        print(f"[codebuddy] Claude skills directory not found: {claude_skills_dir} — skipping skill sync.")
        return

    codebuddy_skills_dir.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(claude_skills_dir.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = codebuddy_skills_dir / skill_dir.name
        tmp = codebuddy_skills_dir / f".{skill_dir.name}.tmp-sync"
        backup = codebuddy_skills_dir / f".{skill_dir.name}.backup-sync"

        if tmp.exists():
            shutil.rmtree(tmp)
        if backup.exists():
            shutil.rmtree(backup)

        shutil.copytree(skill_dir, tmp)

        if dest.exists():
            dest.rename(backup)
        try:
            tmp.rename(dest)
        except OSError:
            if backup.exists() and not dest.exists():
                backup.rename(dest)
            raise
        finally:
            if tmp.exists():
                shutil.rmtree(tmp)
            if backup.exists():
                shutil.rmtree(backup)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {codebuddy_skills_dir}: {', '.join(synced) or '(none)'}.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers, models, skills, and the global recall preamble to CodeBuddy."""
    root = codebuddy_root_dir()
    if not root.exists():
        print(f"[codebuddy] CodeBuddy root not found: {root} — skipping (tool not installed).")
        return

    sync_json_mcp(codebuddy_mcp_path(), mcp_servers)
    _sync_models(cfg)
    _sync_skills()

    # Sync the global historical-recall managed block into the platform's
    # preamble file. Driven by the `preamble` declaration in
    # env/platforms/codebuddy.json (single source of truth); defaults to recall
    # mode into CODEBUDDY.md for backward compatibility (no preamble yet).
    preamble = cfg.get("preamble") or {}
    recall_mode = preamble.get("mode", "recall")
    if recall_mode != "none":
        recall_target = codebuddy_root_dir() / preamble.get("target", "CODEBUDDY.md")
        block = _render_recall_block(codebuddy_skills_base())
        if block is not None:
            _merge_recall_block(recall_target, block)
        else:
            print("[codebuddy] agent-preamble template not found — skipping CODEBUDDY.md recall sync.")
    else:
        print("[codebuddy] historical-recall preamble disabled via preamble.mode=none.")
