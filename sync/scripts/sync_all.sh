#!/usr/bin/env bash
# Sync MCP servers and platform configs to native formats.
#
# Sources:
#   env/mcp/*.json              — MCP server definitions (platform-agnostic)
#   env/platforms/*.json        — platform-specific configs
#   env/user-profile.json       — optional cross-session user profile sync config
#
# Targets:
#   1) Cursor: generate ~/.cursor/mcp.json with mcpServers.
#   2) Codex CLI + Xcode Coding Assistant: merge the MCP and CODEX SHARED
#      marker blocks into each config.toml.
#   3) Claude Code: replace mcpServers in ~/.claude.json and in Xcode's
#      ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json
#      (per-project mcpServers), plus env into ~/.claude/settings.json and
#      primaryApiKey=self into ~/.claude/config.json.
#   4) Cline: replace mcpServers in the VSCode extension MCP settings JSON, and copy
#      skills from ~/.claude/skills/ into ~/.cline/skills/.
#      Cline, Codex, Claude, CodeBuddy, Gemini, and Continue are skipped when their
#      tool home directory does not exist.
#      Xcode targets are skipped when ~/Library/Developer/Xcode/CodingAssistant
#      does not exist.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MCP_DIR="$REPO_ROOT/env/mcp"
SECRETS_FILE="$REPO_ROOT/env/secrets.json"

if [ ! -d "$MCP_DIR" ] || [ -z "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ]; then
  echo "[sync] No MCP config files found in $MCP_DIR." >&2
  echo "[sync] Copy env/templates/mcp.template.json -> env/mcp/<name>.json, edit, then run again." >&2
  echo "[sync] Skipping sync; pre-push will not block on this." >&2
  exit 0
fi

if [ ! -f "$SECRETS_FILE" ]; then
  echo "[sync] env/secrets.json not found." >&2
  echo "[sync] Copy env/secrets.json.example -> env/secrets.json, fill in your keys, then run again." >&2
  echo "[sync] Skipping sync to avoid writing unresolved \${...} placeholders into local agent configs." >&2
  exit 0
fi

echo "[1/2] Sync config to Cursor / CodeBuddy / Codex / Claude / Cline / Xcode"
python3 "$REPO_ROOT/sync/cli/main.py" sync --target all

echo "[2/2] Sync user profile (optional)"
if [[ "${SKIP_USER_PROFILE:-false}" != "true" ]]; then
  if ! bash "$REPO_ROOT/skills-engineering/scripts/sync-user-profile.sh"; then
    echo "[sync] User profile sync failed; continuing because it is optional." >&2
  fi
else
  echo "  (skipped: SKIP_USER_PROFILE=true)"
fi

echo "[sync] If env vars were updated, run 'source ~/.zshrc' in your terminal to apply them."

echo "Done."
