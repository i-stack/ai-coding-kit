#!/usr/bin/env bash
# =============================================================================
# ai-coding-kit 一键同步脚本
#
# 用法:
#   bash sync.sh                 # 同步所有平台的 MCP 和配置
#   bash sync.sh --force         # 强制执行同步（跳过检查提示）
#   bash sync.sh --init          # 仅初始化环境（创建模板文件）
#
# 配置文件:
#   env/mcp/              — MCP 服务器定义（每个文件一个服务）
#   env/platforms/        — 各平台专属配置（遵循官方规范）
#   env/templates/        — 新增 MCP/平台的模板
#
# 此脚本会：
#   1. 检查 env/mcp/ 目录是否存在配置文件
#   2. 执行 sync/sync_all.sh 同步配置到各 AI 编码工具
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$SCRIPT_DIR/env/mcp"
PLATFORMS_DIR="$SCRIPT_DIR/env/platforms"

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
MODE="sync"
if [ "${1:-}" = "--init" ]; then
  MODE="init"
elif [ "${1:-}" = "--force" ]; then
  MODE="force"
fi

# --- 检查配置 ---
check_config() {
  local has_config=false

  if [ -d "$MCP_DIR" ] && [ -n "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ]; then
    has_config=true
  fi

  if [ "$has_config" = false ]; then
    echo_warn "env/mcp/ 目录下没有 MCP 配置文件。"
    echo_warn "请按照以下步骤创建配置："
    echo ""
    echo -e "  ${CYAN}# 1. 从模板创建 MCP 服务器配置${NC}"
    echo -e "  ${CYAN}cp env/templates/mcp.template.json env/mcp/my-server.json${NC}"
    echo -e "  ${CYAN}$EDITOR env/mcp/my-server.json${NC}"
    echo ""
    echo -e "  ${CYAN}# 2. 从模板创建平台配置${NC}"
    echo -e "  ${CYAN}cp env/templates/platform.template.json env/platforms/codex.json${NC}"
    echo -e "  ${CYAN}$EDITOR env/platforms/codex.json${NC}"
    echo ""
    echo_warn "配置完成后，重新运行: bash sync.sh"
    exit 0
  fi
}

# --- 执行同步 ---
run_sync() {
  echo_step "开始同步配置到各 AI 编码工具..."
  echo ""

  # 调用 sync_all.sh 执行全部同步
  bash "$SCRIPT_DIR/sync/sync_all.sh"

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
  echo -e "  • Cline            (VSCode MCP settings)"
  echo -e "  • Gemini CLI       (环境变量)"
  echo -e "  • Continue         (~/.continue/config.yaml)"
}

# --- 主流程 ---
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      ai-coding-kit 一键同步工具 v3.0         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

check_config

if [ "$MODE" = "force" ] || [ "$MODE" = "sync" ]; then
  run_sync
fi
