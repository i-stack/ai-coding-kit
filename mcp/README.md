# mcp

MCP server catalog — the single source of truth for which MCP servers are
exposed to Cursor, Codex (CLI + Xcode), and Claude Code (CLI + Xcode).

## Files

| File | Purpose | Tracked? |
|------|---------|----------|
| `servers.json` | Live config with real tokens. **gitignored** — never commit. | No |
| `servers.json.example` | Empty template. Copy → `servers.json`, then fill in secrets. | Yes |

## Workflow

```bash
# From repo root
cp mcp/servers.json.example mcp/servers.json
$EDITOR mcp/servers.json              # paste tokens / project IDs
bash sync/sync_all.sh                  # propagate to all hosts
```

See [../sync/README.md](../sync/README.md) for the sync targets and the
`# BEGIN/END MCP SYNC` marker-block contract.
