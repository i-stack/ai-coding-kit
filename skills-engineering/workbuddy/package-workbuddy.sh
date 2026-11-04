#!/usr/bin/env bash
# =============================================================================
# package-workbuddy.sh — WorkBuddy 开放平台技能上架包入口
#
# 规范：https://open.workbuddy.cn/docs/skill
#   zip 结构：{skill-name}/SKILL.md + references/ scripts/ templates/
#   frontmatter 必填：name / display_name / display_name_en / description /
#                    description_zh / description_en / version / author
#
# 用法:
#   bash workbuddy/package-workbuddy.sh list
#   bash workbuddy/package-workbuddy.sh build <skill|--all> [--layout flat|nested|both]
#   bash workbuddy/package-workbuddy.sh expert [--layout flat|nested]
#   bash workbuddy/package-workbuddy.sh validate [<skill|--all>]
#   bash workbuddy/package-workbuddy.sh expert    # 专家包：一个 zip 带全部技能
#   bash workbuddy/package-workbuddy.sh sheet     # 生成上架填表清单
#   bash workbuddy/package-workbuddy.sh clean
# =============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${HERE}/build_workbuddy.py" "$@"
