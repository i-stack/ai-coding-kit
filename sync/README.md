# sync

`sync/` renders one local config file into each host's native format.

Canonical source:

```text
env/config.json
```

Template:

```bash
cp env/config.json.example env/config.json
$EDITOR env/config.json
```

## MCP Server Platform Filtering

By default every MCP server is synced to every platform. Add an optional `platforms` array to limit which platforms receive a server:

```json
"mcpServers": {
    "XcodeBuildMCP": {
        "command": "npx",
        "args": ["-y", "xcodebuildmcp@latest", "mcp"],
        "platforms": ["claude", "codex"]
    },
    "design-handoff": {
        "url": "http://localhost:8000/mcp",
        "platforms": ["claude", "cline"]
    },
    "github": {
        "url": "https://api.githubcopilot.com/mcp/"
    }
}
```

- `"platforms": ["claude", "codex"]` — only claude and codex receive this server.
- No `platforms` field — all platforms receive this server (existing behavior preserved).

The `platforms` key is stripped from the output; target config files never see it.

## Design

The architecture is deliberately split into three layers:

| Layer | Owner | Purpose |
|------|-------|---------|
| Source | `env/config.json` | One maintained config file: MCP catalog, shared env, and platform-specific env/config. |
| Renderer | `sync/platforms/*.py` | Converts source schema into each platform's required file format. |
| Orchestrator | `sync/sync_config.py` | Loads the source and dispatches to selected platform renderers. |
| Target | Cursor / CodeBuddy / Codex / Claude / Xcode paths | Generated or merged files; never edited as the source of truth. |

Platform independence lives inside the single config file:

```json
{
  "platforms": {
    "gateway": { "env": {} },
    "claude": { "env": {} },
    "codex": { "env": {}, "features": {}, "projects": {} }
  }
}
```

Values under `platforms.<name>.env` are scoped to that platform. No global `env.shared` — each platform owns its own env vars.

## Targets

| Target | Output |
|------|--------|
| Cursor | Replace `mcpServers` in `~/.cursor/mcp.json`, preserving other top-level keys. |
| CodeBuddy | Replace `mcpServers` in `~/.codebuddy/mcp.json`, sync models to `~/.codebuddy/models.json`, and copy skills from `~/.claude/skills/` to `~/.codebuddy/skills/`. |
| Codex CLI | `~/.codex/mcp.generated.toml` plus managed blocks in `~/.codex/config.toml`. |
| Xcode Codex | `~/Library/Developer/Xcode/CodingAssistant/codex/` with the same TOML rendering. |
| Claude Code | Replace `mcpServers` in `~/.claude.json`, preserving other top-level keys. |
| Xcode Claude Agent | Replace `mcpServers` in `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`; per-project when projects already exist. |
| Claude settings | Merge `platforms.claude.env` into `~/.claude/settings.json` `env`, preserving unrelated env keys. |
| RAG Gateway | `rag-gateway/src/config.ts` reads `platforms["rag-gateway"].env` directly from `env/config.json`; `.env` still wins at runtime. |
| Continue | Replace `mcpServers` (with SSE header compatibility mapping) and update `models` in `~/.continue/config.yaml`. |

Codex targets are TOML because Codex config is TOML. The maintained source remains JSON; `sync_config.py` is the adapter.

## Adding Platforms

**Complex platforms** (custom config format, multi-file writes, or extra logic) need a renderer module:

1. Add `sync/platforms/<name>.py` with a `sync(data) -> None` function.
2. Register it in `TARGETS` inside `sync/sync_config.py`.

**Simple JSON-MCP platforms** (only need `mcpServers` written to a JSON file) can be declared directly in `env/config.json` without any Python:

```json
"platforms": {
    "zed": { "type": "json-mcp", "path": "~/.config/zed/mcp.json" }
}
```

`sync_config.py` auto-discovers all `type=json-mcp` entries and builds sync functions for them at runtime. Adding Zed, Kiro, or any other simple platform requires only a config change.

Do not add another top-level sync script for each platform. The stable command should remain:

```bash
python3 sync/sync_config.py --target <platform>
```

This keeps orchestration, CLI flags, and missing-config behavior in one place while letting each platform own its native rendering.

## Codex Model Provider

`platforms.codex.modelProvider` controls whether the generated Codex TOML pins a custom provider:

```json
"modelProvider": "custom"
```

Generates:

```toml
model_provider = "custom"

[model_providers.custom]
...
```

Omit `modelProvider` or set it to `null` / `""` to avoid generating `model_provider` and `[model_providers.*]`. In that mode, Codex uses its own default provider/model behavior, while other shared fields such as `[features]`, `[projects.*]`, and MCP blocks still sync.

## Commands

```bash
bash sync/sync_all.sh
```

Targeted runs:

```bash
python3 sync/sync_config.py --target cursor
python3 sync/sync_config.py --target codebuddy
python3 sync/sync_config.py --target codex
python3 sync/sync_config.py --target claude
python3 sync/sync_config.py --target gemini
python3 sync/sync_config.py --target continue
```

## Managed Blocks

Codex config files contain two generated regions:

```text
# BEGIN CODEX SHARED (from env/config.json)
...
# END CODEX SHARED

# BEGIN MCP SYNC (from env/config.json)
...
# END MCP SYNC
```

Everything outside those markers is host-specific and preserved. Keep `developer_instructions`, sandbox, plugins, Xcode-only MCP, notifications, and local overrides outside managed blocks.

JSON MCP targets treat `env/config.json` as authoritative: each run replaces the target `mcpServers` object so source-side deletes and edits propagate. Non-MCP top-level keys are preserved. Platform env blocks, such as Claude settings `env`, remain merge-based so unrelated local environment keys survive.

## Safety

`env/config.json` is gitignored because it may contain API keys and MCP tokens. Commit only `env/config.json.example`.
keys and MCP tokens. Commit only `env/config.json.example`.
