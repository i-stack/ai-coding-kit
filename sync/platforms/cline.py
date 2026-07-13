import re
import shutil
from typing import Any

from .common import read_json_object, write_json
from .paths import (
    claude_skills_base,
    cline_root_dir,
    cline_global_state_path,
    cline_mcp_candidate_paths,
    cline_secrets_path,
    cline_skills_base,
)

# Matches a value that is still a single unresolved ${VAR} placeholder.
_UNRESOLVED_PLACEHOLDER_RE = re.compile(r"\A\$\{[^}]+\}\Z")


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


def _clear_global_state_base_url() -> None:
    """Disabled-platform cleanup: reset geminiBaseUrl to empty.

    Called when the platform is disabled (enabled=false). The other global
    state keys and the secret are left untouched — only the third-party API
    base URL is cleared. No-op if it is already empty.
    """
    path = cline_global_state_path()
    existing = read_json_object(path)
    if not existing.get("geminiBaseUrl"):
        print(f"[cline] geminiBaseUrl already empty in {path} — nothing to clear.")
        return
    existing["geminiBaseUrl"] = ""
    write_json(path, existing)
    print(f"Cleared geminiBaseUrl in {path} (platform disabled).")


def _sync_global_state(managed: dict[str, Any]) -> None:
    """Merge the 5 managed keys into ~/.cline/data/globalState.json.

    Preserves every other key in the file (welcome state, auto-approval
    settings, workspace roots, etc.). Unresolved ${VAR} placeholders are
    skipped so a missing cline.url never writes literal "${cline.url}" into
    the user's global state.
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
    if applied:
        write_json(path, merged)
        print(f"Synced {applied} global state key(s) to {path}.")
    else:
        print("[cline] No resolvable global state keys to sync — skipping.")


def _sync_secrets(secrets: dict[str, Any]) -> None:
    """Merge API secrets into ~/.cline/data/secrets.json.

    Cline stores each provider's key under the <provider>ApiKey key
    (e.g. geminiApiKey). Existing keys for other providers are preserved.
    Unresolved ${VAR} placeholders are skipped to avoid writing garbage.
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
    if applied:
        write_json(path, merged)
        print(f"Synced {applied} secret key(s) to {path}.")
    else:
        print("[cline] No resolvable secrets to sync — skipping.")


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers, skills, global state, and secrets to Cline (VSCode extension).

    When the platform is disabled (enabled=false), the orchestrator passes an
    empty cfg. In that case MCP servers and skills are still synced, but the
    managed global state is cleaned up by clearing geminiBaseUrl (disabling the
    third-party API) while leaving the other keys and the secret intact.
    """
    root = cline_root_dir()
    if not root.exists():
        print(f"[cline] Cline root not found: {root} — skipping (tool not installed).")
        return

    _sync_mcp(mcp_servers)
    _sync_skills()
    if not cfg:
        _clear_global_state_base_url()
        return
    _sync_global_state(cfg.get("globalState", {}))
    _sync_secrets(cfg.get("secrets", {}))
