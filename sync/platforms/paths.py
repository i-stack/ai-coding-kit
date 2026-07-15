"""Centralized path constants for all AI coding tool targets.

This module is the single source of truth for all output paths used by
the sync engine. Import from here rather than hardcoding paths in
individual platform modules or shell scripts.

Usage:
    from platforms.paths import XCODE_CODEX_DIR, XCODE_CLAUDE_DIR
"""
from pathlib import Path


# ── Home directory (respects HOME env var at call time) ──────────────────────

def _home() -> Path:
    return Path.home()


# ── Xcode Coding Assistant paths ─────────────────────────────────────────────

def xcode_coding_assistant_dir() -> Path:
    """~/Library/Developer/Xcode/CodingAssistant/"""
    return _home() / "Library/Developer/Xcode/CodingAssistant"


def xcode_coding_assistant_exists() -> bool:
    return xcode_coding_assistant_dir().exists()


def xcode_codex_dir() -> Path:
    """Xcode Codex agent config directory."""
    return xcode_coding_assistant_dir() / "codex"


def xcode_claude_dir() -> Path:
    """Xcode Claude agent .claude config directory."""
    return xcode_coding_assistant_dir() / "ClaudeAgentConfig/.claude"


def xcode_claude_json_path() -> Path:
    """Xcode Claude agent .claude.json (MCP servers)."""
    return xcode_coding_assistant_dir() / "ClaudeAgentConfig/.claude.json"


def xcode_gemini_dir() -> Path:
    """Xcode Gemini agent config directory."""
    return xcode_coding_assistant_dir() / "gemini"


# ── Standard tool config paths ───────────────────────────────────────────────

def codex_config_path() -> Path:
    import os
    if p := os.environ.get("CODEX_CONFIG"):
        return Path(p).expanduser()
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser() / "config.toml"
    return _home() / ".codex/config.toml"


def codex_root_dir() -> Path:
    import os
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser()
    if p := os.environ.get("CODEX_CONFIG"):
        return Path(p).expanduser().parent
    return _home() / ".codex"


def claude_json_path() -> Path:
    return _home() / ".claude.json"


def claude_root_dir() -> Path:
    return _home() / ".claude"


def claude_settings_json_path() -> Path:
    return _home() / ".claude" / "settings.json"


def claude_config_json_path() -> Path:
    return _home() / ".claude" / "config.json"


def claude_hooks_dir_path() -> Path:
    return _home() / ".claude" / "hooks"


def gemini_settings_path() -> Path:
    return _home() / ".gemini/settings.json"


def gemini_root_dir() -> Path:
    return _home() / ".gemini"


def cursor_mcp_path() -> Path:
    return _home() / ".cursor/mcp.json"


def codebuddy_mcp_path() -> Path:
    return _home() / ".codebuddy/mcp.json"


def codebuddy_root_dir() -> Path:
    return _home() / ".codebuddy"


def codebuddy_models_path() -> Path:
    return _home() / ".codebuddy/models.json"


def cline_mcp_candidate_paths() -> list[Path]:
    suffix = "saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    return [
        _home() / f"Library/Application Support/{editor}/User/globalStorage/{suffix}"
        for editor in ("Cursor", "Code", "Code - Insiders")
    ]


def cline_root_dir() -> Path:
    return _home() / ".cline"


def continue_root_dir() -> Path:
    return _home() / ".continue"


# ── Cline data paths ──────────────────────────────────────────────────────────

def cline_data_dir() -> Path:
    """~/.cline/data — Cline's global state + secrets storage."""
    return _home() / ".cline" / "data"


def cline_global_state_path() -> Path:
    """~/.cline/data/globalState.json — Cline's global VS Code state."""
    return cline_data_dir() / "globalState.json"


def cline_secrets_path() -> Path:
    """~/.cline/data/secrets.json — Cline's encrypted-at-rest API secrets."""
    return cline_data_dir() / "secrets.json"


# ── Skill cache base directories ─────────────────────────────────────────────

def codex_skills_base() -> Path:
    return _home() / ".codex/skills"


def claude_skills_base() -> Path:
    return _home() / ".claude/skills"


def cursor_skills_base() -> Path:
    return _home() / ".cursor/skills"


def gemini_skills_base() -> Path:
    return _home() / ".gemini/skills"


def xcode_codex_skills_base() -> Path:
    return xcode_codex_dir() / "skills"


def xcode_claude_skills_base() -> Path:
    return xcode_coding_assistant_dir() / "ClaudeAgentConfig/skills"


def cline_skills_base() -> Path:
    return _home() / ".cline/skills"


def codebuddy_skills_base() -> Path:
    return _home() / ".codebuddy/skills"


def qwen_settings_json_path() -> Path:
    return _home() / ".qwen/settings.json"


def qwen_root_dir() -> Path:
    return _home() / ".qwen"


def qwen_skills_base() -> Path:
    return _home() / ".qwen/skills"


_INSTALL_ROOTS = {
    "cline": cline_root_dir,
    "codex": codex_root_dir,
    "claude": claude_root_dir,
    "codebuddy": codebuddy_root_dir,
    "gemini": gemini_root_dir,
    "continue": continue_root_dir,
    "qwen": qwen_root_dir,
}


def platform_install_root(platform: str) -> Path | None:
    getter = _INSTALL_ROOTS.get(platform)
    if getter is None:
        return None
    return getter()


def platform_is_installed(platform: str) -> bool:
    root = platform_install_root(platform)
    return root is None or root.exists()
