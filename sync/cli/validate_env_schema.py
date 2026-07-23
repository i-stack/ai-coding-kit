"""Validate env/ JSON configuration files against expected schemas.

Checks:
  - env/mcp/*.json: valid MCP server definitions
  - env/platforms/*.json: valid platform configs

Usage:
    python3 sync/cli/main.py validate-env                  # validate all
    python3 sync/cli/main.py validate-env --mcp-only       # only MCP files
    python3 sync/cli/main.py validate-env --platforms-only # only platform files
"""
import json
from pathlib import Path

from platforms.claude import _HOST_SKIP as _CLAUDE_HOST_SKIP
from platforms.codex import _HOST_SKIP as _CODEX_HOST_SKIP

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = REPO_ROOT / "env"
MCP_DIR = ENV_DIR / "mcp"
OPTIONAL_MCP_DIR = ENV_DIR / "optional_mcps"
PLATFORMS_DIR = ENV_DIR / "platforms"

# ── MCP server schema ────────────────────────────────────────────────────────

MCP_VALID_TYPES = {"stdio", "sse"}
MCP_KNOWN_FIELDS = {
    "name", "type", "command", "args", "env", "url", "headers",
    "platforms", "_comment",
}


def validate_mcp_file(path: Path) -> list[str]:
    """Validate a single MCP server JSON file. Returns list of errors."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON — {e}"]
    except OSError as e:
        return [f"{path.name}: cannot read — {e}"]

    if not isinstance(data, dict):
        return [f"{path.name}: root must be a JSON object"]

    # Check type field
    srv_type = data.get("type")
    if srv_type is not None and srv_type not in MCP_VALID_TYPES:
        errors.append(f"{path.name}: invalid type '{srv_type}' (must be one of {MCP_VALID_TYPES})")

    # 渲染兜底：必须有可渲染的入口——stdio 需要 command，sse 需要 url。
    # 任意其一存在即可（type 可省略，由字段推断），但都不能缺失，否则
    # load_all_mcp() 后平台渲染器在 cfg['command']/cfg['url'] 处 KeyError 崩溃。
    has_command = "command" in data
    has_url = "url" in data
    if not has_command and not has_url:
        errors.append(f"{path.name}: MCP definition must include 'command' (stdio) or 'url' (sse)")

    # Check stdio requires command
    if srv_type == "stdio" and "command" not in data:
        errors.append(f"{path.name}: type=stdio requires 'command' field")

    # Check sse requires url
    if srv_type == "sse" and "url" not in data:
        errors.append(f"{path.name}: type=sse requires 'url' field")

    # Check platforms is a list
    platforms = data.get("platforms")
    if platforms is not None and not isinstance(platforms, list):
        errors.append(f"{path.name}: 'platforms' must be a list")

    # Warn about unknown fields
    unknown = set(data.keys()) - MCP_KNOWN_FIELDS
    if unknown:
        errors.append(f"{path.name}: unknown fields: {', '.join(sorted(unknown))}")

    return errors


# ── Platform config schema ────────────────────────────────────────────────────

COMMON_PLATFORM_FIELDS = {
    "_comment",
    "api",
    "env",
    "export_env_to_zshrc",
    "install_root",
    "mcp_target",
    "preamble",
}

PLATFORM_FIELDS = {
    # Claude-specific: team-shared fields not covered by _HOST_SKIP, unioned
    # with the platform's own host-specific set (kept in sync with the real
    # skip list instead of hand-duplicating it — see platforms/claude.py).
    "claude": {
        "model", "effortLevel", "alwaysThinkingEnabled", "outputStyle",
        "includeGitInstructions", "respectGitignore", "fileCheckpointingEnabled",
        "autoCompactEnabled", "autoMemoryEnabled", "respondToBashCommands",
        "permissions", "hooks", "_hostSettings",
    } | _CLAUDE_HOST_SKIP,
    # Codex-specific: team-shared fields not covered by _HOST_SKIP, unioned
    # with the platform's own host-specific set (see platforms/codex.py).
    "codex": {
        "model", "model_provider", "model_providers", "sandbox_mode",
        "approval_policy", "allow_login_shell", "default_permissions",
        "sandbox_workspace_write", "projects",
    } | _CODEX_HOST_SKIP,
    # CodeBuddy-specific
    "codebuddy": {"models", "availableModels"},
    # Qwen-specific
    "qwen": {"security", "modelProviders", "model"},
    # Continue-specific
    "continue": {"models", "path", "recall"},
    # Gemini-specific
    "gemini": {
        "primary_model", "fallback_model", "model", "context", "tools", "skills",
        "hooksConfig", "security", "experimental", "contextManagement",
    },
    # Cline-specific
    "cline": {"globalState", "secrets"},
}


def known_fields_for_platform(platform: str) -> set[str]:
    return COMMON_PLATFORM_FIELDS | PLATFORM_FIELDS.get(platform, set())


def validate_platform_file(path: Path) -> list[str]:
    """Validate a single platform config JSON file. Returns list of errors."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON — {e}"]
    except OSError as e:
        return [f"{path.name}: cannot read — {e}"]

    if not isinstance(data, dict):
        return [f"{path.name}: root must be a JSON object"]

    # Check env is an object if present
    env = data.get("env")
    if env is not None and not isinstance(env, dict):
        errors.append(f"{path.name}: 'env' must be a JSON object")

    # Check export_env_to_zshrc is an object if present
    export_env = data.get("export_env_to_zshrc")
    if export_env is not None and not isinstance(export_env, dict):
        errors.append(f"{path.name}: 'export_env_to_zshrc' must be a JSON object")

    # Check api.enabled is a boolean if present
    api = data.get("api")
    if api is not None:
        if not isinstance(api, dict):
            errors.append(f"{path.name}: 'api' must be a JSON object")
        else:
            api_unknown = set(api.keys()) - {"enabled"}
            if api_unknown:
                errors.append(
                    f"{path.name}: unknown api fields: {', '.join(sorted(api_unknown))}"
                )
            enabled = api.get("enabled")
            if enabled is not None and not isinstance(enabled, bool):
                errors.append(f"{path.name}: 'api.enabled' must be a boolean")

    # Check preamble sync metadata if present
    preamble = data.get("preamble")
    if preamble is not None:
        if not isinstance(preamble, dict):
            errors.append(f"{path.name}: 'preamble' must be a JSON object")
        else:
            preamble_unknown = set(preamble.keys()) - {"target", "mode", "tool", "format", "agents"}
            if preamble_unknown:
                errors.append(
                    f"{path.name}: unknown preamble fields: {', '.join(sorted(preamble_unknown))}"
                )
            mode = preamble.get("mode")
            if mode is not None and mode not in {"full", "recall", "none"}:
                errors.append(f"{path.name}: 'preamble.mode' must be one of: full, none, recall")
            fmt = preamble.get("format")
            if fmt is not None and fmt not in {"markdown", "yaml", "cursor-mdc"}:
                errors.append(
                    f"{path.name}: 'preamble.format' must be one of: cursor-mdc, markdown, yaml"
                )
            agents = preamble.get("agents")
            if agents is not None and not isinstance(agents, bool):
                errors.append(f"{path.name}: 'preamble.agents' must be a boolean")

    # Check for unknown (typo / uncategorized) top-level fields
    unknown = set(data.keys()) - known_fields_for_platform(path.stem)
    if unknown:
        errors.append(f"{path.name}: unknown fields: {', '.join(sorted(unknown))}")

    return errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-only", action="store_true", help="Only validate MCP files")
    parser.add_argument("--platforms-only", action="store_true", help="Only validate platform files")
    args = parser.parse_args(argv)

    all_errors: list[str] = []

    # Validate MCP files (env/mcp + env/optional_mcps)
    if not args.platforms_only:
        mcp_dirs = [MCP_DIR]
        if OPTIONAL_MCP_DIR.is_dir():
            mcp_dirs.append(OPTIONAL_MCP_DIR)
        total_mcp = 0
        for d in mcp_dirs:
            if not d.is_dir():
                all_errors.append(f"{d.relative_to(REPO_ROOT)}/: no JSON files found")
                continue
            for f in sorted(d.glob("*.json")):
                if d is OPTIONAL_MCP_DIR and f.name == "enabled.json":
                    continue  # registry 文件，不是 MCP 定义
                all_errors.extend(validate_mcp_file(f))
                total_mcp += 1
        print(f"Checked {total_mcp} MCP file(s) (incl. optional_mcps).")

    # Validate platform files
    if not args.mcp_only and PLATFORMS_DIR.is_dir():
        platform_files = sorted(PLATFORMS_DIR.glob("*.json"))
        if not platform_files:
            all_errors.append("env/platforms/: no JSON files found")
        for f in platform_files:
            all_errors.extend(validate_platform_file(f))
        print(f"Checked {len(platform_files)} platform file(s).")

    if all_errors:
        print("\nERRORS:")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print("\nAll env/ JSON files are valid.")
        return 0
