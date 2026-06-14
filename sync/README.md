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

## Design

The architecture is deliberately split into three layers:

| Layer | Owner | Purpose |
|------|-------|---------|
| Source | `env/config.json` | One maintained config file: MCP catalog, shared env, and platform-specific env/config. |
| Renderer | `sync/platforms/*.py` | Converts source schema into each platform's required file format. |
| Orchestrator | `sync/sync_config.py` | Loads the source and dispatches to selected platform renderers. |
| Target | Cursor / Codex / Claude / Xcode paths | Generated or merged files; never edited as the source of truth. |

Platform independence lives inside the single config file:

```json
{
  "env": { "shared": {} },
  "platforms": {
    "rag-gateway": { "env": {} },
    "claude": { "env": {} },
    "codex": { "env": {}, "features": {}, "projects": {} }
  }
}
```

`env.shared` is optional. Values under `platforms.<name>.env` override shared values for that platform. This keeps Gateway, Claude, and Codex separately configurable without splitting the source into multiple files.

## Targets

| Target | Output |
|------|--------|
| Cursor | Merge `mcpServers` into `~/.cursor/mcp.json`, preserving other keys and existing non-source servers. |
| Codex CLI | `~/.codex/mcp.generated.toml` plus managed blocks in `~/.codex/config.toml`. |
| Xcode Codex | `~/Library/Developer/Xcode/CodingAssistant/codex/` with the same TOML rendering. |
| Claude Code | Merge `mcpServers` into `~/.claude.json`, preserving other keys and existing non-source servers. |
| Xcode Claude Agent | Merge `mcpServers` into `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`; per-project when projects already exist. |
| Claude settings | Merge `platforms.claude.env` into `~/.claude/settings.json` `env`, preserving unrelated env keys. |
| RAG Gateway | `rag-gateway/src/config.ts` reads `platforms["rag-gateway"].env` directly from `env/config.json`; `.env` still wins at runtime. |

Codex targets are TOML because Codex config is TOML. The maintained source remains JSON; `sync_config.py` is the adapter.

## Adding Platforms

Add one renderer module under `sync/platforms/`, then register it in `TARGETS` inside `sync/sync_config.py`.

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
python3 sync/sync_config.py --target codex
python3 sync/sync_config.py --target claude
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

JSON targets are merge-only: source keys from `env/config.json` are added or updated, while keys not present in the source are left untouched. Removing a stale key from a JSON target remains a manual cleanup step.

## Safety

`env/config.json` is gitignored because it may contain API keys and MCP tokens. Commit only `env/config.json.example`.
