#!/usr/bin/env bash
# Sync configuration sources to Cursor / Codex / Claude Code / Xcode.
#
# Sources (siblings of this sync/ dir):
#   - mcp/servers.json     — MCP server catalog (gitignored, local secrets)
#   - env/codex/shared.toml    — shared Codex config (model, provider, features, projects)
#   - env/claude/settings.shared.json — Claude Code environment variables
#
# Targets:
#   1) Cursor: symlink ~/.cursor/mcp.json → mcp/servers.json (updates when source changes).
#   2) Codex CLI + Xcode Coding Assistant: regenerate ~/.codex/mcp.generated.toml and
#      ~/Library/Developer/Xcode/CodingAssistant/codex/mcp.generated.toml, then merge the
#      MCP and CODEX SHARED marker blocks into each config.toml (anything outside the
#      markers is preserved).
#   3) Claude Code: merge mcpServers into ~/.claude.json and into Xcode's
#      ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json
#      (per-project mcpServers).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_JSON="$REPO_ROOT/mcp/servers.json"

if [ ! -f "$MCP_JSON" ]; then
  echo "[sync] $MCP_JSON is missing (gitignored local file)." >&2
  echo "[sync] Copy mcp/servers.json.example → mcp/servers.json, edit, then run this script again." >&2
  echo "[sync] Skipping sync; pre-push will not block on this." >&2
  exit 0
fi

echo "[1/3] Sync Cursor (symlink)"
mkdir -p ~/.cursor
ln -sf "$MCP_JSON" ~/.cursor/mcp.json

echo "[2/3] Sync Codex (generate TOML; includes Xcode CodingAssistant/codex)"
python3 "$SCRIPT_DIR/sync_mcp.py"

echo "[3/3] Sync Claude Code (merge ~/.claude.json + Xcode ClaudeAgentConfig)"
if [ -f "$SCRIPT_DIR/sync_claude.py" ]; then
  python3 "$SCRIPT_DIR/sync_claude.py"
else
  echo "sync_claude.py not found; skip Claude."
fi

echo "[4/4] Sync Claude Code settings (merge env into ~/.claude/settings.json)"
if [ -f "$SCRIPT_DIR/sync_claude_settings.py" ]; then
  python3 "$SCRIPT_DIR/sync_claude_settings.py"
else
  echo "sync_claude_settings.py not found; skip."
fi

echo "Done."
