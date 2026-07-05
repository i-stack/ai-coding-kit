#!/bin/bash
# =============================================================================
# 删除 GitHub Deployments 工具
# =============================================================================
# 用途：清理 GitHub 仓库中失败的或不活跃的 Deployments
# 依赖：需要安装 gh CLI 并已登录 (gh auth login)
#
# 用法：
#   ./cleanup-github-deployments.sh <owner> <repo> [--dry-run] [--all]
#
# 参数：
#   --dry-run   仅查看，不实际删除
#   --all       删除所有 Deployment（包括成功的），默认只删除非 success 的
#
# 示例：
#   # 预览将要删除的部署（不实际删除）
#   ./cleanup-github-deployments.sh i-stack ai-coding-kit --dry-run
#
#   # 删除所有失败的/非活跃的部署
#   ./cleanup-github-deployments.sh i-stack ai-coding-kit
#
#   # 删除所有部署（包括成功的）
#   ./cleanup-github-deployments.sh i-stack ai-coding-kit --all
# =============================================================================

set -euo pipefail

# ---- 参数解析 ----
OWNER="${1:-}"
REPO="${2:-}"
DRY_RUN=false
DELETE_ALL=false

shift 2 2>/dev/null || true
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --all)     DELETE_ALL=true ;;
    *)         echo "未知参数: $arg"; exit 1 ;;
  esac
done

if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
  echo "用法: $0 <owner> <repo> [--dry-run] [--all]"
  exit 1
fi

# ---- 检查 gh CLI ----
if ! command -v gh &> /dev/null; then
  echo "错误: 需要安装 gh CLI (brew install gh)"
  exit 1
fi

if ! gh auth status &> /dev/null; then
  echo "错误: 请先登录 gh (gh auth login)"
  exit 1
fi

echo "============================================"
echo "  GitHub Deployments 清理工具"
echo "  仓库: $OWNER/$REPO"
echo "  模式: $(if $DRY_RUN; then echo '预览 (不删除)'; elif $DELETE_ALL; then echo '删除全部'; else echo '删除非成功'; fi)"
echo "============================================"
echo ""

# ---- 获取所有部署并逐个处理 ----
DELETED=0
SKIPPED=0

gh api "/repos/$OWNER/$REPO/deployments" --jq '.[].id' | while read -r id; do
  # 获取最新状态
  state=$(gh api "/repos/$OWNER/$REPO/deployments/$id/statuses" --jq '.[0].state // "pending"' 2>/dev/null || echo "unknown")
  created=$(gh api "/repos/$OWNER/$REPO/deployments/$id" --jq '.created_at' 2>/dev/null || echo "unknown")
  env_name=$(gh api "/repos/$OWNER/$REPO/deployments/$id" --jq '.environment // "unknown"' 2>/dev/null || echo "unknown")

  # 判断是否需要删除
  should_delete=false
  if $DELETE_ALL; then
    should_delete=true
  elif [ "$state" != "success" ]; then
    should_delete=true
  fi

  if $should_delete; then
    if $DRY_RUN; then
      echo "[预览] 将删除: id=$id  state=$state  env=$env_name  created=$created"
    else
      echo -n "删除 deployment $id (state=$state)... "
      gh api -X DELETE "/repos/$OWNER/$REPO/deployments/$id" --silent 2>/dev/null && echo "完成" || echo "失败"
    fi
  else
    echo "保留: id=$id  state=$state  env=$env_name  created=$created"
  fi
done

echo ""
echo "============================================"
if $DRY_RUN; then
  echo "  预览结束（未实际删除）。移除 --dry-run 以执行删除。"
else
  echo "  清理完成！"
fi
echo "============================================"

# =============================================================================
# 手动操作参考（不使用脚本时）
# =============================================================================
#
# 1. 列出所有 Deployments:
#    gh api /repos/{owner}/{repo}/deployments --jq '.[].id'
#
# 2. 查看某个 Deployment 的最新状态:
#    gh api /repos/{owner}/{repo}/deployments/{id}/statuses --jq '.[0].state'
#
# 3. 查看某个 Deployment 详情:
#    gh api /repos/{owner}/{repo}/deployments/{id} --jq '{id, environment, ref, created_at, description}'
#
# 4. 删除单个 Deployment:
#    gh api -X DELETE /repos/{owner}/{repo}/deployments/{id}
#
# 5. 批量删除所有失败的 Deployment:
#    gh api /repos/{owner}/{repo}/deployments --jq '.[].id' | while read id; do
#      state=$(gh api /repos/{owner}/{repo}/deployments/$id/statuses --jq '.[0].state // empty')
#      if [ "$state" != "success" ]; then
#        echo "Deleting $id..."
#        gh api -X DELETE /repos/{owner}/{repo}/deployments/$id
#      fi
#    done
#
# 注意：
# - GitHub Web UI 中没有直接删除 Deployment 的按钮，只能通过 API/CLI 操作
# - 删除 Deployment 不会删除对应的 Actions workflow run
# - 建议先使用 --dry-run 预览再执行实际删除
# =============================================================================
