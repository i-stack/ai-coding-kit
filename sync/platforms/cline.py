import re
import shutil
from typing import Any

from core.common import read_json_object, write_json
from core.paths import (
    claude_skills_base,
    cline_data_dir,
    cline_root_dir,
    cline_global_state_path,
    cline_mcp_candidate_paths,
    cline_secrets_path,
    cline_skills_base,
)

# Matches a value that is still a single unresolved ${VAR} placeholder.
_UNRESOLVED_PLACEHOLDER_RE = re.compile(r"\A\$\{[^}]+\}\Z")

# Sidecar that records which keys this tool currently manages, so a key
# removed from the platform config can be pruned from the user's files on the
# next sync. Without this record the managed set would have to be hardcoded
# (and kept in sync by hand every time the config gains or drops a key). Lives
# next to globalState.json / secrets.json; Cline ignores dot-files.
_MANAGED_KEYS_SIDECAR = cline_data_dir() / ".managed_keys.json"


def _load_managed_keys() -> dict[str, set[str]]:
    """Return the set of keys this tool currently manages, per section.

    The sidecar is the single source of truth and is updated on every sync,
    so the managed set is derived from actual sync history rather than
    hardcoded. On a fresh install (no sidecar yet) there is nothing to prune,
    and the first sync writes the current config's keys into the sidecar.
    """
    data = read_json_object(_MANAGED_KEYS_SIDECAR)
    if data:
        return {
            "globalState": set(data.get("globalState", [])),
            "secrets": set(data.get("secrets", [])),
        }
    return {"globalState": set(), "secrets": set()}


def _save_managed_keys(global_state_keys: set[str], secret_keys: set[str]) -> None:
    """Persist the currently-managed key sets to the sidecar."""
    write_json(_MANAGED_KEYS_SIDECAR, {
        "globalState": sorted(global_state_keys),
        "secrets": sorted(secret_keys),
    })


def _prune_all_managed_keys() -> None:
    """Disabled-platform cleanup: remove every key this tool manages.

    Deletes all keys recorded in the sidecar from globalState.json and
    secrets.json, leaving Cline's own keys (welcome state, auto-approval,
    etc.) untouched. The sidecar itself is left intact so re-enabling still
    prunes keys that have since been dropped from the config.

    No-op (beyond a log line) when nothing managed is present — e.g. on a
    fresh install that never synced, or after a previous cleanup.
    """
    record = _load_managed_keys()
    gs_path = cline_global_state_path()
    gs = read_json_object(gs_path)
    removed_gs = [k for k in record["globalState"] if k in gs]
    for k in removed_gs:
        del gs[k]

    sec_path = cline_secrets_path()
    sec = read_json_object(sec_path)
    removed_sec = [k for k in record["secrets"] if k in sec]
    for k in removed_sec:
        del sec[k]

    if removed_gs:
        write_json(gs_path, gs)
    if removed_sec:
        write_json(sec_path, sec)

    if removed_gs or removed_sec:
        print(f"[cline] Platform disabled — removed {len(removed_gs)} global state key(s) and {len(removed_sec)} secret key(s).")
    else:
        print("[cline] Platform disabled — no managed keys to remove.")


def _sync_mcp(servers: dict[str, Any]) -> None:
    targets = [p for p in cline_mcp_candidate_paths() if p.parent.exists()]
    if not targets:
        print("[cline] No Cline MCP settings directory found (checked Cursor, Code, Code - Insiders).")
        return
    for path in targets:
        data = read_json_object(path)
        data["mcpServers"] = servers
        write_json(path, data)
        print(f"Replaced MCP servers in {path}.")


def _sync_skills() -> None:
    claude_skills_dir = claude_skills_base()
    cline_skills_dir = cline_skills_base()
    if not claude_skills_dir.exists():
        print(f"[cline] Claude skills directory not found: {claude_skills_dir} — skipping skill sync.")
        return

    cline_skills_dir.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []

    for skill_dir in sorted(claude_skills_dir.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        dest = cline_skills_dir / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        synced.append(skill_dir.name)

    print(f"Synced {len(synced)} skills to {cline_skills_dir}: {', '.join(synced) or '(none)'}.")


def _sync_global_state(managed: dict[str, Any]) -> None:
    """Merge the managed keys into ~/.cline/data/globalState.json.

    Preserves every other key in the file (welcome state, auto-approval
    settings, workspace roots, etc.). Unresolved ${VAR} placeholders are
    skipped so a missing cline.url never writes literal "${cline.url}" into
    the user's global state.

    Any key we previously managed (tracked in the sidecar) that is no longer
    present in the config is deleted from the file, so removing a key from the
    platform config (e.g. planModeApiProvider) also removes its stale value
    instead of leaving it behind on the next sync.
    """
    if not managed:
        return
    path = cline_global_state_path()
    existing = read_json_object(path)
    merged = dict(existing)
    applied = 0
    for key, value in managed.items():
        if isinstance(value, str) and _UNRESOLVED_PLACEHOLDER_RE.match(value):
            print(f"[cline] Skipping globalState.{key}: unresolved placeholder {value} — set cline.url in secrets.json.")
            continue
        merged[key] = value
        applied += 1
    record = _load_managed_keys()
    removed = 0
    for key in record["globalState"]:
        if key not in managed and key in merged:
            del merged[key]
            removed += 1
    if applied or removed:
        write_json(path, merged)
        record["globalState"] = set(managed.keys())
        _save_managed_keys(record["globalState"], record["secrets"])
        parts = []
        if applied:
            parts.append(f"set {applied} global state key(s)")
        if removed:
            parts.append(f"removed {removed} stale global state key(s)")
        print(f"Synced global state to {path}: {'; '.join(parts)}.")
    else:
        print("[cline] No global state changes to sync — skipping.")


def _sync_secrets(secrets: dict[str, Any]) -> None:
    """Merge API secrets into ~/.cline/data/secrets.json.

    Cline stores each provider's key under the <provider>ApiKey key
    (e.g. geminiApiKey). Existing keys for other providers are preserved.
    Unresolved ${VAR} placeholders are skipped to avoid writing garbage.

    Any key we previously managed (tracked in the sidecar) that is no longer
    present in the config is deleted from the file, so removing a provider
    (e.g. geminiApiKey) also removes its stale secret on the next sync.
    """
    if not secrets:
        return
    path = cline_secrets_path()
    existing = read_json_object(path)
    merged = dict(existing)
    applied = 0
    for key, value in secrets.items():
        if isinstance(value, str) and _UNRESOLVED_PLACEHOLDER_RE.match(value):
            print(f"[cline] Skipping secret '{key}': unresolved placeholder {value} — set cline.key in secrets.json.")
            continue
        merged[key] = value
        applied += 1
    record = _load_managed_keys()
    removed = 0
    for key in record["secrets"]:
        if key not in secrets and key in merged:
            del merged[key]
            removed += 1
    if applied or removed:
        write_json(path, merged)
        record["secrets"] = set(secrets.keys())
        _save_managed_keys(record["globalState"], record["secrets"])
        parts = []
        if applied:
            parts.append(f"set {applied} secret key(s)")
        if removed:
            parts.append(f"removed {removed} stale secret key(s)")
        print(f"Synced secrets to {path}: {'; '.join(parts)}.")
    else:
        print("[cline] No secret changes to sync — skipping.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers, skills, global state, and secrets to Cline (VSCode extension).

    When the platform is disabled (enabled=false), the orchestrator still passes
    the full cfg but the renderer applies its disabled-state handling: MCP
    servers and skills are still synced, and every key this tool manages is
    removed from globalState.json and secrets.json (a thorough cleanup, so no
    stale values linger). Re-enabling re-applies the managed keys.
    """
    root = cline_root_dir()
    if not root.exists():
        print(f"[cline] Cline root not found: {root} — skipping (tool not installed).")
        return

    _sync_mcp(mcp_servers)
    _sync_skills()
    if cfg.get("enabled") is False:
        _prune_all_managed_keys()
        return
    _sync_global_state(cfg.get("globalState", {}))
    _sync_secrets(cfg.get("secrets", {}))
