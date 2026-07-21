#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running sync-skills.sh"
"${SCRIPT_DIR}/sync-skills.sh"

echo "---"
echo "Running sync-agent-preamble.sh"
"${SCRIPT_DIR}/sync-agent-preamble.sh"

echo "---"
echo "Running sync-user-profile.sh (cross-session user profile)"
if [[ "${SKIP_USER_PROFILE:-false}" != "true" ]]; then
  "${SCRIPT_DIR}/sync-user-profile.sh"
else
  echo "  (skipped: SKIP_USER_PROFILE=true)"
fi

echo "---"
echo "Running sync-memory.sh (cross-session event memory)"
if [[ "${SKIP_MEMORY:-false}" != "true" ]]; then
  "${SCRIPT_DIR}/sync-memory.sh"
else
  echo "  (skipped: SKIP_MEMORY=true)"
fi

echo "---"
echo "Running verify-sync.sh"
"${SCRIPT_DIR}/verify-sync.sh"

echo "---"
echo "Full skill sync complete."
