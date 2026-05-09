#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LOCAL_CONFIG="${SCRIPT_DIR}/config.local.sh"
if [[ -f "${LOCAL_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${LOCAL_CONFIG}"
fi

SKILL_NAME="${SKILL_NAME:-ios-engineer}"

TEMPLATE="${TEMPLATE:-${SCRIPT_DIR}/templates/agent-preamble.md.tmpl}"
CLAUDE_TARGET="${CLAUDE_TARGET:-${HOME}/.claude/CLAUDE.md}"
CODEX_TARGET="${CODEX_TARGET:-${HOME}/.codex/AGENTS.md}"
CURSOR_PROJECT_ROOTS="${CURSOR_PROJECT_ROOTS:-}"

BEGIN_MARKER="<!-- managed-block:ios-engineer:begin"
END_MARKER="<!-- managed-block:ios-engineer:end"

CURSOR_MDC_PROLOGUE='---
description: ios-engineer skill usage and audit rules
alwaysApply: true
---
'

DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-agent-preamble.sh [options]

Renders scripts/templates/agent-preamble.md.tmpl into the managed block in:
  - ~/.claude/CLAUDE.md  (tool=claude-code, skills=~/.claude/skills/ios-engineer/)
  - ~/.codex/AGENTS.md   (tool=codex,       skills=~/.codex/skills/ios-engineer/)
  - <project>/.cursor/rules/ios-engineer.mdc for each project root in
    CURSOR_PROJECT_ROOTS (colon-separated). Skipped if unset.

Block markers: <!-- managed-block:ios-engineer:begin ... :end -->
Only block contents are rewritten; surrounding content is preserved.

Options:
  --dry-run     Print diff without writing
  -h, --help    Show help

Environment variables:
  TEMPLATE               Default: <script-dir>/templates/agent-preamble.md.tmpl
  SKILL_NAME             Default: ios-engineer
  CLAUDE_TARGET          Default: ~/.claude/CLAUDE.md
  CODEX_TARGET           Default: ~/.codex/AGENTS.md
  CURSOR_PROJECT_ROOTS   Colon-separated project roots, e.g.
                         /path/to/projA:/path/to/projB
                         Writes to <root>/.cursor/rules/ios-engineer.mdc
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
  shift
done

if [[ ! -f "${TEMPLATE}" ]]; then
  echo "Template not found: ${TEMPLATE}" >&2
  exit 1
fi

render() {
  local tool_name="$1"
  local skills_dir="$2"
  sed -e "s|{{TOOL_NAME}}|${tool_name}|g" \
      -e "s|{{SKILLS_DIR}}|${skills_dir}|g" \
      "${TEMPLATE}"
}

sync_target() {
  local target="$1"
  local tool_name="$2"
  local skills_dir="$3"
  local prologue="${4:-}"

  mkdir -p "$(dirname "${target}")"

  local rendered new_content
  rendered="$(mktemp)"
  new_content="$(mktemp)"
  render "${tool_name}" "${skills_dir}" > "${rendered}"

  if [[ ! -f "${target}" ]]; then
    {
      if [[ -n "${prologue}" ]]; then
        printf '%s' "${prologue}"
      fi
      cat "${rendered}"
    } > "${new_content}"
  elif grep -Fq "${BEGIN_MARKER}" "${target}"; then
    awk -v rendered_file="${rendered}" \
        -v begin="${BEGIN_MARKER}" \
        -v end="${END_MARKER}" '
      BEGIN { in_block = 0 }
      {
        if (!in_block && index($0, begin) > 0) {
          in_block = 1
          while ((getline line < rendered_file) > 0) print line
          next
        }
        if (in_block && index($0, end) > 0) {
          in_block = 0
          next
        }
        if (!in_block) print
      }
    ' "${target}" > "${new_content}"
  else
    { cat "${rendered}"; echo; cat "${target}"; } > "${new_content}"
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    if [[ -f "${target}" ]] && diff -q "${target}" "${new_content}" >/dev/null 2>&1; then
      echo "No change: ${target}"
    else
      echo "--- ${target} (current)"
      echo "+++ ${target} (rendered)"
      diff -u "${target}" "${new_content}" || true
    fi
  else
    if [[ -f "${target}" ]] && diff -q "${target}" "${new_content}" >/dev/null 2>&1; then
      echo "No change: ${target}"
    else
      cp "${new_content}" "${target}"
      echo "Wrote: ${target}"
    fi
  fi

  rm -f "${rendered}" "${new_content}"
}

sync_target "${CLAUDE_TARGET}" "claude-code" "~/.claude/skills/ios-engineer/"
sync_target "${CODEX_TARGET}"  "codex"       "~/.codex/skills/ios-engineer/"

if [[ -n "${CURSOR_PROJECT_ROOTS}" ]]; then
  IFS=':' read -ra _cursor_roots <<< "${CURSOR_PROJECT_ROOTS}"
  for _root in "${_cursor_roots[@]}"; do
    [[ -z "${_root}" ]] && continue
    if [[ ! -d "${_root}" ]]; then
      echo "Cursor project root not found, skipping: ${_root}" >&2
      continue
    fi
    sync_target "${_root}/.cursor/rules/ios-engineer.mdc" \
                "cursor" \
                "~/.cursor/skills/ios-engineer/" \
                "${CURSOR_MDC_PROLOGUE}"
  done
else
  echo "CURSOR_PROJECT_ROOTS not set; skipping Cursor project rules."
fi
