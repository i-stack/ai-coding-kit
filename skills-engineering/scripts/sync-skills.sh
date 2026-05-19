#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

LOCAL_CONFIG="${SCRIPT_DIR}/config.local.sh"
if [[ -f "${LOCAL_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${LOCAL_CONFIG}"
fi

CODEX_DEST_BASE="${CODEX_DEST_BASE:-${HOME}/.codex/skills}"
CLAUDE_DEST_BASE="${CLAUDE_DEST_BASE:-${HOME}/.claude/skills}"
CURSOR_DEST_BASE="${CURSOR_DEST_BASE:-${HOME}/.cursor/skills}"
XCODE_CODEX_DEST_BASE="${XCODE_CODEX_DEST_BASE:-${HOME}/Library/Developer/Xcode/CodingAssistant/codex/skills}"
XCODE_CLAUDE_DEST_BASE="${XCODE_CLAUDE_DEST_BASE:-${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/skills}"

CLAUDE_ROOT="${HOME}/.claude"
CODEX_ROOT="${HOME}/.codex"
CURSOR_ROOT="${HOME}/.cursor"
XCODE_CODEX_ROOT="${HOME}/Library/Developer/Xcode/CodingAssistant/codex"
XCODE_CLAUDE_ROOT="${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig"

WATCH_MODE=false
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-skills.sh [options]

Syncs SKILL.md + references/ for each skill under skills-engineering/ to local
Agent skill directories (Codex, Claude, Cursor, Xcode paths).

Options:
  --watch        Keep watching and auto-sync on change
  --dry-run      Print rsync actions without writing files
  -h, --help     Show help

Environment variables:
  SKILL_NAME       Sync only this skill (e.g. ios-engineer)
  SKILL_NAMES      Colon-separated list (e.g. ios-engineer:cognitive-expansion)
  SOURCE_DIR       Override source when SKILL_NAME is set (default: <repo>/<SKILL_NAME>)
  CODEX_DEST_BASE  Default: ~/.codex/skills
  CLAUDE_DEST_BASE Default: ~/.claude/skills
  CURSOR_DEST_BASE Default: ~/.cursor/skills
  XCODE_CODEX_DEST_BASE / XCODE_CLAUDE_DEST_BASE  Xcode skill paths

If neither SKILL_NAME nor SKILL_NAMES is set, syncs every directory under
skills-engineering/ that contains a SKILL.md file.

Sync target gating (per-tool; values: 1=force on, 0=force off, unset=auto-detect):
  SYNC_CLAUDE, SYNC_CODEX, SYNC_CURSOR, SYNC_XCODE_CODEX, SYNC_XCODE_CLAUDE
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch) WATCH_MODE=true ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
  shift
done

discover_skills() {
  local d name
  for d in "${REPO_ROOT}"/*/; do
    [[ -f "${d}/SKILL.md" ]] || continue
    name="$(basename "${d}")"
    echo "${name}"
  done | sort
}

resolve_skill_list() {
  SKILL_LIST=()
  if [[ -n "${SKILL_NAME:-}" ]]; then
    SKILL_LIST=("${SKILL_NAME}")
    return
  fi
  if [[ -n "${SKILL_NAMES:-}" ]]; then
    IFS=':' read -ra SKILL_LIST <<< "${SKILL_NAMES}"
    return
  fi
  local s
  while IFS= read -r s; do
    [[ -n "${s}" ]] && SKILL_LIST+=("${s}")
  done < <(discover_skills)
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

build_dest_bases() {
  DEST_BASES=()
  if sync_enabled "${SYNC_CLAUDE:-}" "${CLAUDE_ROOT}"; then
    DEST_BASES+=("${CLAUDE_DEST_BASE}")
  elif [[ -n "${SYNC_CLAUDE:-}" ]]; then
    echo "Skip Claude sync: disabled via SYNC_CLAUDE=${SYNC_CLAUDE}."
  else
    echo "Skip Claude sync: ${CLAUDE_ROOT} not found (set SYNC_CLAUDE=1 to force)."
  fi
  if sync_enabled "${SYNC_CODEX:-}" "${CODEX_ROOT}"; then
    DEST_BASES+=("${CODEX_DEST_BASE}")
  elif [[ -n "${SYNC_CODEX:-}" ]]; then
    echo "Skip Codex sync: disabled via SYNC_CODEX=${SYNC_CODEX}."
  else
    echo "Skip Codex sync: ${CODEX_ROOT} not found (set SYNC_CODEX=1 to force)."
  fi
  if sync_enabled "${SYNC_CURSOR:-}" "${CURSOR_ROOT}"; then
    DEST_BASES+=("${CURSOR_DEST_BASE}")
  elif [[ -n "${SYNC_CURSOR:-}" ]]; then
    echo "Skip Cursor sync: disabled via SYNC_CURSOR=${SYNC_CURSOR}."
  else
    echo "Skip Cursor sync: ${CURSOR_ROOT} not found (set SYNC_CURSOR=1 to force)."
  fi
  if sync_enabled "${SYNC_XCODE_CODEX:-}" "${XCODE_CODEX_ROOT}"; then
    DEST_BASES+=("${XCODE_CODEX_DEST_BASE}")
  elif [[ -n "${SYNC_XCODE_CODEX:-}" ]]; then
    echo "Skip Xcode Codex sync: disabled via SYNC_XCODE_CODEX=${SYNC_XCODE_CODEX}."
  else
    echo "Skip Xcode Codex sync: ${XCODE_CODEX_ROOT} not found (set SYNC_XCODE_CODEX=1 to force)."
  fi
  if sync_enabled "${SYNC_XCODE_CLAUDE:-}" "${XCODE_CLAUDE_ROOT}"; then
    DEST_BASES+=("${XCODE_CLAUDE_DEST_BASE}")
  elif [[ -n "${SYNC_XCODE_CLAUDE:-}" ]]; then
    echo "Skip Xcode Claude sync: disabled via SYNC_XCODE_CLAUDE=${SYNC_XCODE_CLAUDE}."
  else
    echo "Skip Xcode Claude sync: ${XCODE_CLAUDE_ROOT} not found (set SYNC_XCODE_CLAUDE=1 to force)."
  fi
}

ensure_target_parent() {
  mkdir -p "$(dirname "$1")"
}

ensure_real_dir_target() {
  local target="$1"
  if [[ -L "${target}" ]]; then
    rm "${target}"
  fi
  mkdir -p "${target}"
}

sync_one_skill_to_target() {
  local source_dir="$1"
  local target="$2"
  ensure_target_parent "${target}"
  ensure_real_dir_target "${target}"

  local rsync_flags=(-a --delete --delete-excluded \
    --include "/SKILL.md" \
    --include "/references/" --include "/references/**" \
    --exclude "*")
  if [[ "${DRY_RUN}" == "true" ]]; then
    rsync_flags+=(--dry-run --itemize-changes)
  fi

  rsync "${rsync_flags[@]}" "${source_dir}/" "${target}/"
  echo "Synced ${source_dir} -> ${target}"
}

sync_all_skills() {
  local skill source_dir base
  for skill in "${SKILL_LIST[@]}"; do
    if [[ -n "${SKILL_NAME:-}" && -n "${SOURCE_DIR:-}" ]]; then
      source_dir="${SOURCE_DIR}"
    else
      source_dir="${REPO_ROOT}/${skill}"
    fi
    if [[ ! -d "${source_dir}" ]]; then
      echo "Source skill directory not found: ${source_dir}" >&2
      exit 1
    fi
    for base in "${DEST_BASES[@]}"; do
      sync_one_skill_to_target "${source_dir}" "${base}/${skill}"
    done
  done
}

resolve_skill_list
build_dest_bases

if [[ ${#SKILL_LIST[@]} -eq 0 ]]; then
  echo "No skills to sync (no SKILL.md found under ${REPO_ROOT})." >&2
  exit 1
fi

if [[ ${#DEST_BASES[@]} -eq 0 ]]; then
  echo "No sync targets enabled; nothing to do."
  exit 0
fi

echo "Syncing skills: ${SKILL_LIST[*]}"

watch_and_sync() {
  local watch_paths=()
  local skill
  for skill in "${SKILL_LIST[@]}"; do
    watch_paths+=("${REPO_ROOT}/${skill}")
  done
  if command -v fswatch >/dev/null 2>&1; then
    echo "Watching skill dirs with fswatch ..."
    fswatch -o "${watch_paths[@]}" | while read -r _; do
      sync_all_skills
    done
  else
    echo "fswatch not found. Install with: brew install fswatch" >&2
    echo "Fallback to polling every 2 seconds..." >&2
    local last_hash=""
    while true; do
      local current_hash
      current_hash="$(find "${watch_paths[@]}" -type f ! -name ".DS_Store" -print0 | xargs -0 shasum 2>/dev/null | shasum | awk '{print $1}')"
      if [[ "${current_hash}" != "${last_hash}" ]]; then
        sync_all_skills
        last_hash="${current_hash}"
      fi
      sleep 2
    done
  fi
}

sync_all_skills

if [[ "${WATCH_MODE}" == "true" ]]; then
  watch_and_sync
fi
