#!/usr/bin/env bash

# Symlink the ios-engineer skill's Claude Code hooks into ~/.claude/hooks/
# so the harness picks them up. This keeps a single source of truth in the
# repo: edit hooks here, every machine that ran this script sees the change
# on next session-end.
#
# Idempotent. Existing non-symlink files at the destination are backed up
# to <name>.bak.<unixtime> before being replaced. Existing correct symlinks
# are left untouched.
#
# Does not edit ~/.claude/settings.json — settings.json holds secrets, so
# we print the snippet you need to add (or merge into an existing Stop
# hooks list) instead of patching the file in place.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

LOCAL_CONFIG="${SCRIPT_DIR}/config.local.sh"
if [[ -f "${LOCAL_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${LOCAL_CONFIG}"
fi

SKILL_NAME="${SKILL_NAME:-ios-engineer}"
SOURCE_HOOKS_DIR="${SOURCE_HOOKS_DIR:-${REPO_ROOT}/${SKILL_NAME}/hooks}"
CLAUDE_HOOKS_DIR="${CLAUDE_HOOKS_DIR:-${HOME}/.claude/hooks}"

DRY_RUN=false

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-claude-hooks.sh [options]

Options:
  --dry-run    Print actions without modifying anything
  -h, --help   Show help

Environment variables:
  SKILL_NAME         Default: ios-engineer
  SOURCE_HOOKS_DIR   Default: <repo>/<SKILL_NAME>/hooks
  CLAUDE_HOOKS_DIR   Default: ~/.claude/hooks
  SYNC_CLAUDE_HOOKS  1=force on, 0=force off, unset=auto-detect via ~/.claude
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

# Gating: same convention as sync-skills.sh.
case "${SYNC_CLAUDE_HOOKS:-auto}" in
  0|false|no|off)
    echo "sync-claude-hooks: disabled via SYNC_CLAUDE_HOOKS=${SYNC_CLAUDE_HOOKS}"
    exit 0
    ;;
  1|true|yes|on) ;;
  auto|"")
    if [[ ! -d "${HOME}/.claude" ]]; then
      echo "sync-claude-hooks: ~/.claude not found, skipping (set SYNC_CLAUDE_HOOKS=1 to force)"
      exit 0
    fi
    ;;
  *)
    echo "sync-claude-hooks: invalid SYNC_CLAUDE_HOOKS=${SYNC_CLAUDE_HOOKS} (use 1/0)" >&2
    exit 1
    ;;
esac

if [[ ! -d "${SOURCE_HOOKS_DIR}" ]]; then
  echo "sync-claude-hooks: source dir not found: ${SOURCE_HOOKS_DIR}" >&2
  exit 1
fi

# Whitelist of files we manage. Anything else in the source dir (README,
# fixtures, etc.) is intentionally not symlinked.
HOOK_FILES=(
  "ledger-sync-on-stop.sh"
  "audit-check-on-stop.sh"
  "audit-check-on-stop.py"
)

run() {
  if $DRY_RUN; then
    printf 'DRY-RUN: %s\n' "$*"
  else
    "$@"
  fi
}

mkdir -p "${CLAUDE_HOOKS_DIR}"

linked=()
already=()
backed_up=()
missing=()

for name in "${HOOK_FILES[@]}"; do
  src="${SOURCE_HOOKS_DIR}/${name}"
  dest="${CLAUDE_HOOKS_DIR}/${name}"

  if [[ ! -f "${src}" ]]; then
    missing+=("${src}")
    continue
  fi

  # Ensure source is executable so the symlinked target inherits exec bit.
  if [[ ! -x "${src}" ]]; then
    run chmod +x "${src}"
  fi

  if [[ -L "${dest}" ]]; then
    # Symlink already present. If it points at our source, leave it alone.
    current_target="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "${dest}")"
    expected_target="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "${src}")"
    if [[ "${current_target}" == "${expected_target}" ]]; then
      already+=("${dest}")
      continue
    fi
    # Symlink elsewhere — back it up by removing it (it carries no content).
    run rm -f "${dest}"
  elif [[ -e "${dest}" ]]; then
    # Real file. Back up before replacing.
    bak="${dest}.bak.$(date +%s)"
    run mv "${dest}" "${bak}"
    backed_up+=("${dest} -> ${bak}")
  fi

  run ln -s "${src}" "${dest}"
  linked+=("${dest} -> ${src}")
done

# ---------- Report ----------

echo
echo "sync-claude-hooks: source     ${SOURCE_HOOKS_DIR}"
echo "sync-claude-hooks: target     ${CLAUDE_HOOKS_DIR}"
$DRY_RUN && echo "sync-claude-hooks: DRY-RUN (no changes written)"
echo

if (( ${#linked[@]} > 0 )); then
  echo "Symlinks created:"
  printf '  %s\n' "${linked[@]}"
fi
if (( ${#already[@]} > 0 )); then
  echo "Already correct:"
  printf '  %s\n' "${already[@]}"
fi
if (( ${#backed_up[@]} > 0 )); then
  echo "Backed up:"
  printf '  %s\n' "${backed_up[@]}"
fi
if (( ${#missing[@]} > 0 )); then
  echo "MISSING in source (skipped):" >&2
  printf '  %s\n' "${missing[@]}" >&2
fi

cat <<EOF

Add the following Stop hooks to ~/.claude/settings.json (merge into an
existing "hooks.Stop[].hooks" array if present):

  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_HOOKS_DIR}/ledger-sync-on-stop.sh",
            "timeout": 30
          },
          {
            "type": "command",
            "command": "${CLAUDE_HOOKS_DIR}/audit-check-on-stop.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }

audit-check-on-stop.sh respects AUDIT_CHECK_MODE (observe|block|off);
default is "observe" — log only, never blocks. Switch to "block" via
launchctl/shell after you've triaged the log for false positives.
EOF
