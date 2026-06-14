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
XCODE_CODEX_TARGET="${XCODE_CODEX_TARGET:-${HOME}/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md}"
XCODE_CLAUDE_TARGET="${XCODE_CLAUDE_TARGET:-${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md}"
CURSOR_PROJECT_ROOTS="${CURSOR_PROJECT_ROOTS:-}"

BEGIN_MARKER="<!-- managed-block:ios-engineer:begin"
END_MARKER="<!-- managed-block:ios-engineer:end"

CURSOR_MDC_PROLOGUE='---
description: ios-engineer skill usage and audit rules
alwaysApply: true
---
'

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-agent-preamble.sh [options]

Renders scripts/templates/agent-preamble.md.tmpl into preamble managed blocks and
generates Cursor .mdc rules from skill references (see sync-manifest in tmpl).

Preamble targets:
  ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, Xcode AGENTS.md / CLAUDE.md

Cursor project rules (from sync-manifest skill:* lines):
  <repo>/.cursor/rules/<skill>.mdc
  <CURSOR_PROJECT_ROOTS>/.cursor/rules/<skill>.mdc

Skill full text is synced by sync-skills.sh to ~/.*/skills/<skill>/ — run
sync-skill-full.sh or sync-skills.sh before this script.

Manifest: agent-preamble.md.tmpl <!-- sync-manifest:v1 --> block; add
  skill:<name> to register Cursor mdc generation — no script edit.

Options:
  --dry-run     Print diff without writing
  -h, --help    Show help
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

parse_sync_manifest() {
  awk '
    /^<!-- sync-manifest/ { inblock=1; next }
    inblock && /^-->/ { exit }
    inblock {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      if ($0 == "" || $0 ~ /^#/) next
      print
    }
  ' "${TEMPLATE}"
}

sibling_skill_dir() {
  printf '%s' "$(dirname "${1%/}")/${2}/"
}

skill_primary_reference() {
  local skill="$1"
  local underscored="${skill//-/_}"
  printf '%s/%s/references/%s.md' "${SE_DIR}" "${skill}" "${underscored}"
}

render_managed_block() {
  local tool_name="$1"
  local skills_dir="$2"
  local ce_dir lr_dir ed_dir pa_dir ei_dir
  ce_dir="$(sibling_skill_dir "${skills_dir}" "cognitive-expansion")"
  lr_dir="$(sibling_skill_dir "${skills_dir}" "logical-reasoning")"
  ed_dir="$(sibling_skill_dir "${skills_dir}" "engineering-discipline")"
  pa_dir="$(sibling_skill_dir "${skills_dir}" "problem-analysis")"
  ei_dir="$(sibling_skill_dir "${skills_dir}" "epistemic-integrity")"
  awk -v begin="${BEGIN_MARKER}" -v end="${END_MARKER}" '
    index($0, begin) > 0 { inblock = 1; print; next }
    inblock && index($0, end) > 0 { print; exit }
    inblock { print }
  ' "${TEMPLATE}" | sed -e "s|{{TOOL_NAME}}|${tool_name}|g" \
      -e "s|{{SKILLS_DIR}}|${skills_dir}|g" \
      -e "s|{{COGNITIVE_EXPANSION_SKILLS_DIR}}|${ce_dir}|g" \
      -e "s|{{LOGICAL_REASONING_SKILLS_DIR}}|${lr_dir}|g" \
      -e "s|{{ENGINEERING_DISCIPLINE_SKILLS_DIR}}|${ed_dir}|g" \
      -e "s|{{PROBLEM_ANALYSIS_SKILLS_DIR}}|${pa_dir}|g" \
      -e "s|{{EPISTEMIC_INTEGRITY_SKILLS_DIR}}|${ei_dir}|g"
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
  render_managed_block "${tool_name}" "${skills_dir}" > "${rendered}"

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
      if [[ -f "${target}" ]]; then
        diff -u "${target}" "${new_content}" || true
      else
        diff -u /dev/null "${new_content}" || true
      fi
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

write_file_or_diff() {
  local dest="$1"
  local src_file="$2"
  mkdir -p "$(dirname "${dest}")"
  if [[ "${DRY_RUN}" == "true" ]]; then
    if [[ -f "${dest}" ]] && diff -q "${dest}" "${src_file}" >/dev/null 2>&1; then
      echo "No change: ${dest}"
    else
      echo "--- ${dest} (current)"
      echo "+++ ${dest} (generated)"
      if [[ -f "${dest}" ]]; then
        diff -u "${dest}" "${src_file}" || true
      else
        diff -u /dev/null "${src_file}" || true
      fi
    fi
  else
    if [[ -f "${dest}" ]] && diff -q "${dest}" "${src_file}" >/dev/null 2>&1; then
      echo "No change: ${dest}"
    else
      cp "${src_file}" "${dest}"
      echo "Wrote: ${dest}"
    fi
  fi
}

generate_skill_cursor_mdc() {
  local skill="$1"
  local dest="$2"
  local ref mdc_tmpl generated
  ref="$(skill_primary_reference "${skill}")"
  mdc_tmpl="${SCRIPT_DIR}/templates/${skill}.mdc.tmpl"

  if [[ ! -f "${ref}" ]]; then
    echo "Skill reference missing for ${skill}: ${ref}" >&2
    return 1
  fi

  generated="$(mktemp)"
  if [[ -f "${mdc_tmpl}" ]]; then
    cat "${mdc_tmpl}" > "${generated}"
    echo "" >> "${generated}"
    cat "${ref}" >> "${generated}"
  else
    {
      echo "---"
      echo "description: ${skill} (from skills-engineering)"
      echo "alwaysApply: true"
      echo "---"
      echo ""
      cat "${ref}"
    } > "${generated}"
  fi

  write_file_or_diff "${dest}" "${generated}"
  rm -f "${generated}"
}

sync_manifest_skill_cursor_rules() {
  local dest_root="$1"
  local line skill
  while IFS= read -r line; do
    [[ "${line}" == skill:* ]] || continue
    skill="${line#skill:}"
    [[ -n "${skill}" ]] || continue
    generate_skill_cursor_mdc "${skill}" "${dest_root}/.cursor/rules/${skill}.mdc"
  done < <(parse_sync_manifest)
}

if sync_enabled "${SYNC_CLAUDE:-}" "${HOME}/.claude"; then
  sync_target "${CLAUDE_TARGET}" "claude-code" "~/.claude/skills/ios-engineer/"
elif [[ -n "${SYNC_CLAUDE:-}" ]]; then
  echo "Skip Claude preamble: disabled via SYNC_CLAUDE=${SYNC_CLAUDE}."
else
  echo "Skip Claude preamble: ${HOME}/.claude not found (set SYNC_CLAUDE=1 to force)."
fi
if sync_enabled "${SYNC_CODEX:-}" "${HOME}/.codex"; then
  sync_target "${CODEX_TARGET}" "codex" "~/.codex/skills/ios-engineer/"
elif [[ -n "${SYNC_CODEX:-}" ]]; then
  echo "Skip Codex preamble: disabled via SYNC_CODEX=${SYNC_CODEX}."
else
  echo "Skip Codex preamble: ${HOME}/.codex not found (set SYNC_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_XCODE_CODEX:-}" "${HOME}/Library/Developer/Xcode/CodingAssistant/codex"; then
  sync_target "${XCODE_CODEX_TARGET}" "codex" "~/Library/Developer/Xcode/CodingAssistant/codex/skills/ios-engineer/"
elif [[ -n "${SYNC_XCODE_CODEX:-}" ]]; then
  echo "Skip Xcode Codex preamble: disabled via SYNC_XCODE_CODEX=${SYNC_XCODE_CODEX}."
else
  echo "Skip Xcode Codex preamble: ${HOME}/Library/Developer/Xcode/CodingAssistant/codex not found (set SYNC_XCODE_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_XCODE_CLAUDE:-}" "${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig"; then
  sync_target "${XCODE_CLAUDE_TARGET}" "claude-code" "~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills/ios-engineer/"
elif [[ -n "${SYNC_XCODE_CLAUDE:-}" ]]; then
  echo "Skip Xcode Claude preamble: disabled via SYNC_XCODE_CLAUDE=${SYNC_XCODE_CLAUDE}."
else
  echo "Skip Xcode Claude preamble: ${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig not found (set SYNC_XCODE_CLAUDE=1 to force)."
fi

sync_manifest_skill_cursor_rules "${REPO_ROOT}"

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
    sync_manifest_skill_cursor_rules "${_root}"
  done
else
  echo "CURSOR_PROJECT_ROOTS not set; skipping Cursor ios-engineer.mdc on external projects."
fi
