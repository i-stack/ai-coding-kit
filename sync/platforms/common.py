import json
import os
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_CONFIG = REPO_ROOT / "env" / "config.json"


def load_config() -> dict[str, Any] | None:
    if not SRC_CONFIG.exists():
        print(f"[sync] {SRC_CONFIG} is missing (gitignored local file).")
        print("[sync] Copy env/config.json.example -> env/config.json, edit, then run again.")
        print("[sync] Skipping sync; pre-push will not block on this.")
        return None

    data = json.loads(SRC_CONFIG.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{SRC_CONFIG} must contain a JSON object.")
    return data


def object_at(data: dict[str, Any], key: str) -> dict[str, Any]:
    val = data.get(key, {})
    if val is None:
        return {}
    if not isinstance(val, dict):
        raise ValueError(f"{key} must be an object.")
    return val


def platform_config(data: dict[str, Any], platform: str) -> dict[str, Any]:
    platforms = object_at(data, "platforms")
    cfg = platforms.get(platform, {})
    if cfg is None:
        return {}
    if not isinstance(cfg, dict):
        raise ValueError(f"platforms.{platform} must be an object.")
    return cfg


def env_for_platform(data: dict[str, Any], platform: str) -> dict[str, str]:
    env_root = object_at(data, "env")
    shared = env_root.get("shared", {})
    if shared is None:
        shared = {}
    if not isinstance(shared, dict):
        raise ValueError("env.shared must be an object.")

    cfg = platform_config(data, platform)
    local_env = cfg.get("env", {})
    if local_env is None:
        local_env = {}
    if not isinstance(local_env, dict):
        raise ValueError(f"platforms.{platform}.env must be an object.")

    merged = {**shared, **local_env}
    return {k: v for k, v in merged.items() if isinstance(k, str) and isinstance(v, str) and v != ""}


def mcp_servers(data: dict[str, Any]) -> dict[str, Any]:
    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcpServers must be an object.")
    return servers


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_object(existing: Any, updates: dict[str, Any]) -> dict[str, Any]:
    base = existing if isinstance(existing, dict) else {}
    return {**base, **updates}


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
