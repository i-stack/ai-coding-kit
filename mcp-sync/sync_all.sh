#!/usr/bin/env bash
# Sync MCP data from this repo's mcp-servers.json to Cursor / Codex / Claude Code / Xcode.
# 1) Cursor: symlink → .cursor updates when data source updates.
# 2) Codex: generate mcp.generated.toml and merge into config.toml (marked block only; rest unchanged),
#    and the same into ~/Library/Developer/Xcode/CodingAssistant/codex/ for Xcode's built-in Codex.
# 3) Claude Code: merge mcpServers into ~/.claude.json and into Xcode's
#    ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json (per-project mcpServers).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Sync Cursor (symlink)"
mkdir -p ~/.cursor
ln -sf "$SCRIPT_DIR/mcp-servers.json" ~/.cursor/mcp.json

echo "[2/3] Sync Codex (generate TOML; includes Xcode CodingAssistant/codex)"
python3 "$SCRIPT_DIR/sync_mcp.py"

echo "[3/3] Sync Claude Code (merge ~/.claude.json + Xcode ClaudeAgentConfig)"
if [ -f "$SCRIPT_DIR/sync_claude.py" ]; then
  python3 "$SCRIPT_DIR/sync_claude.py"
else
  echo "sync_claude.py not found; skip Claude."
fi

echo "Done."
