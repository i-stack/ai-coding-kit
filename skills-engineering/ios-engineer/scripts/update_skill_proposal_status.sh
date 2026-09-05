#!/usr/bin/env bash
# Compatibility shim: snake_case entry forwards to kebab-case.
# Kept for one release cycle; remove after callers migrate.
set -euo pipefail
_new="$(cd "$(dirname "$0")" && pwd)/update-skill-proposal-status.sh"
echo "DEPRECATED: $(basename "$0") has been renamed to update-skill-proposal-status.sh; this shim will be removed after one release cycle." >&2
exec "$_new" "$@"
