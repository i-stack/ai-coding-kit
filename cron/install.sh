#!/usr/bin/env bash
# =============================================================================
# install.sh — 把 ai-coding-kit 同步注册为系统定时任务
#
# 默认在 macOS 上注册 launchd 代理（推荐），也可通过 --cron 改用 crontab。
#
# 用法:
#   bash cron/install.sh                 # 默认每天 09:00 运行（launchd）
#   bash cron/install.sh --hour 3 --minute 30   # 每天 03:30
#   bash cron/install.sh --cron          # 改用 crontab（每天 09:00）
#   bash cron/install.sh --cron --schedule "0 3 * * *"   # 自定义 cron 表达式
#
# 卸载: bash cron/uninstall.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_SYNC="${SCRIPT_DIR}/run-sync.sh"
LABEL="com.aicodingkit.sync"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"

HOUR=9
MINUTE=0
USE_CRON=0
SCHEDULE_SET=0
CRON_SCHEDULE="0 9 * * *"

while [ $# -gt 0 ]; do
  case "$1" in
    --hour) [[ "$2" =~ ^[0-9]+$ ]] && HOUR="$2" || { echo "--hour must be an integer" >&2; exit 1; }; shift 2 ;;
    --minute) [[ "$2" =~ ^[0-9]+$ ]] && MINUTE="$2" || { echo "--minute must be an integer" >&2; exit 1; }; shift 2 ;;
    --cron) USE_CRON=1; shift ;;
    --schedule) CRON_SCHEDULE="$2"; SCHEDULE_SET=1; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# launchd 模式下 --schedule 无意义，给出警告避免静默忽略
if [[ "$USE_CRON" -eq 0 && "${SCHEDULE_SET:-0}" -eq 1 ]]; then
  echo "Warning: --schedule is only used with --cron; ignoring (use --hour/--minute for launchd)." >&2
fi

chmod +x "$RUN_SYNC"

if [ "$USE_CRON" -eq 1 ]; then
  # ---- crontab 方式 ----
  if ! command -v crontab >/dev/null 2>&1; then
    echo "crontab not available on this system." >&2
    exit 1
  fi
  # 去重：移除旧的同标签任务再添加
  ( crontab -l 2>/dev/null | grep -v "$LABEL" ) | crontab -
  ( crontab -l 2>/dev/null; echo "${CRON_SCHEDULE} ${RUN_SYNC} # ${LABEL}" ) | crontab -
  echo "Registered cron job: '${CRON_SCHEDULE} ${RUN_SYNC}'"
  echo "View with: crontab -l"
else
  # ---- launchd 方式（macOS 推荐） ----
  if [ "$(uname)" != "Darwin" ]; then
    echo "launchd is macOS-only. Use --cron on this platform." >&2
    exit 1
  fi
  mkdir -p "$(dirname "$PLIST")"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUN_SYNC}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>${HOUR}</integer>
    <key>Minute</key>
    <integer>${MINUTE}</integer>
  </dict>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>${HOME}/.ai-coding-kit-cron/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>${HOME}/.ai-coding-kit-cron/launchd.err.log</string>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "Registered launchd agent: ${PLIST}"
  echo "Schedule: daily at ${HOUR}:$(printf '%02d' ${MINUTE})"
  echo "Logs: ~/.ai-coding-kit-cron/logs/"
  echo "Unload with: bash cron/uninstall.sh"
fi
