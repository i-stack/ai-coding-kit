#!/usr/bin/env bash
# =============================================================================
# validate-skill-integrity.sh — 技能分发前完整性校验（checksum）
#
# 对齐 Hermes Agent 的 bundle 校验 / checksum 思路：在同步/分发前对技能文件
# 计算 sha256，与上次基线比对，发现非预期改动（ADDED / MODIFIED / REMOVED）。
#
# 这层校验独立于结构校验（validate-skill-structure.sh），关注的是「内容是否被
# 篡改 / 意外改动」，可作为 pre-push 或 CI 的额外闸门。
#
# 采集范围：技能目录下所有 .md/.json/.yaml/.yml，但排除技能根目录下的
# evolution/ —— 那是演进治理的运行时状态（proposals / approvals / history 快照 /
# active_version.json / usage 账本 / minor-changes.log），其变化由治理流程登记、
# 并由专门校验器守护（validate-skill-proposal.sh / check-snapshot-consistency.sh /
# validate-usage-ledger.sh）。纳入基线会让 promote 与使用账本追加造成恒漂移。
#
# 因此 promote（只写快照、不改工作副本契约内容）不会触发漂移；rollback 会把快照
# 恢复进工作副本、确实改动契约内容，之后须刷新基线。
#
# 用法:
#   bash scripts/validate-skill-integrity.sh            # 全部技能：比对并更新基线
#   bash scripts/validate-skill-integrity.sh <skill>    # 单技能
#   bash scripts/validate-skill-integrity.sh --check-only   # 只比对，不更新基线
#   bash scripts/validate-skill-integrity.sh --verify-bundle <bundle.json>
#                                                      # 校验 skill_bundles 产物的 checksum
#
# 基线存储：skills-engineering/.integrity/<skill>.sha256（受治理清单，提交入库）
#
# 基线是「内容登记制」：技能内容变更（.md/.json/.yaml/.yml）会让 --check-only
# 报 ADDED/MODIFIED/REMOVED；变更必须显式登记 —— 运行本脚本（不带 --check-only）
# 刷新基线，并把刷新后的 .sha256 与内容变更放在同一个 commit 里提交。
# CI 用 --check-only 比对仓库内基线，不再自行生成基线（否则恒真）。
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INTEGRITY_DIR="${SE_DIR}/.integrity"
mkdir -p "$INTEGRITY_DIR"

CHECK_ONLY=0
VERIFY_BUNDLE=""
SKILL_ARG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --check-only) CHECK_ONLY=1; shift ;;
    --verify-bundle) VERIFY_BUNDLE="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) SKILL_ARG="$1"; shift ;;
  esac
done

if [ -n "$VERIFY_BUNDLE" ]; then
  [ -f "$VERIFY_BUNDLE" ] || { echo "Bundle manifest not found: $VERIFY_BUNDLE" >&2; exit 1; }
  python3 - "$VERIFY_BUNDLE" <<'PY'
import sys, os, json, hashlib
manifest = sys.argv[1]
base = os.path.dirname(manifest)
data = json.load(open(manifest, encoding="utf-8"))
checksums = data.get("checksums_sha256", {})
fails = 0
for rel, expected in checksums.items():
    fp = os.path.join(base, rel)
    if not os.path.isfile(fp):
        print(f"  FAIL: missing file in bundle: {rel}"); fails += 1; continue
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    if h.hexdigest() != expected:
        print(f"  FAIL: checksum mismatch: {rel}"); fails += 1
    else:
        print(f"  [ok] {rel}")
print(f"--- bundle {data.get('name','?')}: {'PASS' if fails==0 else 'FAIL ('+str(fails)+')'} ---")
sys.exit(1 if fails else 0)
PY
  exit $?
fi

collect_hashes() {
  # $1 = skill dir; prints "relpath sha256" lines (sorted)
  python3 - "$1" <<'PY'
import os, sys, hashlib
skill_dir = sys.argv[1]
files = []
for root, dirs, fnames in os.walk(skill_dir):
    if os.path.abspath(root) == os.path.abspath(skill_dir):
        # 技能根目录下的 evolution/ 是演进治理的运行时状态（proposals /
        # approvals / history 快照 / active_version.json / usage 账本 / minor
        # -changes.log 等），其变化由治理流程登记、并由专门校验器守护
        # （validate-skill-proposal.sh、check-snapshot-consistency.sh、
        # validate-usage-ledger.sh），不属于「技能契约内容」，不纳入基线。
        # 否则 promote / 使用账本追加都会让基线恒漂移。
        dirs[:] = [d for d in dirs if d != "evolution"]
    for fn in fnames:
        if any(fn.endswith(ext) for ext in (".md", ".json", ".yaml", ".yml")):
            files.append(os.path.join(root, fn))
out = []
for fp in files:
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    rel = os.path.relpath(fp, skill_dir)
    out.append(f"{rel} {h.hexdigest()}")
for line in sorted(out):
    print(line)
PY
}

SKILLS=()
if [[ -n "$SKILL_ARG" ]]; then
  # 单 skill 模式：先断言目录存在且含 SKILL.md，避免拼写错误的技能名
  # 被当成「0 文件」空集合而静默通过完整性门禁。
  if [[ ! -d "$SE_DIR/$SKILL_ARG" || ! -f "$SE_DIR/$SKILL_ARG/SKILL.md" ]]; then
    echo "Skill not found or missing SKILL.md: $SKILL_ARG" >&2
    exit 1
  fi
  SKILLS=("$SE_DIR/$SKILL_ARG")
else
  for d in "$SE_DIR"/*/; do
    [[ -f "$d/SKILL.md" ]] && SKILLS+=("$d")
  done
fi

TOTAL_FAIL=0
for skill_dir in "${SKILLS[@]}"; do
  name="$(basename "${skill_dir%/}")"
  baseline="${INTEGRITY_DIR}/${name}.sha256"
  cur="$(collect_hashes "$skill_dir")"

  if [[ ! -f "$baseline" ]]; then
    echo "=== $name ==="
    if [[ "$CHECK_ONLY" -eq 1 ]]; then
      # --check-only 只比对不写基线：无基线即「无可比对」，应判失败而非静默通过。
      echo "  FAIL: no integrity baseline for '$name' (run without --check-only first to create it)"
      TOTAL_FAIL=$((TOTAL_FAIL + 1))
    else
      echo "  [baseline] created ($(echo "$cur" | grep -c .) files hashed)"
      echo "$cur" > "$baseline"
    fi
    continue
  fi

  base="$(cat "$baseline")"
  # 比对
  diff_out="$(diff <(echo "$base") <(echo "$cur") || true)"
  if [[ -z "$diff_out" ]]; then
    echo "=== $name ==="
    echo "  [ok] integrity unchanged ($(echo "$cur" | grep -c .) files)"
  else
    echo "=== $name ==="
    while IFS= read -r line; do
      if [[ "$line" == "< "* ]]; then
        rel="${line#< }"; rel="${rel%% *}"
        echo "  REMOVED: $rel"
      elif [[ "$line" == "> "* ]]; then
        rel="${line#> }"; rel="${rel%% *}"
        # 判断是新增还是修改：看对面是否同 rel 不同 hash
        if grep -q "^${rel} " <<<"$base"; then
          echo "  MODIFIED: $rel"
        else
          echo "  ADDED: $rel"
        fi
      fi
    done <<<"$diff_out"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    if [[ "$CHECK_ONLY" -ne 1 ]]; then
      echo "$cur" > "$baseline"
      echo "  [baseline] updated"
    fi
  fi
done

echo "========================================="
if [[ $TOTAL_FAIL -eq 0 ]]; then
  echo "All checked skills: integrity OK."
  exit 0
else
  echo "Integrity drift detected in $TOTAL_FAIL skill(s)."
  exit 1
fi
