#!/usr/bin/env bash
# =============================================================================
# sync-user-profile.sh — 跨会话用户画像注入
#
# 对齐 Hermes Agent 的 USER.md + 辩证式用户建模：把一份用户画像同步到各端
# Agent preamble，让所有 AI 工具共享同一份偏好与约束。
#
# 机制：
#   1. 用户从仓库根 USER.md.example 复制出 USER.md（gitignored，不提交）并填写
#   2. 本脚本把 USER.md 复制到 ~/.ai-coding-kit/USER.md（跨端共享位置）
#   3. 在各端 preamble 文件中 upsert 一个独立的
#      `<!-- managed-block:user-profile:begin ... end -->` 托管块，
#      指示 Agent 读取该画像并按其调整输出
#   4. 若 USER.md 不存在，则移除所有已注入的托管块（清理）
#
# 该托管块与 sync-agent-preamble.sh 的 agent-preamble 块标记不同，互不干扰。
#
# 用法:
#   bash scripts/sync-user-profile.sh            # 同步 / 清理
#   bash scripts/sync-user-profile.sh --dry-run  # 仅预览
#   bash scripts/sync-user-profile.sh --remove   # 强制移除托管块
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
KIT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
USER_SRC="${KIT_ROOT}/USER.md"
PROFILE_DEST="${HOME}/.ai-coding-kit/USER.md"
mkdir -p "$(dirname "$PROFILE_DEST")"

DRY_RUN=0
REMOVE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --remove) REMOVE=1 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

BLOCK_BEGIN='<!-- managed-block:user-profile:begin (auto-generated from skills-engineering/scripts/sync-user-profile.sh — do not edit) -->'
BLOCK_END='<!-- managed-block:user-profile:end -->'

# 目标文件（与各端 preamble 一致；不存在则跳过并提示）
TARGETS=(
  "${HOME}/.claude/CLAUDE.md"
  "${HOME}/.codex/AGENTS.md"
  "${HOME}/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md"
  "${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md"
  "${HOME}/.gemini/GEMINI.md"
)

# 用 python3 在文件中 upsert / 移除托管块
upsert_block() {
  # $1 = file, $2 = block content (with begin/end markers)
  local file="$1" content="$2"
  [ -f "$file" ] || { echo "  skip (not found): $file"; return 0; }
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] upsert block in: $file"
    return 0
  fi
  python3 - "$file" "$BLOCK_BEGIN" "$BLOCK_END" "$content" <<'PY'
import sys, re
path, begin, end, content = sys.argv[1:5]
with open(path, encoding="utf-8") as f:
    text = f.read()
pat = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
if pat.search(text):
    text = pat.sub(content + "\n", text)
else:
    text = text.rstrip("\n") + "\n\n" + content + "\n"
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
PY
  echo "  upserted: $file"
}

remove_block() {
  local file="$1"
  [ -f "$file" ] || return 0
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] remove block from: $file"
    return 0
  fi
  python3 - "$file" "$BLOCK_BEGIN" "$BLOCK_END" <<'PY'
import sys, re
path, begin, end = sys.argv[1:4]
with open(path, encoding="utf-8") as f:
    text = f.read()
pat = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
if pat.search(text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(pat.sub("", text))
PY
  echo "  removed: $file"
}

build_block() {
  cat <<EOF
$BLOCK_BEGIN
# user profile

执行任务前，先读取用户画像 \`~/.ai-coding-kit/USER.md\`（若存在），并按其中的角色、技术偏好、沟通偏好与约束调整输出风格与默认决策。画像缺失或为空时按通用最佳实践处理。

画像由用户维护（仓库根 \`USER.md\`，从 \`USER.md.example\` 复制），跨会话持久、跨端共享。
$BLOCK_END
EOF
}

if [ "$REMOVE" -eq 1 ] || [ ! -f "$USER_SRC" ]; then
  if [ "$REMOVE" -eq 1 ]; then
    echo "Removing user-profile managed blocks from all targets..."
  else
    echo "No USER.md found at repo root ($USER_SRC)."
    echo "Copy USER.md.example -> USER.md and fill it in to enable the profile."
    echo "Cleaning any stale managed blocks..."
  fi
  for t in "${TARGETS[@]}"; do remove_block "$t"; done
  [ -f "$PROFILE_DEST" ] && rm -f "$PROFILE_DEST" && echo "Removed $PROFILE_DEST"
  echo "Done."
  exit 0
fi

# 有 USER.md：复制并注入
if [ "$DRY_RUN" -ne 1 ]; then
  cp "$USER_SRC" "$PROFILE_DEST"
  echo "Synced profile -> $PROFILE_DEST"
else
  echo "[dry-run] would sync $USER_SRC -> $PROFILE_DEST"
fi
BLOCK="$(build_block)"
echo "Injecting user-profile managed blocks..."
for t in "${TARGETS[@]}"; do upsert_block "$t" "$BLOCK"; done
echo "Done. Agents will now read your profile from ~/.ai-coding-kit/USER.md."
