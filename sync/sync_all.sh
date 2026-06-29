#!/usr/bin/env bash
# Sync configuration sources to Cursor / Codex / Claude Code / Cline / Xcode.
#
# Source (sibling of this sync/ dir):
#   - env/config.json — MCP catalog + platform-specific env/config, gitignored.
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
CONFIG_JSON="$REPO_ROOT/env/config.json"

if [ ! -f "$CONFIG_JSON" ]; then
  echo "[sync] $CONFIG_JSON is missing (gitignored local file)." >&2
  echo "[sync] Copy env/config.json.example -> env/config.json, edit, then run this script again." >&2
  echo "[sync] Skipping sync; pre-push will not block on this." >&2
  exit 0
fi

echo "[1/1] Sync config to Cursor / Codex / Claude / Cline / Xcode"
python3 "$SCRIPT_DIR/sync_config.py" --target all

# Source ~/.zshrc to load any env vars written by the sync (e.g. DATAEYES_API_KEY).
# This takes effect in the current script process only; to apply immediately in your
# open terminal run: source ~/.zshrc
if [ -f "$HOME/.zshrc" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.zshrc" 2>/dev/null || true
  echo "[sync] Sourced ~/.zshrc — run 'source ~/.zshrc' in your terminal for immediate effect."
fi

echo "Done."
