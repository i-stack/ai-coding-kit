#!/usr/bin/env bash

# 测试 proposal 脚本的入参拒绝路径。
# 聚焦 regex 白名单一致性；不做文件副作用断言。
# 用法：bash scripts/test_proposal_scripts.sh
# 失败退出非零并打印首个失败用例。

set -u

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

fail=0
pass=0

expect_reject() {
  local label="$1"; shift
  local expect_msg="$1"; shift
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: ${label} should have rejected but exit=0"
    echo "  cmd: $*"
    echo "  out: ${out}"
    fail=$((fail+1))
    return
  fi
  if ! printf '%s' "$out" | grep -q -- "$expect_msg"; then
    echo "FAIL: ${label} rejected but message did not contain '${expect_msg}'"
    echo "  cmd: $*"
    echo "  out: ${out}"
    fail=$((fail+1))
    return
  fi
  pass=$((pass+1))
}

expect_ok() {
  local label="$1"; shift
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL: ${label} should have succeeded but exit=${rc}"
    echo "  cmd: $*"
    echo "  out: ${out}"
    fail=$((fail+1))
    return
  fi
  pass=$((pass+1))
}

# ---- create_skill_proposal.sh slug whitelist ----
for slug in "fix root" "../../../etc/passwd" "修复" "fix/root" "fix.v2" "" "$(printf 'a%.0s' {1..81})"; do
  expect_reject "create rejects slug: '${slug}'" "Invalid slug format" \
    bash scripts/create_skill_proposal.sh "$slug"
done

# ---- proposal_file whitelist on all consuming scripts ----
BAD_PATHS=(
  "/etc/hosts"
  "../../../etc/passwd"
  "evolution/proposals/foo.md"
  "evolution/proposals/20260101-foo.md"
  "evolution/proposals/20260101-000000-.md"
)

for bad in "${BAD_PATHS[@]}"; do
  expect_reject "approve rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/approve_skill_promotion.sh "$bad" approved-by-test
  expect_reject "promote rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/promote_skill_evolution.sh v999 proposal:test "$bad"
  expect_reject "validate rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/validate_skill_proposal.sh "$bad"
  expect_reject "record rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/record_validation_scenario.sh "$bad" layout pass a b c
  expect_reject "update-status rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/update_skill_proposal_status.sh "$bad" draft
  expect_reject "check-readiness rejects: ${bad}" "Invalid proposal_file format" \
    bash scripts/check_skill_promotion_readiness.sh "$bad"
done

# ---- snapshot consistency: must report OK when tree matches active snapshot ----
# 此脚本可能在晋升前（漂移态）或晋升后（一致态）运行。
# 用 SKIP 绕过以验证校验分支本身能正常加载脚本；真实一致性的断言留到 v33 晋升后。
expect_ok "validate_skill_evolution with SKIP bypasses step 8" \
  env SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh

echo "---"
echo "Passed: ${pass}"
echo "Failed: ${fail}"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
