#!/usr/bin/env bash
# =============================================================================
# ai-coding-kit 一键同步脚本
#
# 用法:
#   bash sync.sh                 # 首次使用：自动检测 config，若不存在则从 example 复制并提示编辑
#   bash sync.sh --force         # 强制执行同步（跳过 config 检查提示）
#   bash sync.sh --init          # 仅初始化 config（从 example 复制）
#
# 此脚本会：
#   1. 检查 env/config.json 是否存在，不存在则从 env/config.json.example 复制
#   2. 执行 sync/sync_all.sh 同步配置到各 AI 编码工具
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_JSON="$SCRIPT_DIR/env/config.json"
CONFIG_EXAMPLE="$SCRIPT_DIR/env/config.json.example"

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

# --- 初始化 config ---
init_config() {
  if [ -f "$CONFIG_JSON" ]; then
    echo_ok "env/config.json 已存在，跳过初始化。"
    return 0
  fi

  if [ ! -f "$CONFIG_EXAMPLE" ]; then
    echo_error "找不到 env/config.json.example，请确认仓库完整性。"
    exit 1
  fi

  echo_warn "env/config.json 不存在，正在从 env/config.json.example 复制..."
  cp "$CONFIG_EXAMPLE" "$CONFIG_JSON"
  echo_ok "已创建 env/config.json"

  echo ""
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}  请编辑 env/config.json 填入你的 API Keys 和 MCP 配置：${NC}"
  echo -e "${YELLOW}${NC}"
  echo -e "${YELLOW}    vim env/config.json${NC}"
  echo -e "${YELLOW}    code env/config.json${NC}"
  echo -e "${YELLOW}${NC}"
  echo -e "${YELLOW}  编辑完成后，重新运行:${NC}"
  echo -e "${YELLOW}${NC}"
  echo -e "${YELLOW}    bash sync.sh${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  if [ "$MODE" = "init" ]; then
    exit 0
  fi

  # 交互模式：等待用户确认是否已编辑完成
  read -r -p "是否已完成编辑？(y/n) " CONFIRM
  if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo_warn "已取消。编辑完 env/config.json 后运行 bash sync.sh 即可同步。"
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
echo -e "${CYAN}║      ai-coding-kit 一键同步工具              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

init_config

if [ "$MODE" = "force" ]; then
  run_sync
elif [ "$MODE" = "sync" ]; then
  run_sync
fi