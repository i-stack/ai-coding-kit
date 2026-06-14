#!/usr/bin/env bash

# Install / uninstall the launchd agent that forwards Codex CLI session
# transcripts into the iOS-engineer usage ledger.
#
# The agent triggers on two signals:
#   1. WatchPaths  — fires when ~/.codex/sessions/ directory tree is
#                     modified (new year/month/day subdir, etc.).
#   2. StartInterval — periodic wake every 120s to catch appends into
#                     existing day subdirs that WatchPaths misses.
# ThrottleInterval collapses rapid triggers so we don't hammer disk.
#
# Usage:
#   bash scripts/install_codex_ledger_sync.sh install
#   bash scripts/install_codex_ledger_sync.sh uninstall
#   bash scripts/install_codex_ledger_sync.sh status

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SWEEP_SCRIPT="$SKILL_DIR/scripts/sync_codex_sessions.sh"
LABEL="com.song.codex.ledger-sync"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
SESSIONS_DIR="$HOME/.codex/sessions"
STATE_DIR="$HOME/.claude/hooks/state/ledger-sync"

action="${1:-install}"

write_plist() {
  mkdir -p "$(dirname "$PLIST_PATH")" "$STATE_DIR"
  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SWEEP_SCRIPT</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>$SESSIONS_DIR</string>
    </array>
    <key>StartInterval</key>
    <integer>120</integer>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$STATE_DIR/codex-sweep.out</string>
    <key>StandardErrorPath</key>
    <string>$STATE_DIR/codex-sweep.err</string>
</dict>
</plist>
PLIST
}

case "$action" in
  install)
    if [ ! -x "$SWEEP_SCRIPT" ]; then
      echo "Sweep script not executable: $SWEEP_SCRIPT" >&2
      exit 1
    fi
    if [ ! -d "$SESSIONS_DIR" ]; then
      mkdir -p "$SESSIONS_DIR"
    fi
    write_plist
    # Unload any previous version silently, then load the new one.
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    echo "Installed $LABEL"
    echo "  plist:   $PLIST_PATH"
    echo "  sweep:   $SWEEP_SCRIPT"
    echo "  watches: $SESSIONS_DIR"
    echo "  logs:    $STATE_DIR/codex-sweep.{log,out,err}"
    ;;
  uninstall)
    if [ -f "$PLIST_PATH" ]; then
      launchctl unload "$PLIST_PATH" 2>/dev/null || true
      rm -f "$PLIST_PATH"
      echo "Uninstalled $LABEL"
    else
      echo "Not installed: $PLIST_PATH"
    fi
    ;;
  status)
    if [ -f "$PLIST_PATH" ]; then
      echo "plist present: $PLIST_PATH"
    else
      echo "plist absent:  $PLIST_PATH"
    fi
    launchctl list | awk -v l="$LABEL" '$3 == l {print "launchctl: " $0}' || true
    ;;
  *)
    echo "Usage: $0 {install|uninstall|status}" >&2
    exit 1
    ;;
esac
