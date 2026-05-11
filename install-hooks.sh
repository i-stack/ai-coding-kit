#!/usr/bin/env bash
# Install repository-managed git hooks for ai-coding-kit.
#
# Registers the root .githooks/ directory with this clone:
#   - pre-commit:  SKILL evolution-proposal guard for skills-engineering/ios-engineer/
#   - pre-push:    skill-sync chain + mcp-sync (sync_all.sh)
#
# Run this once per clone:
#   bash install-hooks.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

if [ ! -d .githooks ]; then
  echo "install-hooks: .githooks directory not found at $REPO_ROOT" >&2
  exit 1
fi

chmod +x .githooks/* 2>/dev/null || true

git config core.hooksPath .githooks

echo "core.hooksPath: $(git config --get core.hooksPath)"
echo "Hooks installed:"
ls -la .githooks/ | tail -n +2 | awk '{print "  " $0}'
echo ""
echo "Bypass single push:   git push --no-verify"
echo "Bypass skill checks:  SKILL_BYPASS=1 git commit / git push"
