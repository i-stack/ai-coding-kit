#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

slug="${1:-demo-flow}"
version="${2:-v-demo-$(date '+%Y%m%d-%H%M%S')}"
approver="${3:-approved-by-user}"

echo "[1/7] Create proposal"
proposal_file="$(bash scripts/create-skill-proposal.sh "$slug")"
echo "proposal=${proposal_file}"

echo "[2/7] Validate proposal with placeholder scenarios"
bash scripts/validate-skill-proposal.sh "$proposal_file" layout concurrency

echo "[3/7] Record layout scenario"
bash scripts/record-validation-scenario.sh "$proposal_file" layout pass "命中四段式输出;先看布局与复用链路" "无" "无"

echo "[4/7] Record concurrency scenario"
bash scripts/record-validation-scenario.sh "$proposal_file" concurrency pass "命中取消链路检查;优先最小修复" "无" "无"

echo "[5/7] Check promotion readiness"
bash scripts/check-skill-promotion-readiness.sh "$proposal_file"

echo "[6/7] Approve promotion"
bash scripts/approve-skill-promotion.sh "$proposal_file" "$approver"

echo "[7/7] Promote and rollback"
bash scripts/promote-skill-evolution.sh "$version" "proposal:$(basename "$proposal_file" .md)" "$proposal_file"
bash scripts/rollback-skill-evolution.sh v1

echo "Demo complete"
echo "proposal=${proposal_file}"
echo "version=${version}"
