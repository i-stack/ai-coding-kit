#!/usr/bin/env bash
# =============================================================================
# sync-memory.sh — 跨会话事件级记忆（对齐 Hermes 持久记忆的「自动累积」层）
#
# 与 sync-user-profile.sh（用户手维护的静态画像 USER.md）互补：
#   - user-profile：用户自维护的稳定偏好 / 角色 / 约束（静态）
#   - user-memory ：交互中累积的事件级记忆（被纠正的偏好、项目约定、决策理由）
#
# 机制：
#   1. 记忆落在 ~/.ai-coding-kit/MEMORY.md（跨端共享、跨会话持久；在仓库外，无需 gitignore）
#   2. 默认（或 `sync` 子命令）向各端 Agent preamble upsert 一个独立的
#      `<!-- managed-block:user-memory:begin ... end -->` 托管块，指示 Agent
#      读取该记忆；并把本脚本自复制到 ~/.ai-coding-kit/sync-memory.sh，
#      使 Agent 在任意会话都能用稳定路径调用 remember / recall。
#   3. `remember "..."`：追加一条带时间戳的记忆（可选 --tag 分类）
#   4. `recall [关键词]`：打印全部记忆，或按关键词过滤（字面短语匹配：-F 固定字符串，
#      多词按完整短语而非分词；如 `recall swift async` 搜的是字面量 "swift async"）
#
# 该托管块与 user-profile / ios-engineer 块标记互相独立，互不干扰。
#
# 用法:
#   bash scripts/sync-memory.sh                  # 注入托管块 + 自复制（幂等）
#   bash scripts/sync-memory.sh sync             # 同上
#   bash scripts/sync-memory.sh --dry-run        # 仅预览托管块变更
#   bash scripts/sync-memory.sh --remove         # 移除托管块（保留 MEMORY.md）
#   bash scripts/sync-memory.sh remember "用户偏好用中文回答" [--tag 沟通]
#   bash scripts/sync-memory.sh recall [关键词]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMORY_DIR="${HOME}/.ai-coding-kit"
MEMORY_FILE="${MEMORY_DIR}/MEMORY.md"
SELF_COPY="${MEMORY_DIR}/sync-memory.sh"

DRY_RUN=0
REMOVE=0
ACTION="sync"
REMEMBER_TEXT=""
REMEMBER_TAG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --remove)  REMOVE=1 ;;
    sync)      ACTION="sync" ;;
    remember)
      ACTION="remember"
      shift
      # 收集 remember 后的文本，直到 --tag
      _buf=""
      while [ $# -gt 0 ]; do
        case "$1" in
          --tag)
            REMEMBER_TAG="${2:-}"
            shift 2 || shift $#
            ;;
          *)
            _buf="${_buf:+$_buf }$1"
            shift
            ;;
        esac
      done
      REMEMBER_TEXT="${_buf}"
      break
      ;;
    recall)
      ACTION="recall"
      shift
      REMEMBER_TEXT="${*:-}"   # 剩余参数作为查询关键词
      break
      ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

BLOCK_BEGIN='<!-- managed-block:user-memory:begin (auto-generated from skills-engineering/scripts/sync-memory.sh — do not edit) -->'
BLOCK_END='<!-- managed-block:user-memory:end -->'

# 目标文件（与 user-profile / preamble 一致；不存在则跳过并提示）
TARGETS=(
  "${HOME}/.claude/CLAUDE.md"
  "${HOME}/.codex/AGENTS.md"
  "${HOME}/Library/Developer/Xcode/CodingAssistant/codex/AGENTS.md"
  "${HOME}/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/CLAUDE.md"
  "${HOME}/.gemini/GEMINI.md"
)

upsert_block() {
  local file="$1" content="$2"
  [ -f "$file" ] || { echo "  skip (not found): $file"; return 0; }
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] upsert block in: $file"
    return 0
  fi
  python3 - "$file" "$BLOCK_BEGIN" "$BLOCK_END" "$content" <<'PY' || { echo "  ERROR: failed to upsert block in $file" >&2; return 1; }
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
  python3 - "$file" "$BLOCK_BEGIN" "$BLOCK_END" <<'PY' || { echo "  ERROR: failed to remove block from $file" >&2; return 1; }
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
# user memory (event-level)

执行任务前，可读取 \`~/.ai-coding-kit/MEMORY.md\`（若存在），其中包含跨会话累积的用户纠正、项目约定与决策理由。仅在相关时参考，不要逐字复述。

记忆由交互中累积：运行 \`~/.ai-coding-kit/sync-memory.sh remember "..."\` 追加一条；\`recall [关键词]\` 检索。该文件跨会话持久、跨端共享，由你自己维护。
$BLOCK_END
EOF
}

ensure_memory_file() {
  mkdir -p "$MEMORY_DIR" || { echo "  ERROR: cannot create $MEMORY_DIR" >&2; return 1; }
  if [ ! -f "$MEMORY_FILE" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "  [dry-run] would create: $MEMORY_FILE"
      return 0
    fi
    cat > "$MEMORY_FILE" <<'EOF' || { echo "  ERROR: cannot write $MEMORY_FILE" >&2; return 1; }
# Cross-session Memory (auto-accumulated)

> Append via: ~/.ai-coding-kit/sync-memory.sh remember "..." [--tag label]
> This file is local-only and shared across all AI coding tools you use.
> Keep entries concise and factual; older entries may be consolidated by hand.

EOF
    echo "Created: $MEMORY_FILE"
  fi
}

self_copy() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] would copy self -> $SELF_COPY"
    return 0
  fi
  # 若已运行在稳定路径上，则无需自复制（cp 会拒绝同路径复制）
  local src dst
  src="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/$(basename "$0")"
  dst="$(cd "$(dirname "$SELF_COPY")" 2>/dev/null && pwd)/$(basename "$SELF_COPY")"
  if [ "$src" = "$dst" ]; then
    echo "  self-copy skipped (already running from stable path: $SELF_COPY)"
    return 0
  fi
  mkdir -p "$MEMORY_DIR" || { echo "  ERROR: cannot create $MEMORY_DIR" >&2; return 1; }
  cp "$0" "$SELF_COPY" || { echo "  ERROR: cannot copy self to $SELF_COPY" >&2; return 1; }
  chmod +x "$SELF_COPY" 2>/dev/null || true
  echo "Copied self -> $SELF_COPY (stable invocation path for agents)"
}

do_sync() {
  if [ "$REMOVE" -eq 1 ]; then
    echo "Removing user-memory managed blocks from all targets..."
    for t in "${TARGETS[@]}"; do remove_block "$t"; done
    echo "Done. (MEMORY.md at $MEMORY_FILE is preserved — remove it manually if desired.)"
    return 0
  fi
  ensure_memory_file
  BLOCK="$(build_block)"
  echo "Injecting user-memory managed blocks..."
  for t in "${TARGETS[@]}"; do upsert_block "$t" "$BLOCK"; done
  self_copy
  echo "Done. Agents will read your memory from $MEMORY_FILE."
}

do_remember() {
  if [ -z "$REMEMBER_TEXT" ]; then
    echo "remember: no text provided." >&2
    echo "Usage: sync-memory.sh remember \"<text>\" [--tag <label>]" >&2
    exit 1
  fi
  ensure_memory_file
  local ts tag
  ts="$(date '+%Y-%m-%d %H:%M')"
  tag="${REMEMBER_TAG:-未分类}"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] would append to $MEMORY_FILE:"
    echo "  ## $ts · $tag"
    echo "  $REMEMBER_TEXT"
    return 0
  fi
  {
    echo ""
    echo "## $ts · $tag"
    echo ""
    echo "$REMEMBER_TEXT"
  } >> "$MEMORY_FILE" || { echo "  ERROR: cannot append to $MEMORY_FILE" >&2; return 1; }
  echo "Remembered (tag=$tag): $REMEMBER_TEXT"
  echo "  -> $MEMORY_FILE"
  # 确保托管块存在，使记忆对 Agent 可见
  do_sync
}

do_recall() {
  if [ ! -f "$MEMORY_FILE" ]; then
    echo "No memory file yet at $MEMORY_FILE"
    echo "Add one with: ~/.ai-coding-kit/sync-memory.sh remember \"...\""
    return 0
  fi
  if [ -n "$REMEMBER_TEXT" ]; then
    echo "=== recall matching: $REMEMBER_TEXT ==="
    grep -i -n -F -- "$REMEMBER_TEXT" "$MEMORY_FILE" || echo "(no match)"
  else
    echo "=== all memory ($MEMORY_FILE) ==="
    cat "$MEMORY_FILE"
  fi
}

case "$ACTION" in
  sync)     do_sync ;;
  remember) do_remember ;;
  recall)   do_recall ;;
esac
