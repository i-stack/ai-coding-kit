#!/usr/bin/env bash
# Sync MCP servers and platform configs to native formats.
#
# Sources:
#   env/mcp/*.json          — MCP server definitions (platform-agnostic)
#   env/platforms/*.json    — platform-specific configs
#
# Targets:
#   1) Cursor: generate ~/.cursor/mcp.json with mcpServers.
#   2) Codex CLI + Xcode Coding Assistant: regenerate ~/.codex/mcp.generated.toml and
#      ~/Library/Developer/Xcode/CodingAssistant/codex/mcp.generated.toml, then merge the
#      MCP and CODEX SHARED marker blocks into each config.toml.
#   3) Claude Code: replace mcpServers in ~/.claude.json and in Xcode's
#      ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json
#      (per-project mcpServers), plus env into ~/.claude/settings.json.
#   4) Cline: replace mcpServers in the VSCode extension MCP settings JSON, and copy
#      skills from ~/.claude/skills/ into ~/.cline/skills/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$REPO_ROOT/env/mcp"

if [ ! -d "$MCP_DIR" ] || [ -z "$(ls -A "$MCP_DIR"/*.json 2>/dev/null || true)" ]; then
  echo "[sync] No MCP config files found in $MCP_DIR." >&2
  echo "[sync] Copy env/templates/mcp.template.json -> env/mcp/<name>.json, edit, then run again." >&2
  echo "[sync] Skipping sync; pre-push will not block on this." >&2
  exit 0
fi

# Auto-backup config before sync (keeps last 10 in ~/.ai-coding-kit-backups/)
bash "$SCRIPT_DIR/backup-config.sh" backup

echo "[1/1] Sync config to Cursor / CodeBuddy / Codex / Claude / Cline / Xcode"
python3 "$SCRIPT_DIR/sync_config.py" --target all

# Source ~/.zshrc to load any env vars written by the sync.
if [ -f "$HOME/.zshrc" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.zshrc" 2>/dev/null || true
  echo "[sync] Sourced ~/.zshrc — run 'source ~/.zshrc' in your terminal for immediate effect."
fi

echo "Done."
