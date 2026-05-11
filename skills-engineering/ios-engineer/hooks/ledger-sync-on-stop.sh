#!/usr/bin/env bash

# Claude Code Stop hook: forward the just-ended session's transcript to the
# ios-engineer skill's ledger sync script, so any <usage-audit> blocks the
# assistant emitted during the session land in evolution/usage/usage.jsonl.
#
# Designed to be symlinked into ~/.claude/hooks/. The script resolves its
# own real path (through the symlink) to find the repository it lives in,
# so the same file works on every machine regardless of where the repo
# was cloned.
#
# Payload (JSON on stdin):
#   transcript_path  absolute path to the session JSONL
#   session_id       UUID
#
# Always exits 0: a ledger sync failure must not stop the user from ending
# their session. Failures are logged for later inspection.

set -u

# Resolve the hook's real path even when invoked through a symlink.
# python3 is required for the JSONL handling downstream anyway.
SELF="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0")"
HOOK_DIR="$(dirname "$SELF")"
SKILL_DIR="$(cd "$HOOK_DIR/.." && pwd -P)"
SYNC_SCRIPT="$SKILL_DIR/scripts/sync_transcript_to_ledger.sh"

LOG_FILE="$HOME/.claude/hooks/state/ledger-sync/sync.log"
mkdir -p "$(dirname "$LOG_FILE")"

payload="$(cat)"

fields="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get("transcript_path") or "")
print(d.get("session_id") or "")
' 2>/dev/null || true)"

transcript_path="$(printf '%s\n' "$fields" | sed -n '1p')"
session_id="$(printf '%s\n' "$fields" | sed -n '2p')"

if [ -z "$transcript_path" ] || [ ! -f "$transcript_path" ]; then
  exit 0
fi

if [ ! -x "$SYNC_SCRIPT" ]; then
  printf '[%s] hook skipped: sync script missing or not executable: %s\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_SCRIPT" >> "$LOG_FILE"
  exit 0
fi

"$SYNC_SCRIPT" "$transcript_path" "$session_id" >/dev/null 2>&1 || true
exit 0
