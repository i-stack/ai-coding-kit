import os
from pathlib import Path
from typing import Any

from .common import load_platform_config


def dump_yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict) and not v:
        return "{}"
    if isinstance(v, list) and not v:
        return "[]"
    s = str(v)
    special_chars = {":", "#", "-", "{", "}", "[", "]", ",", "\n", "@", "`", "&", "*", "!", "|", ">", "?", "<", "=", "%"}
    needs_quotes = (
        any(c in s for c in special_chars)
        or s.lower() in ("true", "false", "null")
        or s.strip() != s
        or (s and s[0] in "-?:,[]{}#&*!|>'\"%@`")
    )
    if needs_quotes:
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    return s


def dump_yaml(data: Any, indent_level: int = 0) -> str:
    spacing = " " * indent_level
    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and len(v) > 0:
                lines.append(f"{spacing}{k}:")
                lines.append(dump_yaml(v, indent_level + 2))
            else:
                lines.append(f"{spacing}{k}: {dump_yaml_scalar(v)}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return "[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                dict_lines = []
                for i, (k, v) in enumerate(item.items()):
                    if i == 0:
                        if isinstance(v, (dict, list)) and len(v) > 0:
                            dict_lines.append(f"{spacing}- {k}:")
                            dict_lines.append(dump_yaml(v, indent_level + 4))
                        else:
                            dict_lines.append(f"{spacing}- {k}: {dump_yaml_scalar(v)}")
                    else:
                        if isinstance(v, (dict, list)) and len(v) > 0:
                            dict_lines.append(f"{spacing}  {k}:")
                            dict_lines.append(dump_yaml(v, indent_level + 4))
                        else:
                            dict_lines.append(f"{spacing}  {k}: {dump_yaml_scalar(v)}")
                lines.append("\n".join(dict_lines))
            else:
                lines.append(f"{spacing}- {dump_yaml_scalar(item)}")
        return "\n".join(lines)
    else:
        return dump_yaml_scalar(data)


def update_yaml_root_key(yaml_text: str, key_name: str, new_key_yaml: str) -> str:
    lines = yaml_text.splitlines()
    new_lines = []

    in_key = False
    key_replaced = False

    for line in lines:
        stripped = line.strip()
        is_empty_or_comment = not stripped or stripped.startswith("#")

        is_root_key = False
        if not is_empty_or_comment and not line.startswith(" "):
            if ":" in line:
                is_root_key = True

        if is_root_key:
            if in_key:
                in_key = False

            curr_key = line.split(":", 1)[0].strip()
            if curr_key == key_name:
                in_key = True
                if not key_replaced:
                    new_lines.append(new_key_yaml)
                    key_replaced = True
                continue

        if in_key:
            continue

        new_lines.append(line)

    if not key_replaced:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(new_key_yaml)

    return "\n".join(new_lines) + "\n"


def sync(mcp_servers: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Sync MCP servers and models to Continue (YAML format)."""
    path_str = cfg.get("path", "~/.continue/config.yaml")
    target_path = Path(path_str).expanduser()

    if not target_path.exists():
        print(f"[warn] Continue configuration file does not exist at {target_path}. Skipping.")
        return

    yaml_text = target_path.read_text(encoding="utf-8")

    # 1. Sync mcpServers
    continue_servers = []
    for name, srv_cfg in sorted(mcp_servers.items()):
        if not isinstance(srv_cfg, dict):
            continue
        srv = {"name": name}
        for k, v in srv_cfg.items():
            srv[k] = v

        # Continue schema mapping for SSE / Remote servers
        if "url" in srv:
            if "type" not in srv:
                srv["type"] = "sse"
            if "headers" in srv:
                headers = srv.pop("headers")
                if headers:
                    srv["requestOptions"] = {"headers": headers}

        continue_servers.append(srv)

    if not continue_servers:
        new_mcp_yaml = "mcpServers: []"
    else:
        new_mcp_yaml = "mcpServers:\n" + dump_yaml(continue_servers, indent_level=2)

    yaml_text = update_yaml_root_key(yaml_text, "mcpServers", new_mcp_yaml)

    # 2. Sync models (only if present in configuration)
    models = cfg.get("models")
    if models is not None:
        if not isinstance(models, list):
            print("[warn] platforms.continue.models must be a list. Skipping model sync.")
        else:
            if not models:
                new_models_yaml = "models: []"
            else:
                new_models_yaml = "models:\n" + dump_yaml(models, indent_level=2)
            yaml_text = update_yaml_root_key(yaml_text, "models", new_models_yaml)
            print("Replaced models in Continue config.")

    target_path.write_text(yaml_text, encoding="utf-8")
    print(f"Replaced MCP servers in {target_path}.")
