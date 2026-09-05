#!/usr/bin/env bash
# Compatibility shim: snake_case entry forwards to kebab-case.
# Kept for one release cycle; remove after callers migrate.
set -euo pipefail
_new="$(cd "$(dirname "$0")" && pwd)/validate-scenario-specs.sh"
echo "DEPRECATED: $(basename "$0") has been renamed to validate-scenario-specs.sh; this shim will be removed after one release cycle." >&2
exec "$_new" "$@"
