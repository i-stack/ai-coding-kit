#!/usr/bin/env bash
# =============================================================================
# ai-coding-kit 初始化脚本
#
# clone 项目后运行一次，完成本地配置初始化：
#   - 从 env/*.example 模板复制出缺失的本地配置文件
#     （幂等：目标已存在则跳过，绝不覆盖你已填好的真实配置）
#   - 提醒填写 env/secrets.json 中的真实 API Keys / Tokens
#
# 用法:
#   bash install.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/env"

# --- 颜色输出 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
echo_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo -e "${CYAN}==>${NC} 初始化 env/ 本地配置（从 .example 模板复制缺失文件）..."

shopt -s nullglob
created=0
for src in "$ENV_DIR"/*.example; do
  dst="${src%.example}"
  if [ ! -e "$dst" ]; then
    cp "$src" "$dst"
    echo_ok "已创建 ${dst#$SCRIPT_DIR/}"
    created=$((created + 1))
  fi
done
shopt -u nullglob

if [ "$created" -eq 0 ]; then
  echo_ok "所有本地配置文件均已存在，无需创建。"
fi

# secrets 仍是模板占位符则提醒填写
SECRETS="$ENV_DIR/secrets.json"
SECRETS_EXAMPLE="$ENV_DIR/secrets.json.example"
if [ -f "$SECRETS" ] && diff -q "$SECRETS" "$SECRETS_EXAMPLE" >/dev/null 2>&1; then
  echo_warn "env/secrets.json 仍是模板占位符，请编辑填入真实 API Keys / Tokens："
  echo -e "  ${CYAN}\$EDITOR env/secrets.json${NC}"
fi

echo ""
echo -e "${CYAN}下一步：${NC}"
echo -e "  1. 编辑 env/secrets.json 填入真实密钥（其余文件已由本脚本创建）"
echo -e "  2. 运行 ${CYAN}bash sync.sh${NC} 同步配置到各 AI 编码工具"
