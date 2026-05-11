#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

LOCAL_CONFIG="${SCRIPT_DIR}/config.local.sh"
if [[ -f "${LOCAL_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${LOCAL_CONFIG}"
fi

SKILL_NAME="${SKILL_NAME:-ios-engineer}"
SOURCE_DIR="${SOURCE_DIR:-${REPO_ROOT}/${SKILL_NAME}}"

CODEX_DEST_BASE="${CODEX_DEST_BASE:-${HOME}/.codex/skills}"
CLAUDE_DEST_BASE="${CLAUDE_DEST_BASE:-${HOME}/.claude/skills}"
CURSOR_DEST_BASE="${CURSOR_DEST_BASE:-${HOME}/.cursor/skills}"

CLAUDE_ROOT="${HOME}/.claude"
CODEX_ROOT="${HOME}/.codex"
CURSOR_ROOT="${HOME}/.cursor"

WATCH_MODE=false
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-skills.sh [options]

Options:
  --watch        Keep watching and auto-sync on change
  --dry-run      Print rsync actions without writing files
  -h, --help     Show help

Environment variables:
  SKILL_NAME       Default: ios-engineer
  SOURCE_DIR       Default: <repo>/<SKILL_NAME>
  CODEX_DEST_BASE  Default: ~/.codex/skills
  CLAUDE_DEST_BASE Default: ~/.claude/skills
  CURSOR_DEST_BASE Default: ~/.cursor/skills

Sync target gating (per-tool; values: 1=force on, 0=force off, unset=auto-detect
via ~/.claude, ~/.codex, ~/.cursor existence):
  SYNC_CLAUDE      Enable Claude sync
  SYNC_CODEX       Enable Codex sync
  SYNC_CURSOR      Enable Cursor sync
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch)
      WATCH_MODE=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Source skill directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

# Decide whether a given tool's sync should run.
# $1: value of SYNC_* env var (possibly empty)
# $2: tool root dir (e.g. $HOME/.claude) — probed when flag is unset
sync_enabled() {
  local flag="$1"
  local root_dir="$2"
  case "${flag}" in
    1|true|yes|on)  return 0 ;;
    0|false|no|off) return 1 ;;
    "")             [[ -d "${root_dir}" ]] ;;
    *)
      echo "Invalid SYNC_* flag value: '${flag}' (expected 1/0/true/false/yes/no/on/off)" >&2
      return 1
      ;;
  esac
}

TARGETS=()
if sync_enabled "${SYNC_CLAUDE:-}" "${CLAUDE_ROOT}"; then
  TARGETS+=("${CLAUDE_DEST_BASE}/${SKILL_NAME}")
elif [[ -n "${SYNC_CLAUDE:-}" ]]; then
  echo "Skip Claude sync: disabled via SYNC_CLAUDE=${SYNC_CLAUDE}."
else
  echo "Skip Claude sync: ${CLAUDE_ROOT} not found (set SYNC_CLAUDE=1 to force)."
fi
if sync_enabled "${SYNC_CODEX:-}" "${CODEX_ROOT}"; then
  TARGETS+=("${CODEX_DEST_BASE}/${SKILL_NAME}")
elif [[ -n "${SYNC_CODEX:-}" ]]; then
  echo "Skip Codex sync: disabled via SYNC_CODEX=${SYNC_CODEX}."
else
  echo "Skip Codex sync: ${CODEX_ROOT} not found (set SYNC_CODEX=1 to force)."
fi
if sync_enabled "${SYNC_CURSOR:-}" "${CURSOR_ROOT}"; then
  TARGETS+=("${CURSOR_DEST_BASE}/${SKILL_NAME}")
elif [[ -n "${SYNC_CURSOR:-}" ]]; then
  echo "Skip Cursor sync: disabled via SYNC_CURSOR=${SYNC_CURSOR}."
else
  echo "Skip Cursor sync: ${CURSOR_ROOT} not found (set SYNC_CURSOR=1 to force)."
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "No sync targets enabled; nothing to do."
  exit 0
fi

ensure_target_parent() {
  local target="$1"
  mkdir -p "$(dirname "${target}")"
}

ensure_real_dir_target() {
  local target="$1"
  if [[ -L "${target}" ]]; then
    rm "${target}"
  fi
  mkdir -p "${target}"
}

sync_one() {
  local target="$1"
  ensure_target_parent "${target}"
  ensure_real_dir_target "${target}"

  local rsync_flags=(-a --delete --delete-excluded \
    --include "/SKILL.md" \
    --include "/references/" --include "/references/**" \
    --exclude "*")
  if [[ "${DRY_RUN}" == "true" ]]; then
    rsync_flags+=(--dry-run --itemize-changes)
  fi

  rsync "${rsync_flags[@]}" "${SOURCE_DIR}/" "${target}/"
  echo "Synced ${SOURCE_DIR} -> ${target}"
}

sync_all() {
  for target in "${TARGETS[@]}"; do
    sync_one "${target}"
  done
}

watch_and_sync() {
  if command -v fswatch >/dev/null 2>&1; then
    echo "Watching ${SOURCE_DIR} with fswatch ..."
    fswatch -o "${SOURCE_DIR}" | while read -r _; do
      sync_all
    done
  else
    echo "fswatch not found. Install with: brew install fswatch" >&2
    echo "Fallback to polling every 2 seconds..." >&2
    local last_hash=""
    while true; do
      local current_hash
      current_hash="$(find "${SOURCE_DIR}" -type f ! -name ".DS_Store" -print0 | xargs -0 shasum | shasum | awk '{print $1}')"
      if [[ "${current_hash}" != "${last_hash}" ]]; then
        sync_all
        last_hash="${current_hash}"
      fi
      sleep 2
    done
  fi
}

sync_all

if [[ "${WATCH_MODE}" == "true" ]]; then
  watch_and_sync
fi
