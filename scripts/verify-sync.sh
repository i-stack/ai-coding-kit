#!/usr/bin/env bash
# Sanity-check sync outputs. Run after sync-skills.sh / sync-agent-preamble.sh
# to confirm three-way skill caches are clean and preamble files are tilde-ified.
#
# Exits non-zero if any check fails; prints one FAIL line per problem.

set -uo pipefail

SKILL_NAME="${SKILL_NAME:-ios-engineer}"

CLAUDE_SKILL="${HOME}/.claude/skills/${SKILL_NAME}"
CODEX_SKILL="${HOME}/.codex/skills/${SKILL_NAME}"
CURSOR_SKILL="${HOME}/.cursor/skills/${SKILL_NAME}"
CLAUDE_PREAMBLE="${HOME}/.claude/CLAUDE.md"
CODEX_PREAMBLE="${HOME}/.codex/AGENTS.md"

FAIL=0
note_fail() {
  echo "FAIL: $*" >&2
  FAIL=1
}

check_skill_dir() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    note_fail "$dir missing"
    return
  fi
  [[ -f "$dir/SKILL.md" ]]    || note_fail "$dir/SKILL.md missing"
  [[ -d "$dir/references" ]]  || note_fail "$dir/references/ missing"
  for stale in evolution proposals history scripts agents validations scenarios approvals usage; do
    if [[ -d "$dir/$stale" ]]; then
      note_fail "$dir/$stale is stale (should be excluded by sync-skills.sh)"
    fi
  done
}

check_preamble_tilde() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    note_fail "$file missing"
    return
  fi
  if ! grep -q '^SKILL 规则位于 `~' "$file"; then
    note_fail "$file is not tilde-ified (expected: SKILL 规则位于 \`~...\`)"
  fi
}

check_skill_dir "$CLAUDE_SKILL"
check_skill_dir "$CODEX_SKILL"
check_skill_dir "$CURSOR_SKILL"
check_preamble_tilde "$CLAUDE_PREAMBLE"
check_preamble_tilde "$CODEX_PREAMBLE"

if [[ $FAIL -eq 0 ]]; then
  echo "OK: three-way skill caches clean (SKILL.md + references/ only); preambles tilde-ified"
fi
exit $FAIL
