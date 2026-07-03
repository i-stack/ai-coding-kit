import json
import os
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_DIR = REPO_ROOT / "env" / "mcp"
PLATFORMS_DIR = REPO_ROOT / "env" / "platforms"
SECRETS_PATH = REPO_ROOT / "env" / "secrets.json"

_SECRET_REF_RE = re.compile(r'\$\{([^}]+)\}')


# ── Secrets resolution ───────────────────────────────────────────────────────

def _flatten_secrets(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Recursively flatten nested dict into {prefix.key: str_value} entries.

    Skips _comment keys at any level.
    Example: {"codex": {"url": "https://...", "key": "sk-..."}}
          -> {"codex.url": "https://...", "codex.key": "sk-..."}
    """
    flat: dict[str, str] = {}
    for k, v in data.items():
        if k.startswith("_"):
            continue
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(_flatten_secrets(v, full_key))
        elif isinstance(v, (str, int, float)):
            flat[full_key] = str(v)
        elif isinstance(v, list):
            flat[full_key] = json.dumps(v, ensure_ascii=False)
    return flat


def load_secrets() -> dict[str, str]:
    """Load secrets from env/secrets.json.

    Returns a flat dot-notation dict, e.g. {"github.token": "...", "codex.url": "...", "codex.key": "..."}.
    Supports per-platform nested format: {"codex": {"url": "...", "key": "..."}}

    If secrets.json doesn't exist, returns {} and prints a warning.
    """
    if not SECRETS_PATH.is_file():
        print("[sync] ⚠ env/secrets.json not found — copy env/secrets.json.example and fill in your keys.")
        return {}
    try:
        data = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[sync] Failed to load secrets: {exc}")
        return {}
    if not isinstance(data, dict):
        return {}
    return _flatten_secrets(data)


def resolve_secrets(data: Any, secrets: dict[str, str]) -> Any:
    """Recursively resolve ${VAR} references in strings using secrets dict.

    Walks dicts, lists, and strings. Non-string values are returned as-is.
    Each "${VAR}" occurrence in any string is replaced by secrets[VAR].
    If VAR is not found in secrets, the placeholder is left unchanged.
    """
    if isinstance(data, str):
        def _replacer(m: re.Match[str]) -> str:
            key = m.group(1)
            if key in secrets:
                return secrets[key]
            return m.group(0)
        return _SECRET_REF_RE.sub(_replacer, data)
    if isinstance(data, dict):
        return {k: resolve_secrets(v, secrets) for k, v in data.items()}
    if isinstance(data, list):
        return [resolve_secrets(v, secrets) for v in data]
    return data


# ── Configuration loading ────────────────────────────────────────────────────

def load_all_mcp() -> dict[str, Any]:
    """Scan env/mcp/*.json, resolve secrets, and return {server_name: server_config}.

    Each file should contain:
      {"name": "server-name", "type": "stdio|sse", ..., "platforms": [...]}

    Secrets (${VAR}) are resolved from env/secrets.json before returning.
    Returns {} if env/mcp/ is missing or empty (graceful degradation).
    """
    if not MCP_DIR.is_dir():
        print(f"[sync] {MCP_DIR} directory not found — no MCP servers loaded.")
        return {}

    secrets = load_secrets()
    result: dict[str, Any] = {}
    for f in sorted(MCP_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[sync] Skipping {f.name}: {exc}")
            continue
        if not isinstance(data, dict):
            print(f"[sync] Skipping {f.name}: not a JSON object.")
            continue
        # Resolve secrets before stripping metadata
        data = resolve_secrets(data, secrets)
        name = data.get("name", f.stem)
        clean = {k: v for k, v in data.items() if k not in ("name", "_comment")}
        result[name] = clean
    return result


def load_platform_config(platform: str) -> dict[str, Any]:
    """Load platform-specific config from env/platforms/<platform>.json.

    Secrets (${VAR}) are resolved from env/secrets.json before returning.
    Returns {} if the file doesn't exist.
    """
    path = PLATFORMS_DIR / f"{platform}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[sync] Failed to load {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        print(f"[sync] {path} must contain a JSON object — skipped.")
        return {}
    secrets = load_secrets()
    data = resolve_secrets(data, secrets)
    return {k: v for k, v in data.items() if k not in ("_comment",)}


def env_for_platform(platform: str) -> dict[str, str]:
    """Extract env vars from a platform config's top-level 'env' key.

    The 'env' key holds {VAR_NAME: value} pairs that the sync engine writes
    to ~/.zshrc managed blocks or platform settings.json as appropriate.
    """
    cfg = load_platform_config(platform)
    env = cfg.get("env", {})
    if env is None:
        env = {}
    if not isinstance(env, dict):
        raise ValueError(f"platforms.{platform}.env must be an object.")
    return {k: v for k, v in env.items() if isinstance(k, str) and isinstance(v, str) and v != ""}


def filter_mcp_for_platform(mcp_all: dict[str, Any], platform: str) -> dict[str, Any]:
    """Filter MCP servers to those enabled for the given platform.

    A server is included if:
      - It has no 'platforms' key (included everywhere), OR
      - Its 'platforms' list includes the given platform name.

    The 'platforms' key is stripped from the output.
    The 'type' key is also stripped (rendering concern, not output concern).
    """
    result: dict[str, Any] = {}
    for name, cfg in mcp_all.items():
        if not isinstance(cfg, dict):
            result[name] = cfg
            continue
        allowed = cfg.get("platforms")
        if allowed is not None:
            if not isinstance(allowed, list) or platform not in allowed:
                continue
        result[name] = {k: v for k, v in cfg.items() if k not in ("platforms", "type")}
    return result


def discover_platforms() -> list[str]:
    """Return platform names that have a config file in env/platforms/.

    Used by the orchestrator to auto-discover sync targets.
    """
    if not PLATFORMS_DIR.is_dir():
        return []
    return sorted(
        f.stem for f in PLATFORMS_DIR.glob("*.json")
    )


# ── JSON I/O utilities ───────────────────────────────────────────────────────

def sync_json_mcp(path: Path, servers: dict[str, Any]) -> None:
    if path.is_symlink():
        path.unlink()
    existing = read_json_object(path)
    existing["mcpServers"] = servers
    write_json(path, existing)
    print(f"Replaced MCP servers in {path}.")


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_object(existing: Any, updates: dict[str, Any]) -> dict[str, Any]:
    base = existing if isinstance(existing, dict) else {}
    return {**base, **updates}


# ── Path helpers ─────────────────────────────────────────────────────────────

def codex_config_path() -> Path:
    if p := os.environ.get("CODEX_CONFIG"):
        return Path(p).expanduser()
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser() / "config.toml"
    return Path.home() / ".codex/config.toml"


def codex_generated_toml_path() -> Path:
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser() / "mcp.generated.toml"
    return Path.home() / ".codex/mcp.generated.toml"


def xcode_codex_dir() -> Path:
    return Path.home() / "Library/Developer/Xcode/CodingAssistant/codex"


# ── TOML generation utilities ────────────────────────────────────────────────

def toml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_bare_key_segment(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", s))


def toml_header_key_segment(s: str) -> str:
    return s if toml_bare_key_segment(s) else toml_quote(s)


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    return toml_quote(str(value))


def toml_array(items: list[Any]) -> str:
    return "[" + ", ".join(toml_quote(str(x)) for x in items) + "]"


def toml_inline_table(values: dict[str, Any]) -> str:
    return "{ " + ", ".join(f"{k} = {toml_value(v)}" for k, v in values.items()) + " }"


def toml_section(entries: dict[str, Any], *, ignore: set[str] | None = None) -> str:
    """Convert a dict tree to TOML key-value lines and [table] sections.

    Skips keys in `ignore` (default: {'env', '_comment', 'projects', 'model_providers'}).
    Nested dicts with scalar values become [parent] tables with key=value lines.
    Deeper nested dicts become [parent.child] tables.
    Returns a TOML string suitable for insertion into managed blocks.
    """
    skip = ignore or {"env", "_comment", "projects", "model_providers", "export_env_to_zshrc"}
    lines: list[str] = []

    def _emit_table(parent_key: str, sub: dict[str, Any]) -> None:
        """Emit a TOML [table] section from a dict."""
        # Separate scalars/lists from nested dicts
        sub_tables: dict[str, dict[str, Any]] = {}
        has_scalars = False
        for k, v in sub.items():
            if isinstance(v, dict):
                sub_tables[k] = v
            else:
                has_scalars = True
                if isinstance(v, list):
                    lines.append(f"{k} = {toml_value(v)}")
                elif v is not None:
                    lines.append(f"{k} = {toml_value(v)}")
        # Emit nested sub-tables
        for sub_key, sub_value in sub_tables.items():
            section_key = toml_header_key_segment(f"{parent_key}.{sub_key}")
            lines.append(f"[{section_key}]")
            _emit_table(sub_key, sub_value)
        if has_scalars or not sub_tables:
            lines.append("")

    # Top-level scalars and simple values
    for key, value in entries.items():
        if key in skip:
            continue
        if isinstance(value, dict):
            # Insert blank line separator before [table] when following a scalar
            if lines and lines[-1] != "":
                lines.append("")
            # Emit as [key] table
            # Check if any sub-value is itself a dict (deeper nesting)
            has_deep = any(isinstance(v, dict) for v in value.values())
            if has_deep:
                lines.append(f"[{key}]")
                _emit_table(key, value)
            else:
                # Flat dict: emit as [key] with key=value lines
                lines.append(f"[{key}]")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        lines.append(f"{sub_key} = {toml_value(sub_value)}")
                    elif sub_value is not None:
                        lines.append(f"{sub_key} = {toml_value(sub_value)}")
                lines.append("")
        elif isinstance(value, list):
            lines.append(f"{key} = {toml_value(value)}")
        elif value is not None:
            lines.append(f"{key} = {toml_value(value)}")

    # model_providers section
    providers = entries.get("model_providers")
    if isinstance(providers, dict):
        for pid, pcfg in providers.items():
            if not isinstance(pcfg, dict):
                continue
            # Ensure single blank line separator before each provider
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[model_providers.{toml_header_key_segment(str(pid))}]")
            for k, v in pcfg.items():
                lines.append(f"{k} = {toml_value(v)}")

    # projects section
    projects = entries.get("projects")
    if isinstance(projects, dict):
        for path, pcfg in projects.items():
            if not isinstance(pcfg, dict):
                continue
            # Ensure single blank line separator before each project
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[projects.{toml_header_key_segment(str(path))}]")
            for k, v in pcfg.items():
                lines.append(f"{k} = {toml_value(v)}")

    return "\n".join(lines)
