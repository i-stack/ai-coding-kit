"""Centralized path constants for all AI coding tool targets.

This module is the single source of truth for all output paths used by
the sync engine. Import from here rather than hardcoding paths in
individual platform modules or shell scripts.

Usage:
    from core.paths import XCODE_CODEX_DIR, XCODE_CLAUDE_DIR

Install-root overrides
----------------------
Every platform's install root can be overridden via the top-level ``paths``
object in ``env/config.json``, so tools installed in non-default locations
(e.g. a custom Codex or Claude Code prefix) are still found:

    {
      "paths": {
        "codex":     "/opt/codex",
        "claude":    "/custom/.claude",
        "gemini":    "/custom/.gemini",
        "codebuddy": "/custom/.codebuddy",
        "workbuddy": "/custom/.workbuddy",
        "cursor":    "/custom/.cursor",
        "cline":     "/custom/.cline",
        "continue":  "/custom/.continue",
        "qwen":      "/custom/.qwen",
        "xcode_coding_assistant": "~/Library/Developer/Xcode/CodingAssistant"
      }
    }

When a platform key is present, ALL derived paths for that platform resolve
under the override. Missing file / malformed JSON / empty value => default.
For Codex, the standard env vars (``CODEX_HOME``, ``CODEX_CONFIG``) still take
precedence over the config.json override.
"""
import json
from pathlib import Path


# ── Home directory (respects HOME env var at call time) ──────────────────────

def _home() -> Path:
    return Path.home()


# ── User-configurable install-root overrides ─────────────────────────────────

CONFIG_PATH = Path(__file__).resolve().parents[2] / "env" / "config.json"

_PATH_OVERRIDES: dict[str, Path] | None = None


def _load_path_overrides() -> dict[str, Path]:
    """Load per-platform install-root overrides from env/config.json.

    Reads the top-level ``paths`` object. Cached after first read. Returns {}
    on any read/parse error or when no override is configured.
    """
    global _PATH_OVERRIDES
    if _PATH_OVERRIDES is not None:
        return _PATH_OVERRIDES
    overrides: dict[str, Path] = {}
    try:
        text = CONFIG_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        _PATH_OVERRIDES = overrides
        return overrides
    if isinstance(data, dict):
        paths_cfg = data.get("paths")
        if isinstance(paths_cfg, dict):
            for key, value in paths_cfg.items():
                if isinstance(value, str) and value.strip():
                    try:
                        overrides[key] = Path(value).expanduser()
                    except (KeyError, RuntimeError):
                        # A dangling `~nonexistent-user` raises KeyError (older
                        # Python) or RuntimeError (newer Python / no HOME). Skip
                        # the bad entry instead of crashing the whole sync engine.
                        import sys

                        print(
                            f"[paths] skipping invalid override paths.{key}={value!r}: "
                            "could not expand ~user",
                            file=sys.stderr,
                        )
    _PATH_OVERRIDES = overrides
    return overrides


def _install_root(platform: str, default: Path) -> Path:
    """Return the user-overridden install root for `platform`, else `default`."""
    return _load_path_overrides().get(platform, default)


# ── Xcode Coding Assistant paths ─────────────────────────────────────────────

def xcode_coding_assistant_dir() -> Path:
    """~/Library/Developer/Xcode/CodingAssistant/ (overridable via paths.xcode_coding_assistant)"""
    return _install_root(
        "xcode_coding_assistant",
        _home() / "Library/Developer/Xcode/CodingAssistant",
    )


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


def xcode_gemini_dotgemini_dir() -> Path:
    """Xcode Gemini nested .gemini directory (holds GEMINI.md symlink + .env)."""
    return xcode_gemini_dir() / ".gemini"


def xcode_gemini_env_path() -> Path:
    """Xcode Gemini .env file path inside the nested .gemini directory."""
    return xcode_gemini_dotgemini_dir() / ".env"


# ── Standard tool config paths ───────────────────────────────────────────────

def codex_config_path() -> Path:
    import os
    if p := os.environ.get("CODEX_CONFIG"):
        return Path(p).expanduser()
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser() / "config.toml"
    return codex_root_dir() / "config.toml"


def codex_root_dir() -> Path:
    import os
    if home := os.environ.get("CODEX_HOME"):
        return Path(home).expanduser()
    if p := os.environ.get("CODEX_CONFIG"):
        return Path(p).expanduser().parent
    return _install_root("codex", _home() / ".codex")


def claude_json_path() -> Path:
    # ~/.claude.json is Claude Code's global config (holds auth + projects);
    # it always lives in $HOME and is NOT affected by the `paths.claude`
    # install-root override. The override only relocates the ~/.claude/ dir.
    return _home() / ".claude.json"


def claude_root_dir() -> Path:
    return _install_root("claude", _home() / ".claude")


def claude_settings_json_path() -> Path:
    return claude_root_dir() / "settings.json"


def claude_config_json_path() -> Path:
    return claude_root_dir() / "config.json"


def claude_hooks_dir_path() -> Path:
    return claude_root_dir() / "hooks"


def gemini_settings_path() -> Path:
    return gemini_root_dir() / "settings.json"


def gemini_root_dir() -> Path:
    return _install_root("gemini", _home() / ".gemini")


def cursor_root_dir() -> Path:
    return _install_root("cursor", _home() / ".cursor")


def cursor_mcp_path() -> Path:
    return cursor_root_dir() / "mcp.json"


def codebuddy_mcp_path() -> Path:
    return codebuddy_root_dir() / "mcp.json"


def codebuddy_root_dir() -> Path:
    return _install_root("codebuddy", _home() / ".codebuddy")


def codebuddy_models_path() -> Path:
    return codebuddy_root_dir() / "models.json"


def workbuddy_root_dir() -> Path:
    return _install_root("workbuddy", _home() / ".workbuddy")


def workbuddy_skills_base() -> Path:
    return workbuddy_root_dir() / "skills"


def cline_mcp_candidate_paths() -> list[Path]:
    suffix = "saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    return [
        _home() / f"Library/Application Support/{editor}/User/globalStorage/{suffix}"
        for editor in ("Cursor", "Code", "Code - Insiders")
    ]


def cline_root_dir() -> Path:
    return _install_root("cline", _home() / ".cline")


def continue_root_dir() -> Path:
    return _install_root("continue", _home() / ".continue")


# ── Cline data paths ──────────────────────────────────────────────────────────

def cline_data_dir() -> Path:
    """~/.cline/data — Cline's global state + secrets storage."""
    return cline_root_dir() / "data"


def cline_global_state_path() -> Path:
    """~/.cline/data/globalState.json — Cline's global VS Code state."""
    return cline_data_dir() / "globalState.json"


def cline_secrets_path() -> Path:
    """~/.cline/data/secrets.json — Cline's encrypted-at-rest API secrets."""
    return cline_data_dir() / "secrets.json"


# ── Skill cache base directories ─────────────────────────────────────────────

def codex_skills_base() -> Path:
    return codex_root_dir() / "skills"


def claude_skills_base() -> Path:
    return claude_root_dir() / "skills"


def cursor_skills_base() -> Path:
    return cursor_root_dir() / "skills"


def gemini_skills_base() -> Path:
    return gemini_root_dir() / "skills"


def xcode_codex_skills_base() -> Path:
    return xcode_codex_dir() / "skills"


def xcode_claude_skills_base() -> Path:
    return xcode_coding_assistant_dir() / "ClaudeAgentConfig/skills"


def cline_skills_base() -> Path:
    return cline_root_dir() / "skills"


def codebuddy_skills_base() -> Path:
    return codebuddy_root_dir() / "skills"


def qwen_models_path() -> Path:
    return qwen_root_dir() / "models.json"


def qwen_settings_json_path() -> Path:
    return qwen_root_dir() / "settings.json"


def qwen_root_dir() -> Path:
    return _install_root("qwen", _home() / ".qwen")


def qwen_skills_base() -> Path:
    return qwen_root_dir() / "skills"


_INSTALL_ROOTS = {
    "cline": cline_root_dir,
    "codex": codex_root_dir,
    "claude": claude_root_dir,
    "codebuddy": codebuddy_root_dir,
    "workbuddy": workbuddy_root_dir,
    "gemini": gemini_root_dir,
    "cursor": cursor_root_dir,
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
