#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running sync-skills.sh"
"${SCRIPT_DIR}/sync-skills.sh"

echo "---"
echo "Running sync-agent-preamble.sh"
"${SCRIPT_DIR}/sync-agent-preamble.sh"

echo "---"
echo "Running verify-sync.sh"
"${SCRIPT_DIR}/verify-sync.sh"

echo "---"
echo "Full skill sync complete."
