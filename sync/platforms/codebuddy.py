import shutil
from pathlib import Path
from typing import Any

from core import recall
from core.common import api_enabled as _api_enabled, read_json_object, sync_json_mcp, write_json
from core.paths import (
    claude_skills_base,
    codebuddy_mcp_path,
    codebuddy_models_path,
    codebuddy_root_dir,
    codebuddy_skills_base,
)

# ── Standalone historical recall (used only when preamble.mode=recall) ──
# CodeBuddy normally receives the full agent-preamble from
# sync-agent-preamble.sh. This renderer is kept for explicit recall-mode configs
# and uses the same template as other standalone recall targets.
_RECALL_BEGIN = "<!-- managed-block:historical-recall:begin"
_RECALL_END = "<!-- managed-block:historical-recall:end"


def _repo_root() -> Path:
    """Repo root: sync/platforms/<this file> -> parents[2]."""
    return Path(__file__).resolve().parents[2]


def _render_recall_block(codebuddy_skills_dir: Path) -> str | None:
    """Render the historical-recall managed block from the shared template.

    Delegates to sync.core.recall (the single source of truth shared with
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

    Delegates to sync.core.recall (shared with the Bash preamble writer).
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


# Marker written onto every model entry this tool syncs into models.json.
# It stays in the target file (self-describing) so a subsequent sync can
# identify which entries are ours and prune the ones we no longer manage,
# while leaving user/system entries (without this marker) untouched.
MANAGED_BY = "ai-coding-kit"


def _is_managed(entry: Any) -> bool:
    return isinstance(entry, dict) and entry.get("_managed_by") == MANAGED_BY


def _claim_legacy_entries(
    existing_entries: list[Any], config_entries: list[dict[str, Any]]
) -> list[Any]:
    """Tag legacy (pre-marker) synced entries with the managed marker.

    Older sync versions wrote model entries WITHOUT ``_managed_by``. An unmarked
    entry that is an *exact* copy of the resolved config (same key set, same
    values) is a legacy sync output — claim it as managed so it updates and
    prunes normally from now on.

    Claiming is deliberately conservative: the identity signal is the whole
    entry, not just credentials. Matching only ``url``/``apiKey`` would wrongly
    claim user-authored entries that share the provider credentials but differ
    elsewhere, or entries on both sides that simply lack credentials
    (``None == None``). Claiming means the config will overwrite the entry on
    this same sync, so a false positive silently destroys a user-owned entry.
    """
    if not config_entries:
        return existing_entries
    config_by_id: dict[str, dict[str, Any]] = {
        m["id"]: m for m in config_entries if isinstance(m, dict) and "id" in m
    }

    result: list[Any] = []
    for entry in existing_entries:
        if not isinstance(entry, dict) or "id" not in entry or _is_managed(entry):
            result.append(entry)
            continue
        cfg = config_by_id.get(entry["id"])
        if cfg is not None and _matches_config_exactly(entry, cfg):
            claimed = dict(entry)
            claimed["_managed_by"] = MANAGED_BY
            result.append(claimed)
        else:
            result.append(entry)
    return result


def _matches_config_exactly(entry: dict[str, Any], cfg: dict[str, Any]) -> bool:
    """True only when ``entry`` looks like an exact legacy copy of ``cfg``.

    A legacy sync wrote the resolved config entry verbatim (no ``_managed_by``),
    so an exact match needs:
    - the same key set beyond ``id``/``_managed_by`` (extra or missing keys mean
      the entry was touched by the user or a UI rewrite — not an exact copy),
    - equal values for every key,
    - at least one non-``None`` comparable field beyond ``id`` (an entry whose
      only field beyond ``id`` is ``None`` carries no evidence).

    Lacking credentials alone does NOT prevent a claim: an entry without
    ``url``/``apiKey`` on either side but with other matching fields (same key
    set, same values) is still an exact copy and is claimed.
    """
    entry_keys = {k for k in entry if k not in ("id", "_managed_by")}
    cfg_keys = {k for k in cfg if k not in ("id", "_managed_by")}
    if not cfg_keys or not any(cfg.get(k) is not None for k in cfg_keys):
        return False
    if entry_keys != cfg_keys:
        return False
    return all(entry.get(k) == cfg.get(k) for k in cfg_keys)


def _merge_model_entries(
    existing_entries: list[Any], config_entries: list[dict[str, Any]]
) -> list[Any]:
    """Merge config-managed model entries into existing entries by id.

    - Config-managed entries (identified by ``id``) appear in config order,
      each tagged with ``_managed_by`` so future syncs can recognize them.
    - If a user-added entry (no ``_managed_by`` marker) shares the same id as a
      config entry, the user entry is kept untouched — config does NOT overwrite
      user-owned entries.
    - Managed entries that are no longer in config are dropped (pruned).
    - User-added entries (no ``_managed_by`` marker) are preserved as-is.
    - Non-dict entries with no id are preserved at the very end.
    """
    if not config_entries:
        return existing_entries

    # Claim legacy (pre-marker) synced entries first so they are managed again.
    existing_entries = _claim_legacy_entries(existing_entries, config_entries)

    config_by_id: dict[str, dict[str, Any]] = {}
    for m in config_entries:
        if isinstance(m, dict) and "id" in m:
            config_by_id[m["id"]] = m

    # Build a set of ids that are already owned by user (same id, no marker).
    existing_by_id: dict[str, Any] = {}
    for m in existing_entries:
        if isinstance(m, dict) and "id" in m:
            existing_by_id[m["id"]] = m
    user_owned_ids: set[str] = {
        mid
        for mid, entry in existing_by_id.items()
        if not _is_managed(entry)
    }

    result: list[Any] = []

    # Config-managed entries first (in config order), each tagged with the marker.
    # Skip config entries whose id is already claimed by a user-owned entry.
    for m in config_entries:
        if not isinstance(m, dict) or "id" not in m:
            continue
        mid = m["id"]
        if mid in user_owned_ids:
            # User has a same-id entry without marker — keep user's, skip config.
            result.append(existing_by_id[mid])
            continue
        tagged = dict(m)
        tagged["_managed_by"] = MANAGED_BY
        result.append(tagged)

    # User-added entries from existing (not managed by us), preserving order.
    for m in existing_entries:
        if not isinstance(m, dict) or "id" not in m:
            continue
        if _is_managed(m):
            # Ours but no longer in config -> drop (scenario 3: deletion).
            continue
        mid = m["id"]
        if mid not in config_by_id:
            result.append(m)
        # If mid IS in config_by_id but also user-owned, we already appended
        # it above (config-skip loop), so skip here to avoid duplicates.

    # Trailing non-standard entries
    for m in existing_entries:
        if not isinstance(m, dict) or "id" not in m:
            result.append(m)

    return result


def _merge_available_models(
    existing_available: list[Any], config_available: list[Any]
) -> list[Any]:
    """Replace availableModels wholesale with the config list.

    availableModels is a plain string list with no per-item marker, so the
    config is the single source of truth: any user/UI-added IDs not in the
    config are dropped on the next sync. An explicitly empty list from config
    means "clear all enabled models".
    """
    return list(config_available)


def _sync_models(cfg: dict[str, Any]) -> None:
    api_enabled = _api_enabled(cfg)
    models = cfg.get("models")
    available_models = cfg.get("availableModels")
    models_path = codebuddy_models_path()

    # No model config at all: clean up any previously synced managed entries.
    if models is None and available_models is None:
        existing = read_json_object(models_path)
        removed = False
        # Drop only our managed model entries, keeping user/system entries.
        existing_entries = existing.get("models")
        if isinstance(existing_entries, list) and any(_is_managed(m) for m in existing_entries):
            existing["models"] = [m for m in existing_entries if not _is_managed(m)]
            if not existing["models"]:
                existing.pop("models", None)
            removed = True
        if "availableModels" in existing:
            existing.pop("availableModels", None)
            removed = True
        if removed:
            write_json(models_path, existing)
            print(f"[codebuddy] Removed managed models config from {models_path} (model config absent).")
        else:
            print("[codebuddy] No models config found — skipping model sync.")
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
        print(f"[codebuddy] API sync disabled — availableModels cleared in {models_path}.")
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
    """Sync MCP servers, models, skills, and CodeBuddy's preamble to CODEBUDDY.md.

    The preamble shape is driven by env/platforms/codebuddy.json `preamble.mode`:
    recall -> standalone historical-recall block; full -> skipped here (rendered by
    sync-agent-preamble.sh as the embedded full preamble); none -> skipped.
    """
    root = codebuddy_root_dir()
    if not root.exists():
        print(f"[codebuddy] CodeBuddy root not found: {root} — skipping (tool not installed).")
        return

    sync_json_mcp(codebuddy_mcp_path(), mcp_servers)
    _sync_models(cfg)
    _sync_skills()

    # Sync the global historical-recall managed block into the platform's
    # preamble file. Driven by the `preamble` declaration in
    # env/platforms/codebuddy.json (single source of truth).
    #
    # - mode == "recall": write the standalone historical-recall block here
    #   (legacy/explicit recall mode, same standalone block shape as Cline /
    #   Qwen / Continue).
    # - mode == "full": the full preamble block (which *embeds* historical-recall)
    #   is rendered by `sync-agent-preamble.sh` into CODEBUDDY.md; writing a
    #   separate standalone block here would duplicate it, so we skip.
    # - mode == "none": nothing is written.
    preamble = cfg.get("preamble") or {}
    recall_mode = preamble.get("mode", "recall")
    if recall_mode == "recall":
        recall_target = codebuddy_root_dir() / preamble.get("target", "CODEBUDDY.md")
        block = _render_recall_block(codebuddy_skills_base())
        if block is not None:
            _merge_recall_block(recall_target, block)
        else:
            print("[codebuddy] agent-preamble template not found — skipping CODEBUDDY.md recall sync.")
    elif recall_mode == "none":
        print("[codebuddy] historical-recall preamble disabled via preamble.mode=none.")
    else:  # full
        print(
            "[codebuddy] preamble.mode=full — full preamble (incl. historical-recall) "
            "is rendered by sync-agent-preamble.sh; skipping standalone recall block here."
        )
