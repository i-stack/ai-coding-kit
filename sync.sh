#!/usr/bin/env bash
# =============================================================================
# ai-coding-kit 一键同步脚本
#
# 用法:
#   bash sync.sh                 # 同步所有平台的 MCP 和配置
#   bash sync.sh --force         # 强制执行同步（跳过检查提示）
#
# 配置文件（已提交到 Git，开箱即用）:
#   env/mcp/              — MCP 服务器定义（敏感值用 ${VAR} 占位）
#   env/platforms/        — 各平台专属配置（敏感值用 ${VAR} 占位）
#   env/templates/        — 新增 MCP/平台的模板
#
# 用户唯一需要配置的文件:
#   env/secrets.json       — 填写 API Keys / Tokens
#   （从 env/secrets.json.example 复制并编辑）
#
# 此脚本会：
#   1. 检查 env/secrets.json 是否存在（不存在则提示创建）
#   2. 执行 sync/scripts/sync_all.sh 同步配置到各 AI 编码工具
#      并按 env/user-profile.json 可选同步跨会话用户画像
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$SCRIPT_DIR/env/mcp"
SECRETS_FILE="$SCRIPT_DIR/env/secrets.json"
SECRETS_EXAMPLE="$SCRIPT_DIR/env/secrets.json.example"

# --- 颜色输出 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo_step()  { echo -e "${CYAN}==>${NC} $*"; }
echo_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
echo_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- 参数解析 ---
FORCE=false
if [ "${1:-}" = "--force" ]; then
  FORCE=true
fi

# --- 检查 secrets.json ---
check_secrets() {
  if [ ! -f "$SECRETS_FILE" ]; then
    echo_error "env/secrets.json 不存在！"
    echo ""
    echo -e "  ${CYAN}# 这是你唯一需要配置的文件：${NC}"
    echo -e "  ${CYAN}cp env/secrets.json.example env/secrets.json${NC}"
    echo -e "  ${CYAN}\$EDITOR env/secrets.json${NC}"
    echo ""
    echo -e "  填入你的 API Keys，然后重新运行 bash sync.sh"
    exit 1
  fi
}

# --- 检查 MCP 配置 ---
check_mcp() {
  if [ ! -d "$MCP_DIR" ] || [ -z "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ]; then
    echo_warn "env/mcp/ 目录下没有 MCP 配置文件。"
    echo_warn "MCP 配置文件已包含在仓库中 — 请确认 env/mcp/*.json 存在。"
    exit 1
  fi
}

# --- 执行同步 ---
run_sync() {
  echo_step "开始同步配置到各 AI 编码工具..."
  echo ""

  # 调用 sync_all.sh 执行全部同步
  bash "$SCRIPT_DIR/sync/scripts/sync_all.sh"

  echo ""
  echo_ok "同步完成！"
  echo ""
  echo -e "${CYAN}已同步目标：${NC}"
  echo -e "  • Cursor           (~/.cursor/mcp.json)"
  echo -e "  • CodeBuddy        (~/.codebuddy/mcp.json, models.json, skills)"
  echo -e "  • Codex CLI        (~/.codex/config.toml)"
  echo -e "  • Xcode Codex      (~/Library/Developer/Xcode/CodingAssistant/codex/)"
  echo -e "  • Claude Code      (~/.claude.json, settings.json)"
  echo -e "  • Xcode Claude     (~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/)"
  echo -e "  • Cline            (~/.cline/data/globalState.json, secrets.json, skills)"
  echo -e "  • Gemini CLI       (~/.gemini/settings.json, ~/.zshrc env)"
  echo -e "  • Continue         (~/.continue/config.yaml)"
  echo -e "  • Qwen Code        (~/.qwen/settings.json, skills)"
  echo -e "  • User Profile     (~/.ai-coding-kit/USER.md, optional)"
}

# --- 主流程 ---
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      ai-coding-kit 一键同步工具 v3.0         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

check_secrets
check_mcp

if [ "$FORCE" = true ]; then
  run_sync
else
  echo_step "env/secrets.json 已就绪，即将同步配置..."
  run_sync
fi
