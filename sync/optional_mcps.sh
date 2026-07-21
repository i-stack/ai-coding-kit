#!/usr/bin/env bash
# =============================================================================
# optional_mcps.sh — 可选 MCP 服务器的启用 / 禁用 / 列出
#
# 对齐 Hermes Agent 的 optional-mcps/：把非默认、社区/高级 MCP 服务器与开箱
# 即用的 env/mcp/ 分开，避免污染默认配置。
#
#   enable <name>   把 env/optional-mcps/<name>.json 复制到 env/mcp/<name>.json
#                   下一次 sync.sh 会自动发现并同步
#   disable <name>  从 env/mcp/ 移除并停止同步
#   list            列出所有可选服务器及启用状态
#   sync            重新复制所有已启用服务器（刷新）
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OPT_DIR="${REPO_ROOT}/env/optional-mcps"
MCP_DIR="${REPO_ROOT}/env/mcp"
REGISTRY="${OPT_DIR}/enabled.json"

mkdir -p "$MCP_DIR"
[ -f "$REGISTRY" ] || echo '{}' > "$REGISTRY"

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

read_registry() {
  python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" "$REGISTRY"
}

# 注：registry 写入统一走下方 enable/disable 的内联「tmp 写 → 原子 mv」模式，
# 不存在独立的 write_registry 入口（已移除死代码）。
cmd="${1:-}"; shift || true
case "$cmd" in
  list)
    echo "=== optional MCP servers ==="
    enabled_names="$(python3 -c "import json; print(' '.join(json.load(open('$REGISTRY')).keys()))")"
    found=0
    for f in "${OPT_DIR}"/*.json; do
      [ -e "$f" ] || break
      name="$(basename "$f" .json)"
      [ "$name" = "enabled" ] && continue
      found=1
      case " $enabled_names " in
        *" $name "*) printf "  [on ] %s\n" "$name" ;;
        *)             printf "  [off] %s\n" "$name" ;;
      esac
    done
    if [ "$found" -eq 0 ]; then echo "(none)"; fi
    ;;
  enable)
    [ $# -ge 1 ] || usage 1
    name="$1"
    src="${OPT_DIR}/${name}.json"
    dst="${MCP_DIR}/${name}.json"
    [ -f "$src" ] || { echo "Optional MCP not found: $src"; exit 1; }
    if [ -f "$dst" ]; then
      echo "Already enabled (or present in env/mcp): $name"
    else
      cp "$src" "$dst"
      echo "Enabled $name -> $dst (will sync on next 'bash sync.sh')"
    fi
    reg="$(read_registry)"
    echo "$reg" | python3 -c "import json,sys; d=json.load(sys.stdin); d[sys.argv[1]]={'enabled_at':'$(date -u +%Y-%m-%dT%H:%M:%SZ)'}; print(json.dumps(d))" "$name" > "$REGISTRY.tmp"
    mv "$REGISTRY.tmp" "$REGISTRY"
    ;;
  disable)
    [ $# -ge 1 ] || usage 1
    name="$1"
    dst="${MCP_DIR}/${name}.json"
    # 安全护栏：只移除「由本工具启用」的服务器，绝不删除仓库默认 env/mcp/*.json
    if ! python3 -c "import json,sys; sys.exit(0 if sys.argv[1] in json.load(open('$REGISTRY')) else 1)" "$name"; then
      echo "$name is not managed by optional_mcps (not in enabled registry)."
      echo "If it is a default server in env/mcp/, edit/remove it directly — refusing to delete tracked defaults."
      exit 1
    fi
    if [ -f "$dst" ]; then
      rm -f "$dst"
      echo "Disabled $name (removed $dst)"
    else
      echo "$name was recorded but its file is already gone; cleaning registry only."
    fi
    reg="$(read_registry)"
    echo "$reg" | python3 -c "import json,sys; d=json.load(sys.stdin); d.pop(sys.argv[1], None); print(json.dumps(d))" "$name" > "$REGISTRY.tmp"
    mv "$REGISTRY.tmp" "$REGISTRY"
    ;;
  sync)
    reg="$(read_registry)"
    echo "$reg" | python3 -c "
import json, sys, os, shutil
d = json.load(sys.stdin)
opt='${OPT_DIR}'; mcp='${MCP_DIR}'
for name in d:
    src = os.path.join(opt, name + '.json')
    dst = os.path.join(mcp, name + '.json')
    if os.path.isfile(src):
        shutil.copy(src, dst)
        print('refreshed', name)
    else:
        print('missing source for', name, '- skipped')
"
    ;;
  ""|-h|--help) usage 0 ;;
  *) echo "Unknown command: $cmd" >&2; usage 1 ;;
esac
