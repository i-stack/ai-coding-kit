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

# Mirror sync-skills.sh gating: 1=force on, 0=force off, unset=auto-detect.
sync_enabled() {
  local flag="$1"
  local root_dir="$2"
  case "${flag}" in
    1|true|yes|on)  return 0 ;;
    0|false|no|off) return 1 ;;
    "")             [[ -d "${root_dir}" ]] ;;
    *)
      echo "Invalid SYNC_* flag value: '${flag}'" >&2
      return 1
      ;;
  esac
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

CHECKED=0
if sync_enabled "${SYNC_CLAUDE:-}" "${HOME}/.claude"; then
  check_skill_dir "$CLAUDE_SKILL"
  check_preamble_tilde "$CLAUDE_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CLAUDE:-}" ]]; then
  echo "Skip Claude verify: disabled via SYNC_CLAUDE=${SYNC_CLAUDE}."
else
  echo "Skip Claude verify: ${HOME}/.claude not found (set SYNC_CLAUDE=1 to force)."
fi
if sync_enabled "${SYNC_CODEX:-}" "${HOME}/.codex"; then
  check_skill_dir "$CODEX_SKILL"
  check_preamble_tilde "$CODEX_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CODEX:-}" ]]; then
  echo "Skip Codex verify: disabled via SYNC_CODEX=${SYNC_CODEX}."
else
  echo "Skip Codex verify: ${HOME}/.codex not found (set SYNC_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_CURSOR:-}" "${HOME}/.cursor"; then
  check_skill_dir "$CURSOR_SKILL"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CURSOR:-}" ]]; then
  echo "Skip Cursor verify: disabled via SYNC_CURSOR=${SYNC_CURSOR}."
else
  echo "Skip Cursor verify: ${HOME}/.cursor not found (set SYNC_CURSOR=1 to force)."
fi

if [[ $FAIL -eq 0 ]]; then
  if [[ $CHECKED -eq 0 ]]; then
    echo "OK: no sync targets enabled; nothing to verify."
  else
    echo "OK: ${CHECKED} target(s) clean (SKILL.md + references/ only); preambles tilde-ified"
  fi
fi
exit $FAIL
