#!/usr/bin/env bash

# Claude Code Stop hook: detect whether the just-ended turn looks like an
# iOS engineering task, and if so, check that the last assistant text
# message contains a <usage-audit>...</usage-audit> block.
#
# Designed to be symlinked into ~/.claude/hooks/. Resolves its real path
# via python so the companion .py file is found regardless of how the
# wrapper was invoked.
#
# Modes (AUDIT_CHECK_MODE env var):
#   observe (default)   never blocks; appends decision lines to the log
#   block               emits {"decision":"block","reason":"..."} when an
#                       iOS task lacks an audit block, prompting Claude
#                       to continue and add it
#   off                 short-circuit, no work
#
# Always exits 0.

set -u

MODE="${AUDIT_CHECK_MODE:-observe}"

if [ "$MODE" = "off" ]; then
  exit 0
fi

LOG_DIR="$HOME/.claude/hooks/state/audit-check"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/missing-audit.log"
DEBUG_FILE="$LOG_DIR/debug.log"

SELF="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0")"
HOOK_DIR="$(dirname "$SELF")"
CHECKER="$HOOK_DIR/audit-check-on-stop.py"

if [ ! -f "$CHECKER" ]; then
  printf '[%s] checker-missing|%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$CHECKER" >> "$DEBUG_FILE"
  exit 0
fi

result="$(python3 "$CHECKER" 2>>"$DEBUG_FILE" || true)"
ts="$(date '+%Y-%m-%dT%H:%M:%S%z')"

case "$result" in
  OK\|*)
    printf '[%s] %s\n' "$ts" "$result" >> "$LOG_FILE"

    is_ios="$(printf '%s' "$result" | sed -n 's/.*is_ios=\([01]\).*/\1/p')"
    has_audit="$(printf '%s' "$result" | sed -n 's/.*has_audit=\([01]\).*/\1/p')"

    if [ "$MODE" = "block" ] && [ "$is_ios" = "1" ] && [ "$has_audit" = "0" ]; then
      cat <<'JSON'
{"decision":"block","reason":"iOS engineering task detected but <usage-audit> block is missing. Per ~/.claude/CLAUDE.md (# ios-engineer skill audit), append the block now following the schema in ios-engineer/references/usage_ledger.md section 4."}
JSON
    fi
    ;;
  "")
    printf '[%s] EMPTY|checker-failed\n' "$ts" >> "$DEBUG_FILE"
    ;;
  *)
    printf '[%s] %s\n' "$ts" "$result" >> "$DEBUG_FILE"
    ;;
esac

exit 0
