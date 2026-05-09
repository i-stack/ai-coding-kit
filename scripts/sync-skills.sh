#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKILL_NAME="${SKILL_NAME:-ios-engineer}"
SOURCE_DIR="${SOURCE_DIR:-${REPO_ROOT}/${SKILL_NAME}}"

CODEX_DEST_BASE="${CODEX_DEST_BASE:-${HOME}/.codex/skills}"
CLAUDE_DEST_BASE="${CLAUDE_DEST_BASE:-${HOME}/.claude/skills}"
CURSOR_DEST_BASE="${CURSOR_DEST_BASE:-${HOME}/.cursor/skills}"

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

TARGETS=(
  "${CODEX_DEST_BASE}/${SKILL_NAME}"
  "${CLAUDE_DEST_BASE}/${SKILL_NAME}"
  "${CURSOR_DEST_BASE}/${SKILL_NAME}"
)

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
