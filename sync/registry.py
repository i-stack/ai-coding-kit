"""Shared target registry for all sync surfaces.

Single source of truth answering, per target:
  - Is this target installed?
  - What env flag controls it?
  - Does it receive skill payloads?
  - Does it receive a preamble, and in what mode/format?
  - What should verification assert?

All sync surfaces (skills sync, preamble sync, verify) must consume this
module instead of maintaining their own platform lists.

Usage:
    from registry import load_targets, enabled_targets, SyncTarget
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

SYNC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SYNC_DIR.parent
PLATFORMS_DIR = REPO_ROOT / "env" / "platforms"

if str(SYNC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNC_DIR))

from platforms import paths as _paths  # noqa: E402


@dataclass
class PreambleSpec:
    target: Path | None
    # target is None when the preamble is injected by a renderer (e.g. Continue
    # YAML recall, which has no standalone target file to write or verify).
    mode: Literal["full", "recall", "none"]
    format: Literal["markdown", "yaml", "cursor-mdc"] = "markdown"
    tool: str = ""
    router: bool = False
    agents: bool = False


@dataclass
class VerifySpec:
    skills: bool = False
    full_preamble: bool = False
    recall_preamble: bool = False
    # yaml_recall with target=None skips the file-exists check; verifying
    # Continue's YAML recall requires reading the platform config file.
    yaml_recall: bool = False


@dataclass
class SyncTarget:
    name: str
    install_root: Path
    enabled_flag: str
    preamble: PreambleSpec | None = None
    skills_dir: Path | None = None
    verify: VerifySpec = field(default_factory=VerifySpec)


def _resolve_install_root(name: str, data: dict) -> Path | None:
    """Resolve install root for a platform.

    Priority:
    1. ``path`` field in the platform JSON (e.g. ``"path": "~/.custom_codex"``)
    2. paths.py Mac default (reads secrets.json overrides internally)
    3. ``~/.{name}`` — fallback for platforms not registered in paths.py

    Returns None only when the resolved path would be meaningless (shouldn't
    happen after adding the ~/.{name} fallback, but kept for safety).
    """
    json_path = data.get("install_root")
    if json_path and isinstance(json_path, str) and json_path.strip():
        try:
            return Path(json_path).expanduser()
        except (KeyError, RuntimeError):
            pass

    root = _paths.platform_install_root(name)
    if root is not None:
        return root

    # New platform not yet in paths._INSTALL_ROOTS: fall back to ~/.{name}
    return Path.home() / f".{name}"


def _parse_preamble(raw: dict, install_root: Path) -> PreambleSpec:
    mode = raw.get("mode", "none")
    fmt = raw.get("format", "markdown")
    tool = raw.get("tool", "")
    target_rel = raw.get("target")
    target = (install_root / target_rel) if target_rel else None
    return PreambleSpec(
        target=target,
        mode=mode,
        format=fmt,
        tool=tool,
        router=bool(raw.get("router", False)),
        agents=bool(raw.get("agents", False)),
    )


def _platform_targets() -> list[SyncTarget]:
    """Discover targets from env/platforms/*.json."""
    targets: list[SyncTarget] = []
    for cfg_file in sorted(PLATFORMS_DIR.glob("*.json")):
        name = cfg_file.stem
        try:
            data: dict = json.loads(cfg_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        install_root = _resolve_install_root(name, data)
        if install_root is None:
            continue

        enabled_flag = f"SYNC_{name.upper().replace('-', '_')}"

        raw_preamble = data.get("preamble")
        preamble = (
            _parse_preamble(raw_preamble, install_root)
            if isinstance(raw_preamble, dict)
            else None
        )

        # Continue loads skills from the repo; no skills dir is installed.
        has_skills = name != "continue"
        skills_dir = (install_root / "skills") if has_skills else None

        verify = VerifySpec(
            skills=has_skills,
            full_preamble=(
                preamble is not None
                and preamble.mode == "full"
                and preamble.format == "markdown"
            ),
            recall_preamble=(
                preamble is not None
                and preamble.mode == "recall"
                and preamble.format == "markdown"
            ),
            yaml_recall=(preamble is not None and preamble.format == "yaml"),
        )

        targets.append(
            SyncTarget(
                name=name,
                install_root=install_root,
                enabled_flag=enabled_flag,
                preamble=preamble,
                skills_dir=skills_dir,
                verify=verify,
            )
        )
    return targets


def _xcode_targets() -> list[SyncTarget]:
    """Return Xcode special targets (not represented in env/platforms/*.json)."""
    xcode_base = _paths.xcode_coding_assistant_dir()
    codex_root = xcode_base / "codex"
    claude_root = xcode_base / "ClaudeAgentConfig"
    return [
        SyncTarget(
            name="xcode-codex",
            install_root=codex_root,
            enabled_flag="SYNC_XCODE_CODEX",
            preamble=PreambleSpec(
                target=codex_root / "AGENTS.md",
                mode="full",
                format="markdown",
                tool="codex",
            ),
            skills_dir=codex_root / "skills",
            verify=VerifySpec(skills=True, full_preamble=True),
        ),
        SyncTarget(
            name="xcode-claude",
            install_root=claude_root,
            enabled_flag="SYNC_XCODE_CLAUDE",
            preamble=PreambleSpec(
                target=claude_root / "CLAUDE.md",
                mode="full",
                format="markdown",
                tool="claude-code",
            ),
            skills_dir=claude_root / "skills",
            verify=VerifySpec(skills=True, full_preamble=True),
        ),
    ]


def load_targets() -> list[SyncTarget]:
    """Return all known sync targets (installed or not)."""
    return _platform_targets() + _xcode_targets()


def _flag_value(target: SyncTarget) -> str:
    return os.environ.get(target.enabled_flag, "")


def is_enabled(target: SyncTarget) -> bool:
    """True if the target's env flag is on, or unset and install root exists."""
    flag = _flag_value(target)
    if flag in ("0", "false", "no", "off"):
        return False
    if flag in ("1", "true", "yes", "on"):
        return True
    return target.install_root.exists()


def enabled_targets() -> list[SyncTarget]:
    """Return targets that are currently enabled."""
    return [t for t in load_targets() if is_enabled(t)]
