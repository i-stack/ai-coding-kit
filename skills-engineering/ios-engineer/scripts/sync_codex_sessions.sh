#!/usr/bin/env bash

# Sweep recent Codex CLI session JSONL files under ~/.codex/sessions/ and
# forward any that have been idle (no writes) for >= IDLE_SEC seconds to
# scripts/sync_transcript_to_ledger.sh. Invoked by the launchd WatchPaths
# job com.song.codex.ledger-sync; see scripts/install_codex_ledger_sync.sh
# for setup.
#
# Design notes:
# - Codex has no native session-end hook. This script is idempotent: the
#   sync script maintains per-transcript offset files, so re-running on the
#   same still-growing transcript is cheap and safe.
# - The idle filter (mtime >= IDLE_SEC seconds ago) is a coarse "session
#   end" proxy. Mid-session polls are allowed: a complete <usage-audit>
#   block always appears inside a single assistant response JSONL line,
#   written atomically by Codex, so partial blocks are not a concern in
#   practice. The idle filter just reduces churn.
# - Lookback window (LOOKBACK_MIN minutes) limits how far back we walk —
#   anything older than this is considered ingested already and skipped.
# - All stderr is swallowed: this runs unattended under launchd, failures
#   must never block the user.

set -u

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SYNC_SCRIPT="$SKILL_DIR/scripts/sync_transcript_to_ledger.sh"
SESSIONS_DIR="${CODEX_SESSIONS_DIR:-$HOME/.codex/sessions}"
IDLE_SEC="${CODEX_LEDGER_IDLE_SEC:-30}"
LOOKBACK_MIN="${CODEX_LEDGER_LOOKBACK_MIN:-2880}"  # 2 days
STATE_DIR="${CLAUDE_LEDGER_SYNC_STATE_DIR:-$HOME/.claude/hooks/state/ledger-sync}"
LOG_FILE="$STATE_DIR/codex-sweep.log"

mkdir -p "$STATE_DIR"

if [ ! -d "$SESSIONS_DIR" ]; then
  exit 0
fi

if [ ! -x "$SYNC_SCRIPT" ]; then
  printf '[%s] sweep skipped: sync script missing or not executable: %s\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_SCRIPT" >> "$LOG_FILE"
  exit 0
fi

now="$(date +%s)"
processed=0
synced=0

while IFS= read -r -d '' file; do
  mtime="$(stat -f %m "$file" 2>/dev/null || echo 0)"
  age=$((now - mtime))
  if [ "$age" -lt "$IDLE_SEC" ]; then
    continue
  fi
  processed=$((processed + 1))
  if "$SYNC_SCRIPT" "$file" >/dev/null 2>&1; then
    synced=$((synced + 1))
  fi
done < <(find "$SESSIONS_DIR" -type f -name '*.jsonl' -mmin "-$LOOKBACK_MIN" -print0 2>/dev/null)

if [ "$processed" -gt 0 ]; then
  printf '[%s] codex sweep: processed=%s synced=%s idle>=%ss lookback=%smin\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$processed" "$synced" "$IDLE_SEC" "$LOOKBACK_MIN" \
    >> "$LOG_FILE"
fi

exit 0
