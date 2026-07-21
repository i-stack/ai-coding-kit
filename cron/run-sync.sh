#!/usr/bin/env bash
# =============================================================================
# run-sync.sh — 定时同步执行体（被 launchd / cron 调用）
#
# 做「set-and-forget」式配置同步：
#   1. 仅当 env/secrets.json 存在时才真正同步（否则跳过，不报错）
#   2. 运行 sync.sh（MCP + 平台配置）
#   3. 运行 skills-engineering 的技能同步 + preamble 同步 + 校验
#   4. 全程日志写入 ~/.ai-coding-kit-cron/logs/
#
# 该脚本本身不依赖任何调度器；调度由 cron/install.sh 注册。
# =============================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${HOME}/.ai-coding-kit-cron/logs"
mkdir -p "$LOG_DIR"
TS="$(date '+%Y%m%d-%H%M%S')"
LOG_FILE="${LOG_DIR}/sync-${TS}.log"
# 保留最近 30 个日志（BSD head 不支持 -n 负数，改用 ls -t + tail -n +31 实现 macOS 兼容）
ls -t "$LOG_DIR"/sync-*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== ai-coding-kit scheduled sync start (pid $$) ==="

if [ ! -f "${REPO_ROOT}/env/secrets.json" ]; then
  log "SKIP: env/secrets.json not found — run 'cp env/secrets.json.example env/secrets.json' first."
  log "=== sync skipped ==="
  exit 0
fi

# 1) MCP + 平台配置同步
log "[1/2] sync.sh (MCP + platforms)"
if bash "${REPO_ROOT}/sync.sh" >>"$LOG_FILE" 2>&1; then
  log "  sync.sh OK"
else
  log "  sync.sh FAILED (see log) — continuing to skill sync"
fi

# 2) 技能同步 + preamble + 校验
log "[2/2] skills-engineering sync + verify"
SE="${REPO_ROOT}/skills-engineering"
if [ -d "$SE" ]; then
  bash "${SE}/scripts/sync-skills.sh" >>"$LOG_FILE" 2>&1 && log "  sync-skills.sh OK" || log "  sync-skills.sh FAILED"
  bash "${SE}/scripts/sync-agent-preamble.sh" >>"$LOG_FILE" 2>&1 && log "  sync-agent-preamble.sh OK" || log "  sync-agent-preamble.sh FAILED"
  bash "${SE}/scripts/sync-user-profile.sh" >>"$LOG_FILE" 2>&1 && log "  sync-user-profile.sh OK" || log "  sync-user-profile.sh FAILED"
  bash "${SE}/scripts/verify-sync.sh" >>"$LOG_FILE" 2>&1 && log "  verify-sync.sh OK" || log "  verify-sync.sh FAILED"
fi

log "=== ai-coding-kit scheduled sync done ==="
