#!/usr/bin/env bash
# validate-doc-hygiene.sh — DH-002 禁用词回归扫描（doc-hygiene 的自动化回退）
#
# DH-002 禁止「过程叙事关键词」出现在会被 Agent 加载运行的文档正文中。
# 此前该规则仅靠写时 self-check，无任何 CI 回退。本脚本扫回归。
#
# 扫描边界（与 doc-hygiene/references/doc_hygiene.md 的 DH-001「适用范围与
# 自动化边界」注记一致）：
#   DH-001/002 对所有 .md 生效（契约层面覆盖全部 references）。但本脚本的自动
#   扫描聚焦「运行期会被 Agent 加载运行的入口/约定类文档」——不含普通
#   references/*.md 技术细则（那里常有合法的「迁移期间」等工程叙述，非本 skill
#   针对的文档变更过程叙事，靠写时 self-check 覆盖，盲目 CI 扫全仓误伤率高）。
#
#   排除（永不扫）：
#   - doc-hygiene 整个 skill 目录（SKILL/AGENT-BRIEF/OUT-OF-SCOPE/references 都在
#     描述/定义纪律本身，出现禁用词是定义行为而非违规）；
#   - .agents/writing-docs.md（引用 DH-002 词表作说明）；
#   - CHANGELOG.md / evolution/** / history/** / proposals/** / plan-reviews/**
#     （变更记录载体，DH-002 明文例外）。
#   自动扫描的边界不削弱 DH-001 对 references 的契约效力。
#
# 禁用词清单以 doc-hygiene/references/doc_hygiene.md 的 DH-002 条文为单一真值；
# 若需增删词，改此处与条文保持一致即可。
#
# 退出码：0 无命中；1 命中禁用词（阻断）。
#
# 用法：
#   scripts/validate-doc-hygiene.sh            # 按上述边界扫
#   scripts/validate-doc-hygiene.sh <path>     # 仅扫某文件（若为规则自身则自动跳过）

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 扫描白名单（glob，递归覆盖所有 skill 的入口/约定类文档）：
#   SKILL.md / AGENT-BRIEF.md / OUT-OF-SCOPE.md / rule_index.md / README.md
#   .agents/invocation.md / .agents/composition.md
INCLUDE_GLOBS=(
  '--glob' '**/SKILL.md'
  '--glob' '**/AGENT-BRIEF.md'
  '--glob' '**/OUT-OF-SCOPE.md'
  '--glob' '**/rule_index.md'
  '--glob' '**/README.md'
  '--glob' '**/.agents/invocation.md'
  '--glob' '**/.agents/composition.md'
)

# --- DH-002 禁用词（与 doc-hygiene/references/doc_hygiene.md 保持一致） ---
# 用固定字符串（-F）匹配，避免 ERE 对中文多字节的异常。
# 只收「高特异」的过程叙事词；通用短词（如「本轮」「现由」「现已」）在正常
# 技术文档太常见，误伤率高，不进自动扫描（仍由写时 self-check 覆盖）。
PATTERNS=(
  '迁移期'
  '迁移说明'
  '待平移'
  '待真值文件'
  '待后续'
  'owner 纠正'
  '抽象归属倒置'
  '此前承载'
  '之前承载'
  '不再由'
  '我们做了'
  '已重构为'
)

# 规则定义/描述区必须列举这些词，永远排除：
#   - doc-hygiene 整个 skill 目录（描述/定义纪律本身，出现禁用词是定义行为）
#   - .agents/writing-docs.md（引用 DH-002 词表作说明）
#   - 变更记录载体：CHANGELOG.md / evolution/** / history/** / proposals/** / 等
EXCLUDE_GLOBS=(
  '--glob' '!**/doc-hygiene/**'
  '--glob' '!**/.agents/writing-docs.md'
  '--glob' '!**/CHANGELOG.md'
  '--glob' '!**/evolution/**'
  '--glob' '!**/history/**'
  '--glob' '!**/proposals/**'
  '--glob' '!**/plan-reviews/**'
)

# 扫描根：默认整个 skills-engineering，允许调用方用 $1 覆盖为单文件/目录。
SCAN_ROOT="${1:-${SE_DIR}}"

echo "=== doc-hygiene (DH-002) banned-phrase scan ==="
echo "scan root: ${SCAN_ROOT}"

HITS=""
GREP_ARGS=()
for p in "${PATTERNS[@]}"; do
  GREP_ARGS+=(-e "$p")
done

# 用 ripgrep；若不可用则回退 grep -F（边界控制较弱：仅按文件名白名单，不递归排除）。
if command -v rg >/dev/null 2>&1; then
  out="$(rg --no-messages -F -n "${INCLUDE_GLOBS[@]}" "${EXCLUDE_GLOBS[@]}" "${GREP_ARGS[@]}" "$SCAN_ROOT" 2>/dev/null)" || true
  [ -n "$out" ] && HITS+="${out}"$'\n'
else
  echo "  WARN: ripgrep (rg) not found; falling back to grep -F over whitelist filenames" >&2
  while IFS= read -r fp; do
    case "$fp" in
      */doc-hygiene/**|*/.agents/writing-docs.md|*/CHANGELOG.md|*/evolution/*|*/history/*|*/proposals/*|*/plan-reviews/*) continue ;;
    esac
    o="$(grep -Fn "${PATTERNS[@]}" "$fp" 2>/dev/null)" || true
    [ -n "$o" ] && HITS+="${fp}: ${o}"$'\n'
  done < <(find "$SCAN_ROOT" -type f \( -name SKILL.md -o -name AGENT-BRIEF.md -o -name OUT-OF-SCOPE.md -o -name rule_index.md -o -name README.md \))
fi

if [ -z "${HITS}" ]; then
  echo "  [ok] no DH-002 banned phrases found in runnable entry docs."
  echo "--- doc-hygiene scan: PASS ---"
  exit 0
fi

echo "  FAIL: DH-002 banned phrases found:" >&2
echo "${HITS}" | while IFS= read -r line; do
  [ -n "$line" ] && echo "    ${line}" >&2
done
echo "--- doc-hygiene scan: FAIL ---" >&2
exit 1
