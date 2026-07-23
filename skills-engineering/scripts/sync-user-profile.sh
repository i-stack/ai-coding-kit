#!/usr/bin/env bash
# =============================================================================
# sync-user-profile.sh — 跨会话用户画像注入
#
# 对齐 Hermes Agent 的 USER.md + 辩证式用户建模：把一份用户画像同步到各端
# Agent preamble，让所有 AI 工具共享同一份偏好与约束。
#
# 机制：
#   1. 用户从 env/user-profile.md.example 复制出 env/user-profile.md（gitignored，不提交）并填写
#   2. 可选复制 env/user-profile.json.example 为 env/user-profile.json，配置 enabled/source
#   3. 本脚本把用户画像复制到 ~/.ai-coding-kit/USER.md（跨端共享位置）
#   4. 在各端 preamble 文件中 upsert 一个独立的
#      `<!-- managed-block:user-profile:begin ... end -->` 托管块，
#      指示 Agent 读取该画像并按其调整输出
#   5. enabled=auto 且画像不存在时跳过；--remove 强制清理托管块
#
# 该托管块与 sync-agent-preamble.sh 的 agent-preamble 块标记不同，互不干扰。
#
# 用法:
#   bash scripts/sync-user-profile.sh            # 同步 / 清理
#   bash scripts/sync-user-profile.sh --dry-run  # 仅预览
#   bash scripts/sync-user-profile.sh --remove   # 强制移除托管块
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
KIT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_FILE="${KIT_ROOT}/env/user-profile.json"
DEFAULT_USER_SRC="${KIT_ROOT}/env/user-profile.md"
USER_SRC="$DEFAULT_USER_SRC"
PROFILE_ENABLED="auto"
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

load_config() {
  [ -f "$CONFIG_FILE" ] || return 0
  local parsed
  if ! parsed="$(python3 - "$CONFIG_FILE" "$KIT_ROOT" <<'PY'
import json
import os
import sys

config_path, kit_root = sys.argv[1:3]
with open(config_path, encoding="utf-8") as f:
    cfg = json.load(f)

enabled = str(cfg.get("enabled", "auto")).strip().lower()
if enabled not in {"auto", "on", "off"}:
    raise SystemExit("enabled must be one of: auto, on, off")

source = str(cfg.get("source", "env/user-profile.md")).strip() or "env/user-profile.md"
source = os.path.expandvars(os.path.expanduser(source))
if not os.path.isabs(source):
    source = os.path.join(kit_root, source)
source = os.path.normpath(source)

print(enabled)
print(source)
PY
  )"; then
    echo "Invalid user profile config: $CONFIG_FILE" >&2
    return 1
  fi
  PROFILE_ENABLED="$(printf '%s\n' "$parsed" | sed -n '1p')"
  USER_SRC="$(printf '%s\n' "$parsed" | sed -n '2p')"
}

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

画像由用户维护（默认 \`env/user-profile.md\`，从 \`env/user-profile.md.example\` 复制；可通过 \`env/user-profile.json\` 改路径），跨会话持久、跨端共享。
$BLOCK_END
EOF
}

if ! load_config; then
  exit 1
fi

if [ "$REMOVE" -eq 1 ]; then
  echo "Removing user-profile managed blocks from all targets..."
  for t in "${TARGETS[@]}"; do remove_block "$t"; done
  [ -f "$PROFILE_DEST" ] && rm -f "$PROFILE_DEST" && echo "Removed $PROFILE_DEST"
  echo "Done."
  exit 0
fi

if [ "$PROFILE_ENABLED" = "off" ]; then
  echo "User profile sync disabled by env/user-profile.json (enabled=off)."
  echo "Run with --remove to clean existing managed blocks."
  exit 0
fi

if [ ! -f "$USER_SRC" ]; then
  if [ "$PROFILE_ENABLED" = "on" ]; then
    echo "User profile source not found: $USER_SRC" >&2
    echo "Copy env/user-profile.md.example -> env/user-profile.md, or update env/user-profile.json source." >&2
    exit 1
  fi
  echo "No user profile found at $USER_SRC."
  echo "Copy env/user-profile.md.example -> env/user-profile.md to enable the profile, or set enabled=on/off in env/user-profile.json."
  echo "Skipping user-profile sync."
  exit 0
fi

if [ ! -s "$USER_SRC" ]; then
  if [ "$PROFILE_ENABLED" = "on" ]; then
    echo "User profile source is empty: $USER_SRC" >&2
    exit 1
  fi
  echo "User profile source is empty: $USER_SRC"
  echo "Skipping user-profile sync."
  exit 0
fi

# 有用户画像：复制并注入
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
