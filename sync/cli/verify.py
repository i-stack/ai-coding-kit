"""Python verifier for sync outputs.

Replaces the hardcoded platform list in verify-sync.sh with targets discovered
from the shared target registry. All platforms declared in env/platforms/*.json plus the
Xcode special targets are verified consistently.

Exit code: 0 on clean, 1 on any failure.

Usage:
    python3 sync/cli/main.py verify
    python3 sync/cli/main.py verify --target claude
    python3 sync/cli/main.py verify --target all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SYNC_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SYNC_DIR.parent

from core.registry import SyncTarget, enabled_targets, is_enabled, load_targets  # noqa: E402

# Directories that must not exist in an installed skill payload.
_STALE_DIRS = frozenset({
    "evolution", "proposals", "history", "scripts",
    "agents", "validations", "scenarios", "approvals", "usage",
})

# Required content patterns for full-preamble verification.
# Each entry: (label_for_error_message, substring_that_must_exist)
_FULL_PREAMBLE_PATTERNS: list[tuple[str, str]] = [
    ("managed-block begin marker", "<!-- managed-block:agent-preamble:begin"),
    ("tilde-ified skill path", "SKILL 规则位于 `~"),
    ("cognitive-expansion reference", "cognitive-expansion/references/cognitive_expansion.md"),
    ("logical-reasoning reference", "logical-reasoning/references/logical_reasoning.md"),
    ("engineering-discipline reference", "engineering-discipline/references/engineering_discipline.md"),
    ("problem-analysis reference", "problem-analysis/references/problem_analysis.md"),
    ("plan-grill reference", "plan-grill/references/plan_grill.md"),
    ("epistemic-integrity reference", "epistemic-integrity/references/epistemic_integrity.md"),
]

# Required content patterns for standalone recall-preamble verification (Cline / Qwen,
# plus any platform explicitly configured with preamble.mode=recall). These targets
# get only the historical-recall managed block, not the full agent-preamble.
# Checking content rather than just inode existence catches stale or empty files.
_RECALL_PREAMBLE_PATTERNS: list[tuple[str, str]] = [
    ("managed-block begin marker", "<!-- managed-block:historical-recall:begin"),
    ("historical-recall SKILL path", "historical-recall/SKILL.md"),
    ("HR rules reference", "HR-001"),
    ("recall CLI path", "plan-reviews/dist/cli.js"),
]


# ── Skill checks ─────────────────────────────────────────────────────────────

def _discover_skills(skills_engineering_dir: Path) -> list[str]:
    skills = []
    for d in sorted(skills_engineering_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            skills.append(d.name)
    return skills


def _check_skill_dir(skill_dir: Path, failures: list[str]) -> None:
    if not skill_dir.is_dir():
        failures.append(f"{skill_dir} missing")
        return
    for required_file in ("SKILL.md", "AGENT-BRIEF.md", "OUT-OF-SCOPE.md"):
        if not (skill_dir / required_file).exists():
            failures.append(f"{skill_dir}/{required_file} missing")
    if not (skill_dir / "references").is_dir():
        failures.append(f"{skill_dir}/references/ missing")
    for stale in _STALE_DIRS:
        if (skill_dir / stale).is_dir():
            failures.append(
                f"{skill_dir}/{stale} is stale (should be excluded by sync-skills.sh)"
            )


def _check_skills(target: SyncTarget, skills: list[str], failures: list[str]) -> None:
    assert target.skills_dir is not None
    for skill in skills:
        _check_skill_dir(target.skills_dir / skill, failures)


# ── Preamble checks ───────────────────────────────────────────────────────────

def _check_full_preamble(path: Path, failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"{path} missing")
        return
    content = path.read_text(encoding="utf-8")
    for label, pattern in _FULL_PREAMBLE_PATTERNS:
        if pattern not in content:
            failures.append(f"{path}: missing {label} ({pattern!r})")


def _check_recall_preamble(path: Path, failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"{path} missing (recall preamble)")
        return
    content = path.read_text(encoding="utf-8")
    for label, pattern in _RECALL_PREAMBLE_PATTERNS:
        if pattern not in content:
            failures.append(f"{path}: missing {label} ({pattern!r})")


def _check_yaml_recall(path: Path | None, failures: list[str]) -> None:
    # Continue's YAML recall is injected into the platform config, not a
    # standalone file.  When target is None, there is nothing to assert here;
    # structural verification requires reading the platform's own config file.
    if path is None:
        return
    if not path.is_file():
        failures.append(f"{path} missing (yaml recall preamble)")


# ── Per-target verification ───────────────────────────────────────────────────

def verify_target(
    target: SyncTarget,
    skills: list[str],
    failures: list[str],
) -> None:
    v = target.verify

    if v.skills and target.skills_dir is not None:
        _check_skills(target, skills, failures)

    if v.full_preamble and target.preamble and target.preamble.target:
        _check_full_preamble(target.preamble.target, failures)

    if v.recall_preamble and target.preamble and target.preamble.target:
        _check_recall_preamble(target.preamble.target, failures)

    if v.yaml_recall and target.preamble:
        _check_yaml_recall(target.preamble.target, failures)


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify sync outputs against the target registry."
    )
    parser.add_argument(
        "--target",
        default="all",
        help="Target name to verify, or 'all' (default: all enabled targets).",
    )
    args = parser.parse_args(argv)

    skills_engineering_dir = REPO_ROOT / "skills-engineering"

    if args.target == "all":
        targets = enabled_targets()
        skipped = [t for t in load_targets() if not is_enabled(t)]
    else:
        all_targets = {t.name: t for t in load_targets()}
        if args.target not in all_targets:
            print(
                f"Unknown target: {args.target!r}. "
                f"Known: {sorted(all_targets)}", file=sys.stderr
            )
            return 2
        t = all_targets[args.target]
        targets = [t] if is_enabled(t) else []
        skipped = [] if targets else [t]

    for t in skipped:
        flag = t.enabled_flag
        import os
        flag_val = os.environ.get(flag, "")
        if flag_val in ("0", "false", "no", "off"):
            print(f"Skip {t.name} verify: disabled via {flag}={flag_val}.")
        else:
            print(
                f"Skip {t.name} verify: {t.install_root} not found "
                f"(set {flag}=1 to force)."
            )

    if not targets:
        print("OK: no sync targets enabled; nothing to verify.")
        return 0

    skills = _discover_skills(skills_engineering_dir)
    failures: list[str] = []
    checked = 0

    for target in targets:
        before = len(failures)
        verify_target(target, skills, failures)
        if len(failures) == before:
            print(f"OK: {target.name}")
        checked += 1

    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)

    if failures:
        return 1

    print(f"\nOK: {checked} target(s) clean")
    return 0
