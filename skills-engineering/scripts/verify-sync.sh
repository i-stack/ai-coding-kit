#!/usr/bin/env bash
# Thin wrapper around sync/cli/main.py verify.
#
# This script previously contained all verification logic with a hardcoded
# platform list. It is now a compatibility shim that delegates to the Python
# verifier, which discovers targets from the shared registry (sync/core/registry.py)
# and env/platforms/*.json.
#
# All SYNC_* env flags and exit-code semantics are preserved.
#
# TODO(P2): Once compatibility wrappers are deprecated, callers should invoke
#   python3 sync/cli/main.py verify --target all directly and this wrapper can
# be removed.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

exec python3 "${REPO_ROOT}/sync/cli/main.py" verify "$@"
