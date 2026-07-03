# sync

`sync/` reads MCP server definitions and platform configs, then renders them into each platform's native format.

## Canonical sources

```text
env/mcp/*.json           — MCP server definitions (one file per server)
env/platforms/*.json     — platform-specific configs (follow each platform's spec)
```

## Setup

```bash
# 1. Create MCP configs from template
cp env/templates/mcp.template.json env/mcp/github.json
$EDITOR env/mcp/github.json

# 2. Create platform configs from template
cp env/templates/platform.template.json env/platforms/codex.json
$EDITOR env/platforms/codex.json

# 3. Sync
bash sync.sh
```

## MCP Server File Format

Each `env/mcp/<name>.json`:

```json
{
  "name": "my-server",
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "my-mcp-package"],
  "env": {},
  "platforms": ["claude", "codex", "codebuddy"]
}
```

- `type`: `"stdio"` (requires `command`/`args`) or `"sse"` (requires `url`/`headers`)
- `platforms`: optional filter — omit to sync to all platforms, or list specific platforms
- `env`: environment variables passed to the MCP server process

## Platform Config Files

Each `env/platforms/<name>.json` follows that platform's **official configuration spec**:

| Platform | File | Follows |
|----------|------|---------|
| Codex | `codex.json` | [Codex config.toml schema](https://developers.openai.com/codex/config-reference) |
| Claude | `claude.json` | Claude Code settings.json `env` + `hooks` |
| CodeBuddy | `codebuddy.json` | CodeBuddy `models.json` schema |
| Gemini | `gemini.json` | Gemini CLI env vars |
| Continue | `continue.json` | Continue `config.yaml` models |
| Cursor | `cursor.json` | (no platform config needed) |
| Cline | `cline.json` | (no platform config needed) |
| RAG Gateway | `rag-gateway.json` | Gateway env vars |

The JSON keys map directly to the platform's native format — no field name translation needed.

## Targets

| Target | Output |
|--------|--------|
| Cursor | Replace `mcpServers` in `~/.cursor/mcp.json` |
| CodeBuddy | Replace `mcpServers` in `~/.codebuddy/mcp.json`, sync `models.json`, skills |
| Codex CLI | `~/.codex/mcp.generated.toml` + managed blocks in `config.toml` |
| Xcode Codex | `~/Library/.../CodingAssistant/codex/` |
| Claude Code | Replace `mcpServers` in `~/.claude.json` + Xcode Claude |
| Claude settings | Merge `env` + `hooks` into `~/.claude/settings.json` |
| Cline | Replace `mcpServers` in VSCode extension settings + skills sync |
| Gemini CLI | Replace `mcpServers` in `~/.gemini/settings.json` + `~/.zshrc` env |
| Continue | Update `mcpServers` + `models` in `~/.continue/config.yaml` |

## Adding a Platform

1. Copy template: `cp env/templates/platform.template.json env/platforms/my-platform.json`
2. Fill in config following the platform's official spec
3. If the platform only needs `mcpServers` in a JSON file, add `"mcp_target": "~/.my-platform/mcp.json"` to the config
4. If custom rendering is needed, create `sync/platforms/my_platform.py` with a `sync(mcp_servers, cfg)` function and register in `sync_config.py`

## Adding an MCP Server

```bash
cp env/templates/mcp.template.json env/mcp/my-new-server.json
$EDITOR env/mcp/my-new-server.json
bash sync.sh
```

## Commands

```bash
bash sync.sh                              # sync all
python3 sync/sync_config.py --target all  # sync all (Python direct)
python3 sync/sync_config.py --target codex  # single platform
```

## Design Principles

1. **MCP separation**: one file per server — no monolithic config
2. **Platform spec compliance**: config keys match the platform's native naming exactly
3. **Zero field-name mapping**: renderers convert format (JSON→TOML, JSON→YAML), not field names
4. **Auto-discovery**: platforms are discovered from `env/platforms/` directory

## Safety

All files under `env/mcp/` and `env/platforms/` are gitignored (contain secrets).
Only `env/templates/` is committed (no secrets, placeholder values only).
