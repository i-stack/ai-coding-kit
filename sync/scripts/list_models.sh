#!/usr/bin/env bash
# =============================================================================
# list_models.sh — 跨平台模型 / provider 配置总览
#
# 对齐 Hermes Agent 的 model_metadata.py（provider 无关）思路：把分散在
# env/platforms/*.json 里的模型 / provider 配置抽出来统一查看，便于新增
# 模型或厂商时一眼看清「哪里配了什么」。
#
# 它不修改任何配置，只读 env/platforms/*.json，抽取含 model / provider /
# base_url / api_key / model_providers 等关键词的字段并打印成表。
#
# 用法:
#   bash sync/scripts/list_models.sh
#   bash sync/scripts/list_models.sh --json
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PLATFORMS_DIR="${REPO_ROOT}/env/platforms"

EMIT_JSON=0
[ "${1:-}" = "--json" ] && EMIT_JSON=1

if [ ! -d "$PLATFORMS_DIR" ]; then
  echo "No platforms dir: $PLATFORMS_DIR" >&2
  exit 1
fi

python3 - "$PLATFORMS_DIR" "$EMIT_JSON" <<'PY'
import os, sys, json

plat_dir, emit_json = sys.argv[1], sys.argv[2] == "1"
# 关注的键（大小写不敏感包含匹配）
KEYWORDS = ("model", "provider", "base_url", "api_key", "apikey", "endpoint")

def walk(obj, prefix=""):
    """Yield (path, value) for leaf nodes whose key matches KEYWORDS."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(kw in k.lower() for kw in KEYWORDS):
                if isinstance(v, (str, int, float, bool)):
                    out.append((prefix + k, v))
                elif isinstance(v, dict) and v:
                    # 折叠一层，避免刷屏
                    out.append((prefix + k, "{...}"))
            out.extend(walk(v, prefix + k + "."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(walk(v, f"{prefix}[{i}]."))
    return out

rows = []
for fn in sorted(os.listdir(plat_dir)):
    if not fn.endswith(".json"):
        continue
    path = os.path.join(plat_dir, fn)
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        rows.append((fn, "(parse error)", str(e)))
        continue
    found = walk(data)
    if not found:
        rows.append((fn, "(no model/provider fields)", ""))
    else:
        for k, v in found:
            # 脱敏：值含 key/token 时打码
            sval = str(v)
            if any(t in k.lower() for t in ("key", "token", "secret")) and len(sval) > 6:
                sval = sval[:3] + "***" + sval[-2:]
            rows.append((fn, k, sval))

if emit_json:
    print(json.dumps(
        [{"platform": r[0], "field": r[1], "value": r[2] if len(r) > 2 else ""} for r in rows],
        indent=2, ensure_ascii=False))
else:
    print("=== 跨平台模型 / provider 配置总览 ===\n")
    print(f"{'platform':<22} {'field':<28} value")
    print("-" * 80)
    for r in rows:
        plat, field = r[0], r[1]
        val = r[2] if len(r) > 2 else ""
        print(f"{plat:<22} {field:<28} {val}")
    print("\n提示：新增模型/厂商时，复制 env/templates/platform.template.json，"
          "在各平台 JSON 中按官方 spec 填 model/provider 字段即可。")
PY
