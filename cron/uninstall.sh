#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — 移除 ai-coding-kit 定时同步任务
#   同时清理 launchd 代理与 crontab 中的同标签任务。
# =============================================================================
set -uo pipefail

LABEL="com.aicodingkit.sync"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"

# launchd
if [ -f "$PLIST" ]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed launchd agent: $PLIST"
else
  echo "No launchd agent found."
fi

# crontab
if command -v crontab >/dev/null 2>&1; then
  if crontab -l 2>/dev/null | grep -q "$LABEL"; then
    ( crontab -l 2>/dev/null | grep -v "$LABEL" ) | crontab -
    echo "Removed cron job for ${LABEL}."
  fi
fi

echo "Done. Logs in ~/.ai-coding-kit-cron/ are left intact."
