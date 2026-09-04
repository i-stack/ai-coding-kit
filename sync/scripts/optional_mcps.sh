#!/usr/bin/env bash
# =============================================================================
# optional_mcps.sh — 可选 MCP 服务器的启用 / 禁用 / 列出
#
# 对齐 Hermes Agent 的 optional_mcps/：把非默认、社区/高级 MCP 服务器与开箱
# 即用的 env/mcp/ 分开，避免污染默认配置。
#
#   enable <name>   把 env/optional_mcps/<name>.json 复制到 env/mcp/<name>.json
#                   下一次 sync.sh 会自动发现并同步
#   disable <name>  从 env/mcp/ 移除并停止同步
#   list            列出所有可选服务器及启用状态
#   sync            重新复制所有已启用服务器（刷新）
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OPT_DIR="${REPO_ROOT}/env/optional_mcps"
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

# sha256(file) -> 裸 hash（macOS/Linux 通用）
file_sha256() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

# 读取 registry 中某 name 的 sha256（不存在则空串）
registry_sha256() {
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2],{}).get('sha256','') if isinstance(d.get(sys.argv[2]),dict) else '')" "$REGISTRY" "$1"
}

# 校验 optional 源是否为合法的 MCP 定义，防止把无效定义 enable/sync 进同步链路
# 导致平台渲染 cfg['command'] 时 KeyError 崩溃。规则与 validate_env_schema.py 对齐。
validate_optional_source() {
  python3 - "$1" <<'PY'
import json, sys
src = sys.argv[1]
try:
    data = json.load(open(src, encoding="utf-8"))
except Exception as e:
    print(f"invalid JSON in {src}: {e}", file=sys.stderr); sys.exit(1)
if not isinstance(data, dict):
    print(f"{src}: root must be a JSON object", file=sys.stderr); sys.exit(1)
t = data.get("type")
KNOWN = {"name","type","command","args","env","url","headers","platforms","_comment","enabled"}
if t is not None and t not in ("stdio", "sse"):
    print(f"{src}: invalid type '{t}' (must be stdio or sse)", file=sys.stderr); sys.exit(1)
# 渲染兜底：必须有可渲染的入口——stdio 需要 command，sse 需要 url。
# 任意其一存在即可（type 可省略，由字段推断），但都不能缺失，否则
# load_all_mcp() 后平台渲染器在 cfg['command']/cfg['url'] 处 KeyError 崩溃。
has_cmd = "command" in data
has_url = "url" in data
if not has_cmd and not has_url:
    print(f"{src}: MCP definition must include 'command' (stdio) or 'url' (sse) (invalid MCP definition)", file=sys.stderr); sys.exit(1)
if t == "stdio" and "command" not in data:
    print(f"{src}: type=stdio requires 'command' (invalid MCP definition)", file=sys.stderr); sys.exit(1)
if t == "sse" and "url" not in data:
    print(f"{src}: type=sse requires 'url' (invalid MCP definition)", file=sys.stderr); sys.exit(1)
unknown = set(data.keys()) - KNOWN
if unknown:
    print(f"{src}: unknown fields: {', '.join(sorted(unknown))} (invalid MCP definition)", file=sys.stderr); sys.exit(1)
PY
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
    # 校验 optional 源合法性，防止把无效定义 enable 进同步链路导致平台崩溃
    if ! validate_optional_source "$src"; then
      echo "Refusing to enable '$name': invalid MCP definition in $src" >&2
      exit 1
    fi
    src_sum="$(file_sha256 "$src")"
    if [ -f "$dst" ]; then
      dst_sum="$(file_sha256 "$dst")"
      if [ "$src_sum" != "$dst_sum" ]; then
        # 目标已存在且内容与 optional 源不同：极可能是仓库默认或手动编辑的文件。
        # 若此时登记，disable 会误删非本工具创建的文件（违反安全护栏）。故拒绝。
        echo "Refusing to enable '$name': ${dst} already exists and differs from the optional source." >&2
        echo "It looks like a repo default or a manually edited file — not registering, not overwriting." >&2
        echo "If you really want the optional version, remove/rename ${dst} first, then re-run enable." >&2
        exit 1
      fi
      echo "Already enabled ($name content matches optional source)."
    else
      cp "$src" "$dst"
      echo "Enabled $name -> $dst (will sync on next 'bash sync.sh')"
    fi
    # 记录启用时的内容 checksum，供 disable 前的归属校验使用
    reg="$(read_registry)"
    echo "$reg" | python3 -c "import json,sys; d=json.load(sys.stdin); d[sys.argv[1]]={'enabled_at':'$(date -u +%Y-%m-%dT%H:%M:%SZ)','sha256':sys.argv[2]}; print(json.dumps(d))" "$name" "$src_sum" > "$REGISTRY.tmp"
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
      # 删除前二次确认归属：当前文件内容必须与「启用时记录的 checksum」一致，
      # 否则说明文件已被手动改动或本就是默认文件，拒绝删除以免误删仓库默认配置。
      recorded_sum="$(registry_sha256 "$name")"
      current_sum="$(file_sha256 "$dst")"
      # 若本工具之外的刷新路径（如 sync.sh）已更新 dst，registry 中的 checksum 可能过期。
      # 此时只要当前文件与 optional 源完全一致，仍可安全删除（它仍是本工具复制的产物）。
      src_sum=""
      [ -f "${OPT_DIR}/${name}.json" ] && src_sum="$(file_sha256 "${OPT_DIR}/${name}.json")"
      if [ -n "$recorded_sum" ] && [ "$recorded_sum" != "$current_sum" ]; then
        if [ -n "$src_sum" ] && [ "$src_sum" = "$current_sum" ]; then
          rm -f "$dst"
          echo "Disabled $name (removed $dst; current content matches optional source after sync)"
        else
          echo "Refusing to remove ${dst}: current content differs from what optional_mcps enabled (checksum mismatch)." >&2
          echo "It may be a repo default or was edited after enabling — leaving the file and registry entry in place." >&2
          exit 1
        fi
      else
        rm -f "$dst"
        echo "Disabled $name (removed $dst)"
      fi
    else
      echo "$name was recorded but its file is already gone; cleaning registry only."
    fi
    reg="$(read_registry)"
    echo "$reg" | python3 -c "import json,sys; d=json.load(sys.stdin); d.pop(sys.argv[1], None); print(json.dumps(d))" "$name" > "$REGISTRY.tmp"
    mv "$REGISTRY.tmp" "$REGISTRY"
    ;;
  sync)
    reg="$(read_registry)"
    # 刷新前校验每个已启用 optional 源的合法性，跳过无效定义以免破坏同步链路
    valid_names=()
    for name in $(echo "$reg" | python3 -c "import json,sys; print(' '.join(json.load(sys.stdin).keys()))"); do
      src="${OPT_DIR}/${name}.json"
      if [ ! -f "$src" ]; then
        echo "missing source for $name - skipped"
        continue
      fi
      if validate_optional_source "$src"; then
        valid_names+=("$name")
      else
        echo "Skipping sync of '$name': invalid MCP definition in $src" >&2
      fi
    done
    # 仅刷新通过校验的源，并同步更新 registry 中的 sha256（避免后续 disable 因
    # 校验和过期而拒绝删除，导致 list 显示 off 但 sync.sh 仍同步）。
    echo "$reg" | python3 -c "
import json, sys, os, shutil, hashlib
d = json.load(sys.stdin)
opt='${OPT_DIR}'; mcp='${MCP_DIR}'; reg='${REGISTRY}'
valid = set(sys.argv[1:])
for name in valid:
    src = os.path.join(opt, name + '.json')
    dst = os.path.join(mcp, name + '.json')
    if os.path.isfile(src):
        shutil.copy(src, dst)
        new_sum = hashlib.sha256(open(src, 'rb').read()).hexdigest()
        if isinstance(d.get(name), dict):
            d[name]['sha256'] = new_sum
        else:
            d[name] = {'sha256': new_sum}
        print('refreshed', name)
json.dump(d, open(reg + '.tmp', 'w'), indent=2, ensure_ascii=False)
open(reg + '.tmp', 'a').write('\n')
" "${valid_names[@]}" && mv "${REGISTRY}.tmp" "${REGISTRY}"
    ;;
  ""|-h|--help) usage 0 ;;
  *) echo "Unknown command: $cmd" >&2; usage 1 ;;
esac
