#!/usr/bin/env bash

# 治理脚本不变式隔离测试：覆盖 GC 删除边界 + rollback 护栏。
# 不污染真实 evolution/ 目录；全部在 mktemp 最小自包含 fixture 内运行。
# 用法：bash scripts/test_gc_invariant.sh
# 失败退出非零。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fail=0
pass=0

ok()  { echo "PASS: $1"; pass=$((pass+1)); }
bad() { echo "FAIL: $1"; fail=$((fail+1)); }

# 最小自包含 fixture：只包含 GC 需要的目录结构 + 一个真实脚本副本
FX="$(mktemp -d)"
cleanup() { rm -rf "$FX"; }
trap cleanup EXIT

SCRIPT_ROOT="$FX/ios-engineer"
mkdir -p "$SCRIPT_ROOT/scripts" \
         "$SCRIPT_ROOT/evolution/history" \
         "$SCRIPT_ROOT/evolution/proposals" \
         "$SCRIPT_ROOT/evolution/approvals" \
         "$SCRIPT_ROOT/evolution/validations"

cp "$SCRIPT_DIR/gc_evolution_history.sh" "$SCRIPT_ROOT/scripts/"
cp "$SCRIPT_DIR/rollback_skill_evolution.sh" "$SCRIPT_ROOT/scripts/"

# 生成 v1..v13，每个含 snapshot/{SKILL.md,agents,references,scripts} + metadata.json
for v in $(seq -w 1 13); do
  num=${v#0}
  d="$SCRIPT_ROOT/evolution/history/v${num}"
  mkdir -p "$d/snapshot/agents" "$d/snapshot/references" "$d/snapshot/scripts"
  printf -- '---\nname: ios-engineer\n---\n# fixture v%s\n' "$num" > "$d/snapshot/SKILL.md"
  : > "$d/snapshot/agents/.keep"
  : > "$d/snapshot/references/.keep"
  : > "$d/snapshot/scripts/.keep"
  printf '{"source":"proposal:fixture-%s"}\n' "$num" > "$d/metadata.json"
  # 给每个版本一个对应 proposal/approval（让 GC Phase 4 有界）
  printf -- '# fixture proposal %s\n' "$num" > "$SCRIPT_ROOT/evolution/proposals/fixture-${num}.md"
  printf '{"status":"approved"}\n' > "$SCRIPT_ROOT/evolution/approvals/fixture-${num}.json"
done

# active_version = v10（受保护）
printf '{\n  "active_version": "v10"\n}\n' > "$SCRIPT_ROOT/evolution/active_version.json"

# ---- Test 1: GC with KEEP_RECENT=10 must keep v4..v13, delete v1..v3 ----
if KEEP_RECENT=10 bash "$SCRIPT_ROOT/scripts/gc_evolution_history.sh" >/dev/null 2>&1; then
  ok "gc executed on minimal fixture"
else
  bad "gc execution failed on minimal fixture"
fi

kept=0
deleted_ok=true
for v in $(seq -w 1 13); do
  num=${v#0}
  if [ -d "$SCRIPT_ROOT/evolution/history/v${num}" ]; then
    kept=$((kept+1))
  else
    [ "$num" -le 3 ] || deleted_ok=false
  fi
done
if [ "$kept" -eq 10 ]; then ok "gc kept exactly 10 most recent versions (kept=$kept)"; else bad "gc kept $kept versions, expected 10"; fi
if $deleted_ok; then ok "gc only deleted oldest versions (v1..v3)"; else bad "gc deleted a version it should have kept"; fi
if [ -d "$SCRIPT_ROOT/evolution/history/v10" ]; then ok "active version v10 protected"; else bad "active version v10 was deleted"; fi

# 断言：每个保留版本 snapshot 完整
snap_ok=true
for v in $(seq -w 4 13); do
  num=${v#0}
  d="$SCRIPT_ROOT/evolution/history/v${num}/snapshot"
  for p in SKILL.md agents references scripts; do
    [ -e "$d/$p" ] || snap_ok=false
  done
done
if $snap_ok; then ok "every kept version retains complete snapshot"; else bad "a kept version lost snapshot integrity"; fi

# ---- Test 2: rollback 对缺失 snapshot 的版本必须拒绝（护栏） ----
mkdir -p "$SCRIPT_ROOT/evolution/history/v999"
if bash "$SCRIPT_ROOT/scripts/rollback_skill_evolution.sh" v999 >/dev/null 2>&1; then
  bad "rollback accepted version with missing snapshot (should reject)"
else
  ok "rollback rejects version with missing snapshot"
fi

# ---- Test 3: rollback 版本格式白名单（路径穿越） ----
if bash "$SCRIPT_ROOT/scripts/rollback_skill_evolution.sh" "../../etc/passwd" >/dev/null 2>&1; then
  bad "rollback accepted path-traversal version (should reject)"
else
  ok "rollback rejects invalid version format"
fi

echo "---"
echo "Passed: ${pass}"
echo "Failed: ${fail}"
[ "$fail" -eq 0 ] || exit 1
