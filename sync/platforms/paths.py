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


def codex_generated_toml_path() -> Path:
    import os
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser() / "mcp.generated.toml"
    return _home() / ".codex/mcp.generated.toml"


def claude_json_path() -> Path:
    return _home() / ".claude.json"


def claude_settings_json_path() -> Path:
    return _home() / ".claude" / "settings.json"


def claude_config_json_path() -> Path:
    return _home() / ".claude" / "config.json"


def claude_hooks_dir_path() -> Path:
    return _home() / ".claude" / "hooks"


def gemini_settings_path() -> Path:
    return _home() / ".gemini/settings.json"


def cursor_mcp_path() -> Path:
    return _home() / ".cursor/mcp.json"


def codebuddy_mcp_path() -> Path:
    return _home() / ".codebuddy/mcp.json"


def codebuddy_models_path() -> Path:
    return _home() / ".codebuddy/models.json"


def cline_mcp_candidate_paths() -> list[Path]:
    suffix = "saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    return [
        _home() / f"Library/Application Support/{editor}/User/globalStorage/{suffix}"
        for editor in ("Cursor", "Code", "Code - Insiders")
    ]


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
