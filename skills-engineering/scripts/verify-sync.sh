#!/usr/bin/env bash
# Sanity-check sync outputs. Run after sync-skills.sh / sync-agent-preamble.sh
# to confirm enabled skill caches are clean and preamble files are tilde-ified.
#
# Exits non-zero if any check fails; prints one FAIL line per problem.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_PREAMBLE="${HOME}/.claude/CLAUDE.md"
CODEX_PREAMBLE="${HOME}/.codex/AGENTS.md"
XCODE_CODEX_PREAMBLE="${HOME}/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md"
XCODE_CLAUDE_PREAMBLE="${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md"

FAIL=0
note_fail() {
  echo "FAIL: $*" >&2
  FAIL=1
}

discover_skills() {
  local d name
  for d in "${SE_DIR}"/*/; do
    [[ -f "${d}/SKILL.md" ]] || continue
    name="$(basename "${d}")"
    echo "${name}"
  done | sort
}

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

check_skills_under_base() {
  local base="$1"
  local skill
  while IFS= read -r skill; do
    [[ -n "${skill}" ]] || continue
    check_skill_dir "${base}/${skill}"
  done < <(discover_skills)
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
  if ! grep -q 'cognitive-expansion/references/cognitive_expansion.md' "$file"; then
    note_fail "$file missing cognitive-expansion full-text load instruction"
  fi
  if ! grep -q 'logical-reasoning/references/logical_reasoning.md' "$file"; then
    note_fail "$file missing logical-reasoning full-text load instruction"
  fi
  if ! grep -q 'engineering-discipline/references/engineering_discipline.md' "$file"; then
    note_fail "$file missing engineering-discipline full-text load instruction"
  fi
}

CHECKED=0
if sync_enabled "${SYNC_CLAUDE:-}" "${HOME}/.claude"; then
  check_skills_under_base "${HOME}/.claude/skills"
  check_preamble_tilde "$CLAUDE_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CLAUDE:-}" ]]; then
  echo "Skip Claude verify: disabled via SYNC_CLAUDE=${SYNC_CLAUDE}."
else
  echo "Skip Claude verify: ${HOME}/.claude not found (set SYNC_CLAUDE=1 to force)."
fi
if sync_enabled "${SYNC_CODEX:-}" "${HOME}/.codex"; then
  check_skills_under_base "${HOME}/.codex/skills"
  check_preamble_tilde "$CODEX_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CODEX:-}" ]]; then
  echo "Skip Codex verify: disabled via SYNC_CODEX=${SYNC_CODEX}."
else
  echo "Skip Codex verify: ${HOME}/.codex not found (set SYNC_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_CURSOR:-}" "${HOME}/.cursor"; then
  check_skills_under_base "${HOME}/.cursor/skills"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_CURSOR:-}" ]]; then
  echo "Skip Cursor verify: disabled via SYNC_CURSOR=${SYNC_CURSOR}."
else
  echo "Skip Cursor verify: ${HOME}/.cursor not found (set SYNC_CURSOR=1 to force)."
fi
if sync_enabled "${SYNC_XCODE_CODEX:-}" "${HOME}/Library/Developer/Xcode/CodingAssistant/codex"; then
  check_skills_under_base "${HOME}/Library/Developer/Xcode/CodingAssistant/codex/skills"
  check_preamble_tilde "$XCODE_CODEX_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_XCODE_CODEX:-}" ]]; then
  echo "Skip Xcode Codex verify: disabled via SYNC_XCODE_CODEX=${SYNC_XCODE_CODEX}."
else
  echo "Skip Xcode Codex verify: ${HOME}/Library/Developer/Xcode/CodingAssistant/codex not found (set SYNC_XCODE_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_XCODE_CLAUDE:-}" "${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig"; then
  check_skills_under_base "${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills"
  check_preamble_tilde "$XCODE_CLAUDE_PREAMBLE"
  CHECKED=$((CHECKED + 1))
elif [[ -n "${SYNC_XCODE_CLAUDE:-}" ]]; then
  echo "Skip Xcode Claude verify: disabled via SYNC_XCODE_CLAUDE=${SYNC_XCODE_CLAUDE}."
else
  echo "Skip Xcode Claude verify: ${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig not found (set SYNC_XCODE_CLAUDE=1 to force)."
fi

if [[ $FAIL -eq 0 ]]; then
  if [[ $CHECKED -eq 0 ]]; then
    echo "OK: no sync targets enabled; nothing to verify."
  else
    echo "OK: ${CHECKED} target(s) clean (all skills: SKILL.md + references/ only); preambles tilde-ified"
  fi
fi
exit $FAIL
