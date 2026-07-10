#!/usr/bin/env python3
"""Validate env/ JSON configuration files against expected schemas.

Checks:
  - env/mcp/*.json: valid MCP server definitions
  - env/platforms/*.json: valid platform configs

Usage:
    python3 sync/validate_env_schema.py                 # validate all
    python3 sync/validate_env_schema.py --mcp-only      # only MCP files
    python3 sync/validate_env_schema.py --platforms-only # only platform files
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = REPO_ROOT / "env"
MCP_DIR = ENV_DIR / "mcp"
PLATFORMS_DIR = ENV_DIR / "platforms"

# ── MCP server schema ────────────────────────────────────────────────────────

MCP_REQUIRED_FIELDS = set()  # No strictly required fields (name defaults to filename)
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

COMMON_PLATFORM_FIELDS = {"_comment", "env", "export_env_to_zshrc", "mcp_target"}

PLATFORM_FIELDS = {
    # Claude-specific
    "claude": {
        "model", "effortLevel", "alwaysThinkingEnabled", "outputStyle",
        "includeGitInstructions", "respectGitignore", "fileCheckpointingEnabled",
        "autoCompactEnabled", "autoMemoryEnabled", "respondToBashCommands",
        "permissions", "hooks", "_hostSettings",
        "apiKeyHelper", "theme", "tui", "editorMode", "preferredNotifChannel",
        "statusLine", "voice", "voiceEnabled", "viewMode", "prefersReducedMotion",
        "syntaxHighlightingDisabled", "terminalProgressBarEnabled",
        "wheelScrollAccelerationEnabled", "axScreenReaderRender", "showTurnDuration",
        "showThinkingSummaries", "showClearContextOnPlanAccept", "autoScrollEnabled",
        "spinnerTipsEnabled", "spinnerTipsOverride", "spinnerVerbs", "companyAnnouncements",
        "footerLinksRegexes", "language", "ultracode", "fastModePerSessionOptIn",
        "autoConnectIde", "autoInstallIdeExtension", "externalEditorContext",
        "fileSuggestion", "feedbackSurveyRate", "cleanupPeriodDays", "defaultShell",
        "prUrlTemplate", "autoUpdatesChannel", "sshConfigs", "worktree", "plansDirectory",
        "autoMemoryDirectory", "teammateMode", "teammateDefaultModel", "disableAgentView",
        "agent", "agentPushNotifEnabled", "inputNeededNotifEnabled", "remoteControlAtStartup",
        "awsAuthRefresh", "awsCredentialExport", "gcpAuthRefresh", "otelHeadersHelper",
        "claudeMd", "claudeMdExcludes", "policyHelper", "skipWebFetchPreflight",
    },
    # Codex-specific
    "codex": {
        "model", "model_provider", "model_providers", "personality",
        "model_reasoning_effort", "model_verbosity", "model_reasoning_summary",
        "plan_mode_reasoning_effort", "sandbox_mode", "approval_policy",
        "allow_login_shell", "default_permissions", "project_doc_max_bytes",
        "project_doc_fallback_filenames", "sandbox_workspace_write", "features",
        "projects", "hide_agent_reasoning", "web_search", "file_opener", "history",
        "tools", "shell_environment_policy", "tui", "agents", "memories",
        "analytics", "feedback",
    },
    # CodeBuddy-specific
    "codebuddy": {"models", "availableModels"},
    # Continue-specific
    "continue": {"models", "path"},
    # Gemini-specific
    "gemini": {
        "primary_model", "fallback_model", "model", "context", "tools", "skills",
        "hooksConfig", "security", "experimental", "contextManagement",
    },
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

    # Check for unknown (typo / uncategorized) top-level fields
    unknown = set(data.keys()) - known_fields_for_platform(path.stem)
    if unknown:
        errors.append(f"{path.name}: unknown fields: {', '.join(sorted(unknown))}")

    return errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-only", action="store_true", help="Only validate MCP files")
    parser.add_argument("--platforms-only", action="store_true", help="Only validate platform files")
    args = parser.parse_args()

    all_errors: list[str] = []

    # Validate MCP files
    if not args.platforms_only and MCP_DIR.is_dir():
        mcp_files = sorted(MCP_DIR.glob("*.json"))
        if not mcp_files:
            all_errors.append("env/mcp/: no JSON files found")
        for f in mcp_files:
            all_errors.extend(validate_mcp_file(f))
        print(f"Checked {len(mcp_files)} MCP file(s).")

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
        sys.exit(1)
    else:
        print("\nAll env/ JSON files are valid.")


if __name__ == "__main__":
    main()
