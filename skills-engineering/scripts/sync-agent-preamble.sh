#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve a platform's install root via the SAME source as the Python sync engine
# (sync/core/paths.py -> platform_install_root). Honors the top-level `paths`
# override in env/secrets.json AND platform-specific defaults (e.g. CODEX_HOME for
# Codex) so the Bash preamble/skills writers never drift from the Python engine.
# Falls back to `default` when the platform is unknown or resolution fails.
resolve_install_root() {
  local platform="$1"
  local default="${2:-}"
  python3 - "$platform" "${default}" "${REPO_ROOT}/sync" <<'PY'
import sys
plat, default, sync_dir = sys.argv[1], sys.argv[2], sys.argv[3]
if sync_dir not in sys.path:
    sys.path.insert(0, sync_dir)
try:
    from core.paths import platform_install_root
    root = platform_install_root(plat)
    print(str(root) if root else (default or ""))
except Exception:
    print(default or "")
PY
}

SKILL_NAME="${SKILL_NAME:-ios-engineer}"

TEMPLATE="${TEMPLATE:-${SCRIPT_DIR}/templates/agent-preamble.md.tmpl}"
CLAUDE_TARGET="${CLAUDE_TARGET:-${HOME}/.claude/CLAUDE.md}"
CLAUDE_AGENTS_DIR="${CLAUDE_AGENTS_DIR:-${HOME}/.claude/agents}"
CODEX_TARGET="${CODEX_TARGET:-${HOME}/.codex/AGENTS.md}"
GEMINI_TARGET="${GEMINI_TARGET:-${HOME}/.gemini/GEMINI.md}"
XCODE_CODEX_TARGET="${XCODE_CODEX_TARGET:-${HOME}/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md}"
XCODE_CLAUDE_TARGET="${XCODE_CLAUDE_TARGET:-${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md}"
# Recall-only preamble targets (cline / qwen) and full preamble
# targets (claude / codex / gemini / xcode / codebuddy) are now discovered from each
# platform's `preamble` declaration in env/platforms/<platform>.json — see the
# data-driven loop below. No per-platform hardcoding remains here.

BEGIN_MARKER="<!-- managed-block:agent-preamble:begin"
END_MARKER="<!-- managed-block:agent-preamble:end"
LEGACY_BEGIN_MARKER="<!-- managed-block:ios-engineer:begin"
LEGACY_END_MARKER="<!-- managed-block:ios-engineer:end"
CLAUDE_ROUTER_BEGIN_MARKER="<!-- managed-block:claude-router-pro-mode:begin"
CLAUDE_ROUTER_END_MARKER="<!-- managed-block:claude-router-pro-mode:end"
RECALL_BEGIN_MARKER="<!-- managed-block:historical-recall:begin"
RECALL_END_MARKER="<!-- managed-block:historical-recall:end"

# Dynamically build the Cursor .mdc frontmatter for a platform skill.
# $1 = skill name (e.g. ios-engineer). Description reflects the skill, not a
# hardcoded iOS string, so web-engineer.mdc / backend-engineer.mdc are correct.
cursor_mdc_prologue() {
  local skill="$1"
  printf -- '---\n'
  printf -- 'description: %s skill rules (platform, applied on demand)\n' "${skill}"
  printf -- 'alwaysApply: true\n'
  printf -- '---\n'
}

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Absolute path to the recall CLI, injected into the recall block so it works
# from any working directory (these global context files are used across projects).
RECALL_CLI_PATH="${REPO_ROOT}/skills-engineering/plan-reviews/dist/cli.js"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

resolve_cursor_project_roots() {
  if [[ -n "${CURSOR_PROJECT_ROOTS:-}" ]]; then
    printf '%s\n' "${CURSOR_PROJECT_ROOTS}"
    return
  fi
  python3 - "${REPO_ROOT}/env/config.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    sys.exit(0)

paths = data.get("paths")
if not isinstance(paths, dict):
    sys.exit(0)

roots = paths.get("cursor_project_roots")
if isinstance(roots, str):
    print(roots)
elif isinstance(roots, list):
    print(":".join(str(root) for root in roots if isinstance(root, str) and root.strip()))
PY
}

CURSOR_PROJECT_ROOTS="$(resolve_cursor_project_roots)"

DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-agent-preamble.sh [options]

Renders scripts/templates/agent-preamble.md.tmpl into preamble managed blocks and
generates Cursor .mdc rules from skill references (see sync-manifest in tmpl).

Preamble targets (full agent-preamble block):
  ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, Xcode AGENTS.md / CLAUDE.md

Recall-only targets (historical-recall managed block, no ios-engineer audit):
  ~/.cline/rules/ai-coding-kit-recall.md            (Cline global rules)
  ~/.qwen/QWEN.md                                    (Qwen Code global memory)
  Continue: config.yaml `rules` (injected by sync/platforms/continue.py)

Cursor project rules (from sync-manifest skill:* lines):
  <repo>/.cursor/rules/<skill>.mdc
  <env/config.json paths.cursor_project_roots>/.cursor/rules/<skill>.mdc

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
  local begin_marker="$1"
  local end_marker="$2"
  local tool_name="$3"
  local skills_dir="$4"
  local cr_dir ed_dir pa_dir pg_dir hr_dir
  cr_dir="$(sibling_skill_dir "${skills_dir}" "cognitive-reasoning")"
  ed_dir="$(sibling_skill_dir "${skills_dir}" "engineering-discipline")"
  pa_dir="$(sibling_skill_dir "${skills_dir}" "problem-analysis")"
  pg_dir="$(sibling_skill_dir "${skills_dir}" "plan-grill")"
  hr_dir="$(sibling_skill_dir "${skills_dir}" "historical-recall")"

  # The historical-recall section lives in ONE place in this template (the
  # managed-block:historical-recall block). Full-mode blocks reference it via the
  # {{HISTORICAL_RECALL_BLOCK}} placeholder so the text is never duplicated,
  # while recall-only targets use that block as-is.
  local hr_block_file
  hr_block_file="$(mktemp)"
  awk -v begin="${RECALL_BEGIN_MARKER}" -v end="${RECALL_END_MARKER}" '
    index($0, begin) > 0 { inblock = 1; next }
    inblock && index($0, end) > 0 { exit }
    inblock { print }
  ' "${TEMPLATE}" > "${hr_block_file}"

  awk -v begin="${begin_marker}" \
      -v end="${end_marker}" \
      -v begin_line="${begin_marker} (auto-generated from scripts/templates/agent-preamble.md.tmpl — do not edit; run scripts/sync-agent-preamble.sh) -->" \
      -v end_line="${end_marker} -->" \
      -v phfile="${hr_block_file}" '
    BEGIN { inblock = 0 }
    index($0, begin) > 0 { inblock = 1; print begin_line; next }
    inblock && index($0, end) > 0 { print end_line; exit }
    inblock {
      if ($0 ~ /^<!-- template-note:/) next
      if ($0 == "{{HISTORICAL_RECALL_BLOCK}}") {
        while ((getline l < phfile) > 0) print l
        next
      }
      print
    }
  ' "${TEMPLATE}" | sed -e "s|{{TOOL_NAME}}|${tool_name}|g" \
      -e "s|{{IOS_ENGINEER_SKILLS_DIR}}|${skills_dir}|g" \
      -e "s|{{SKILLS_DIR}}|${skills_dir}|g" \
      -e "s|{{COGNITIVE_REASONING_SKILLS_DIR}}|${cr_dir}|g" \
      -e "s|{{ENGINEERING_DISCIPLINE_SKILLS_DIR}}|${ed_dir}|g" \
      -e "s|{{PROBLEM_ANALYSIS_SKILLS_DIR}}|${pa_dir}|g" \
      -e "s|{{PLAN_GRILL_SKILLS_DIR}}|${pg_dir}|g" \
      -e "s|{{HISTORICAL_RECALL_SKILLS_DIR}}|${hr_dir}|g" \
      -e "s|{{RECALL_CLI_PATH}}|${RECALL_CLI_PATH}|g"

  rm -f "${hr_block_file}"
}

sync_target() {
  local target="$1"
  local tool_name="$2"
  local skills_dir="$3"
  local prologue="${4:-}"
  local begin_marker="${5:-${BEGIN_MARKER}}"
  local end_marker="${6:-${END_MARKER}}"

  mkdir -p "$(dirname "${target}")"

  local rendered new_content
  rendered="$(mktemp)"
  new_content="$(mktemp)"
  render_managed_block "${begin_marker}" "${end_marker}" "${tool_name}" "${skills_dir}" > "${rendered}"

  if [[ ! -f "${target}" ]]; then
    {
      if [[ -n "${prologue}" ]]; then
        printf '%s' "${prologue}"
      fi
      cat "${rendered}"
    } > "${new_content}"
  elif grep -Fq "${begin_marker}" "${target}"; then
    awk -v rendered_file="${rendered}" \
        -v begin="${begin_marker}" \
        -v end="${end_marker}" '
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
  elif [[ "${begin_marker}" == "${BEGIN_MARKER}" ]] && grep -Fq "${LEGACY_BEGIN_MARKER}" "${target}"; then
    awk -v rendered_file="${rendered}" \
        -v begin="${LEGACY_BEGIN_MARKER}" \
        -v end="${LEGACY_END_MARKER}" '
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

remove_managed_block() {
  local target="$1"
  local begin_marker="$2"
  local end_marker="$3"
  local label="$4"
  local new_content

  [[ -f "${target}" ]] || return 0
  if ! grep -Fq "${begin_marker}" "${target}"; then
    return 0
  fi

  new_content="$(mktemp)"
  awk -v begin="${begin_marker}" \
      -v end="${end_marker}" '
    BEGIN { in_block = 0 }
    {
      if (!in_block && index($0, begin) > 0) {
        in_block = 1
        next
      }
      if (in_block && index($0, end) > 0) {
        in_block = 0
        next
      }
      if (!in_block) print
    }
  ' "${target}" > "${new_content}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "--- ${target} (current)"
    echo "+++ ${target} (without ${label})"
    diff -u "${target}" "${new_content}" || true
  else
    cp "${new_content}" "${target}"
    echo "Removed ${label}: ${target}"
  fi

  rm -f "${new_content}"
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

remove_generated_claude_agent_file() {
  local dest="$1"

  [[ -f "${dest}" ]] || return 0
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "Would remove legacy Claude router agent: ${dest}"
  else
    rm -f "${dest}"
    echo "Removed legacy Claude router agent: ${dest}"
  fi
}

remove_generated_claude_agents() {
  local agents_dir="$1"
  remove_generated_claude_agent_file "${agents_dir}/router-agent.md"
  remove_generated_claude_agent_file "${agents_dir}/coder-agent.md"
  remove_generated_claude_agent_file "${agents_dir}/fast-agent.md"
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

# Map a skill name to a project-type token, or empty if it is a
# language-agnostic (always-generate) skill. Convention: <type>-engineer
# maps to project type <type> (ios-engineer -> ios, android-engineer ->
# android, web-engineer -> web, backend-engineer -> backend). Anything else
# (cognitive-reasoning, engineering-discipline, ...) returns empty = always.
skill_project_type() {
  local skill="$1"
  case "${skill}" in
    *-engineer) printf '%s' "${skill%-engineer}" ;;
    *) printf '' ;;
  esac
}

# Generate a Cursor .mdc for a *platform* skill (e.g. ios-engineer) whose rule
# text lives in SKILL.md (not a single references/<name>.md primary file). The
# mdc frontmatter is built per-skill by cursor_mdc_prologue(). Platform skills
# are emitted only when their detected project type matches (gated by caller).
# Stable marker written into every platform .mdc this syncer generates. Deletion
# of a stale .mdc is permitted ONLY when this marker is present, so user-authored
# or unrelated .mdc files (even if named <skill>.mdc) are never removed.
MDC_MANAGED_MARKER='<!-- managed-by: ai-coding-kit sync-agent-preamble -->'

sync_platform_skill_cursor_mdc() {
  local skill="$1"
  local dest="$2"
  local src mdc_generated
  src="${SE_DIR}/${skill}/SKILL.md"
  [[ -f "${src}" ]] || { echo "Platform skill SKILL.md missing for ${skill}: ${src}" >&2; return 1; }
  mdc_generated="$(mktemp)"
  {
    cursor_mdc_prologue "${skill}"
    cat "${src}"
    printf '\n%s\n' "${MDC_MANAGED_MARKER}"
  } > "${mdc_generated}"
  write_file_or_diff "${dest}" "${mdc_generated}"
  rm -f "${mdc_generated}"
}

# Detect a LEGACY platform .mdc produced by the pre-marker sync implementation
# (the old sync_target path that hardcoded ios-engineer.mdc for every external
# project). Such files carry the old `managed-block:agent-preamble` marker but
# NOT the new MDC_MANAGED_MARKER. We accept them for one-time cleanup ONLY when
# BOTH: basename is exactly ios-engineer.mdc AND it matches the legacy fixed
# frontmatter description AND it carries the old managed-block marker. Never
# delete on filename alone, and never apply this legacy grant to other skills.
is_legacy_managed_mdc() {
  local dest="$1"
  local base
  base="$(basename "${dest}")"
  [[ "${base}" == "ios-engineer.mdc" ]] || return 1
  grep -qF "ios-engineer skill usage and audit rules" "${dest}" 2>/dev/null \
    && grep -qF "managed-block:agent-preamble" "${dest}" 2>/dev/null
}

# Controlled removal of a stale platform .mdc generated by this syncer. Deletes
# the file if it carries MDC_MANAGED_MARKER, OR (one-time legacy-migration grant)
# if it is the legacy ios-engineer.mdc format described by is_legacy_managed_mdc.
# A file matching NEITHER is treated as user-authored/unrelated, skipped, and
# warned about. Honors DRY_RUN (shows the deletion diff instead of removing).
# $1 = dest path, $2 = skill name (used to scope the legacy grant to ios-engineer).
delete_mdc_or_diff() {
  local dest="$1"
  local skill="${2:-}"
  if [[ ! -f "${dest}" ]]; then
    return 0
  fi
  # Ownership check: never delete a file we did not generate.
  if ! grep -qF "${MDC_MANAGED_MARKER}" "${dest}" 2>/dev/null; then
    if [[ "${skill}" == "ios-engineer" ]] && is_legacy_managed_mdc "${dest}"; then
      echo "Legacy: ${dest} is a pre-marker ios-engineer.mdc; eligible for one-time cleanup."
    else
      echo "Skip: ${dest} has no managed-by marker; not generated by this syncer, leaving untouched." >&2
      return 0
    fi
  fi
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "--- ${dest} (current)"
    echo "+++ /dev/null (would delete: stale platform skill, type no longer detected)"
    diff -u "${dest}" /dev/null || true
  else
    rm -f "${dest}"
    echo "Deleted: ${dest} (stale platform skill, type no longer detected)"
  fi
}

# Generate Cursor .mdc rules from the sync-manifest skill:* lines.
# $1 = dest root (the project dir). $2 = optional space-separated list of
# detected project types; when non-empty, platform skills (e.g. ios-engineer)
# are generated ONLY if their mapped type is in the list, and a previously
# generated platform .mdc whose type is no longer detected is removed so the
# "on demand" set converges. Language-agnostic skills are always generated.
# Empty $2 = generate everything (legacy/fallback, used for the kit's own root).
sync_manifest_skill_cursor_rules() {
  local dest_root="$1"
  local allowed_types="${2:-}"
  local line skill ptype
  while IFS= read -r line; do
    [[ "${line}" == skill:* ]] || continue
    skill="${line#skill:}"
    [[ -n "${skill}" ]] || continue
    ptype="$(skill_project_type "${skill}")"
    if [[ -n "${ptype}" ]]; then
      # Platform skill: gate by detected project type (empty allowed_types =
      # generate all, used for the kit's own repo root).
      if [[ -n "${allowed_types}" ]] && ! printf '%s' " ${allowed_types} " | grep -q " ${ptype} "; then
        # No longer applicable: remove any stale .mdc we generated earlier so
        # the on-demand set converges when a project changes type.
        delete_mdc_or_diff "${dest_root}/.cursor/rules/${skill}.mdc" "${skill}"
        continue
      fi
      sync_platform_skill_cursor_mdc "${skill}" "${dest_root}/.cursor/rules/${skill}.mdc"
    else
      generate_skill_cursor_mdc "${skill}" "${dest_root}/.cursor/rules/${skill}.mdc"
    fi
  done < <(parse_sync_manifest)
}

# ── Data-driven preamble sync ───────────────────────────────────────────────
# Iterate env/platforms/*.json (the single source of truth). Each platform's
# `preamble` declaration specifies its target file (relative to the install
# root), mode (full | recall), and tool name. Adding a platform = add one JSON
# declaration — no script edits. Xcode (two sub-roots, no single JSON) and
# Cursor (manifest-driven .mdc generation below) remain explicit.

read_preamble() {
  # Emit preamble fields as TAB-separated values for a platform, or nothing.
  local name="$1"
  python3 - "$name" "${REPO_ROOT}/env/platforms" <<'PY'
import json, os, sys
name, pdir = sys.argv[1], sys.argv[2]
path = os.path.join(pdir, name + ".json")
try:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    sys.exit(0)
pre = data.get("preamble")
if not isinstance(pre, dict):
    sys.exit(0)
target = pre.get("target", "")
mode = pre.get("mode", "")
tool = pre.get("tool", name)
fmt = pre.get("format", "markdown")
agents = "1" if pre.get("agents") else "0"
print("|".join([name, target, mode, tool, fmt, agents]))
PY
}

shopt -s nullglob
for cfg_file in "${REPO_ROOT}/env/platforms"/*.json; do
  name="$(basename "$cfg_file" .json)"
  IFS='|' read -r p_name p_target p_mode p_tool p_fmt p_agents \
    < <(read_preamble "$name") || true
  [[ -z "$p_name" || -z "$p_mode" ]] && continue

  root="$(resolve_install_root "$name")"
  [[ -z "$root" ]] && continue

  skills_dir="${root/#$HOME/\~}/skills/ios-engineer/"
  flag_var="SYNC_$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')"
  flag="${!flag_var:-}"

  if [[ "$p_fmt" == "yaml" ]]; then
    echo "Skip ${name} preamble in bash: format=yaml (recall written by sync/platforms/continue.py)."
    continue
  fi

  if [[ "$p_mode" == "full" ]]; then
    if sync_enabled "$flag" "$root"; then
      sync_target "$root/$p_target" "$p_tool" "$skills_dir"
      # Full block already embeds the historical-recall section; drop any
      # stale recall-only block left by a previous recall-mode sync
      # (e.g. a platform flipped from recall -> full such as codebuddy).
      remove_managed_block "$root/$p_target" \
        "${RECALL_BEGIN_MARKER}" \
        "${RECALL_END_MARKER}" \
        "historical-recall"
      if [[ "$name" == "claude" ]]; then
        remove_managed_block "$root/$p_target" \
          "${CLAUDE_ROUTER_BEGIN_MARKER}" \
          "${CLAUDE_ROUTER_END_MARKER}" \
          "Claude router pro mode"
        if [[ "$p_agents" == "1" ]]; then
          remove_generated_claude_agents "$root/agents"
        fi
      fi
    elif [[ -n "$flag" ]]; then
      echo "Skip ${name} preamble: disabled via ${flag_var}=${flag}."
    else
      echo "Skip ${name} preamble: ${root} not found (set ${flag_var}=1 to force)."
    fi
  elif [[ "$p_mode" == "recall" ]]; then
    if sync_enabled "$flag" "$root"; then
      sync_target "$root/$p_target" "$p_tool" "$skills_dir" "" "${RECALL_BEGIN_MARKER}" "${RECALL_END_MARKER}"
    elif [[ -n "$flag" ]]; then
      echo "Skip ${name} recall preamble: disabled via ${flag_var}=${flag}."
    else
      echo "Skip ${name} recall preamble: ${root} not found (set ${flag_var}=1 to force)."
    fi
  else
    echo "Skip ${name} preamble: unknown mode '${p_mode}'."
  fi
done
shopt -u nullglob

# ── Xcode CodingAssistant (two sub-roots, no single platform JSON) ──
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

# REPO_ROOT is the kit itself (meta-engineering); generate every manifest
# skill's .mdc so kit maintainers see all skills locally. External project
# roots below are filtered by detected project type.
sync_manifest_skill_cursor_rules "${REPO_ROOT}"

if [[ -n "${CURSOR_PROJECT_ROOTS}" ]]; then
  DETECT_SH="${SCRIPT_DIR}/detect-project-type.sh"
  IFS=':' read -ra _cursor_roots <<< "${CURSOR_PROJECT_ROOTS}"
  for _root in "${_cursor_roots[@]}"; do
    [[ -z "${_root}" ]] && continue
    if [[ ! -d "${_root}" ]]; then
      echo "Cursor project root not found, skipping: ${_root}" >&2
      continue
    fi
    # Detect the project's type(s); only generate platform skills whose
    # mapped type is detected. Language-agnostic skills are always generated.
    # A failed/empty detection is normalized to "unknown" so that, by design,
    # NO platform skill is generated (not "generate all"). Passing an explicit
    # token here keeps the empty-arg semantics reserved for the kit's own
    # repo root (which intentionally generates every skill).
    _detected=""
    if [[ -f "${DETECT_SH}" ]]; then
      _detected="$("${DETECT_SH}" "${_root}" 2>/dev/null || true)"
    fi
    if [[ -z "${_detected}" || "${_detected}" == "unknown" ]]; then
      _detected="unknown"
      echo "Cursor project ${_root}: no platform signal detected (unknown); generating language-agnostic .mdc only."
    else
      echo "Cursor project ${_root}: detected type(s) -> ${_detected}; generating matching .mdc rules."
    fi
    sync_manifest_skill_cursor_rules "${_root}" "${_detected}"
  done
else
  echo "paths.cursor_project_roots not set in env/config.json; skipping Cursor project .mdc generation on external projects."
fi
