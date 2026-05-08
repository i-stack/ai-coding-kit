#!/usr/bin/env bash

# Fresh-device bootstrap for skills-engineering.
#
# Clones the repo (or pulls if already present) and runs the sync scripts:
#   1. scripts/sync-skills.sh         -> pushes ios-engineer skill to
#                                        ~/.claude, ~/.codex, ~/.cursor skills dirs
#   2. scripts/sync-agent-preamble.sh -> renders agent preamble into
#                                        ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md
#                                        (and optional Cursor project rules)
#
# One-liner for a fresh device:
#   curl -fsSL https://raw.githubusercontent.com/i-stack/skills-engineering/main/scripts/bootstrap.sh | bash
#
# Environment variables:
#   REPO_URL               Default: https://github.com/i-stack/skills-engineering.git
#   CLONE_TARGET           Default: ~/Desktop/github/skills-engineering
#   REF                    Branch/tag/commit to check out after clone. Default: main
#   CURSOR_PROJECT_ROOTS   Passthrough to sync-agent-preamble.sh (optional)
#   SKIP_PREAMBLE=true     Skip sync-agent-preamble.sh
#   SKIP_SKILLS=true       Skip sync-skills.sh

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/i-stack/skills-engineering.git}"
CLONE_TARGET="${CLONE_TARGET:-${HOME}/Desktop/github/skills-engineering}"
REF="${REF:-main}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but not found on PATH" >&2
  exit 1
fi

if [[ -d "${CLONE_TARGET}/.git" ]]; then
  echo "Repo already present at ${CLONE_TARGET} — fetching updates..."
  git -C "${CLONE_TARGET}" fetch --tags origin
  git -C "${CLONE_TARGET}" checkout "${REF}"
  git -C "${CLONE_TARGET}" pull --ff-only origin "${REF}" || \
    echo "(pull --ff-only failed; leaving working tree as-is)"
elif [[ -e "${CLONE_TARGET}" ]]; then
  echo "Path exists but is not a git repo: ${CLONE_TARGET}" >&2
  echo "Move or remove it, or set CLONE_TARGET to a different path." >&2
  exit 1
else
  echo "Cloning ${REPO_URL} -> ${CLONE_TARGET}"
  mkdir -p "$(dirname "${CLONE_TARGET}")"
  git clone "${REPO_URL}" "${CLONE_TARGET}"
  git -C "${CLONE_TARGET}" checkout "${REF}"
fi

SCRIPTS_DIR="${CLONE_TARGET}/scripts"

if [[ "${SKIP_SKILLS:-false}" != "true" ]]; then
  echo "---"
  echo "Running sync-skills.sh"
  "${SCRIPTS_DIR}/sync-skills.sh"
fi

if [[ "${SKIP_PREAMBLE:-false}" != "true" ]]; then
  echo "---"
  echo "Running sync-agent-preamble.sh"
  "${SCRIPTS_DIR}/sync-agent-preamble.sh"
fi

echo "---"
echo "Bootstrap complete."
echo "Source repo: ${CLONE_TARGET}"
echo "Re-run sync anytime with:"
echo "  ${SCRIPTS_DIR}/sync-skills.sh"
echo "  ${SCRIPTS_DIR}/sync-agent-preamble.sh"
