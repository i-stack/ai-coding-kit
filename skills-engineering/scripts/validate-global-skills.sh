#!/usr/bin/env bash
# Validate global skill rules end-to-end: source structure, behavior contracts,
# generated preambles, synced runtime copies, integrity baselines, and regression
# tests that guard multi-skill coordination.
#
# This is intentionally read-only: sync-agent-preamble is run in --dry-run mode,
# and integrity is checked with --check-only so CI cannot refresh baselines by
# accident.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

FAILED=0

run_step() {
  local name="$1"
  shift
  echo
  echo "=== ${name} ==="
  if "$@"; then
    echo "--- ${name}: PASS ---"
  else
    local rc=$?
    echo "--- ${name}: FAIL (${rc}) ---" >&2
    FAILED=1
  fi
}

cd "${REPO_ROOT}" || exit 1

run_step "skill structure" \
  bash "${SCRIPT_DIR}/validate-skill-structure.sh"

run_step "skill behavior" \
  bash "${SCRIPT_DIR}/validate-skill-behavior.sh"

run_step "preamble sync dry-run" \
  bash "${SCRIPT_DIR}/sync-agent-preamble.sh" --dry-run

run_step "sync verification" \
  bash "${SCRIPT_DIR}/verify-sync.sh"

run_step "skill integrity check-only" \
  bash "${SCRIPT_DIR}/validate-skill-integrity.sh" --check-only

run_step "doc-hygiene DH-002 banned-phrase scan" \
  bash "${SCRIPT_DIR}/validate-doc-hygiene.sh"

run_step "codebuddy/global coordination tests" \
  python3 tests/test_codebuddy_sync.py

echo
echo "========================================="
if [[ "${FAILED}" -eq 0 ]]; then
  echo "Global skill validation: PASS"
  exit 0
fi

echo "Global skill validation: FAIL" >&2
exit 1
