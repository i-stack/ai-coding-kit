# sync

`sync/` reads MCP server definitions and platform configs, **injects secrets** from `env/secrets.json`, then renders them into each platform's native format.

## 快速开始（3 步）

```bash
# 1. 复制 secrets 模板（唯一需要创建的文件）
cp env/secrets.json.example env/secrets.json

# 2. 编辑填写你的 API Keys
$EDITOR env/secrets.json

# 3. 一键同步到所有平台
bash sync.sh
```

## 架构

```text
env/
├── secrets.json            ← 你唯一需要配置的文件（gitignored）
├── secrets.json.example    ← 模板（已提交，列出所有需要的 Key）
│
├── mcp/                    ← MCP 服务器定义（已提交，开箱即用）
│   ├── github.json         ← token 用 ${github.token} 占位
│   ├── apifox.json
│   └── ...
│
├── platforms/              ← 平台配置（已提交，开箱即用）
│   ├── codex.json          ← url/key 用 ${codex.url}/${codex.key} 占位
│   ├── claude.json
│   └── ...
│
└── templates/              ← 模板（供新增 MCP/平台时参考）
    ├── mcp.template.json
    └── platform.template.json
```

## 占位符机制

所有配置文件的敏感值使用 `${platform.field}` 占位，同步时从 `env/secrets.json` 注入：

```json
// env/mcp/github.json（已提交）
{ "headers": { "Authorization": "Bearer ${github.token}" } }

// env/platforms/codex.json（已提交）
{ "model_providers": { "dataeyes": {
    "base_url": "${codex.url}",
    "env_key": "DATAEYES_API_KEY"
  }},
  "env": { "DATAEYES_API_KEY": "${codex.key}" }
}

// env/secrets.json（不提交，用户填写 — 每个平台一个对象）
{
  "github": { "token": "ghp_xxx" },
  "codex":  { "url": "https://api.example.com/v1", "key": "sk-xxx" },
  ...
}

// 运行时解析为：
{ "headers": { "Authorization": "Bearer ghp_xxx" } }
{ "base_url": "https://api.example.com/v1", ... }
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
- Secrets: use `${platform.field}` syntax, resolved from nested `env/secrets.json` at sync time

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
| Cline | `cline.json` | Merge `globalState` + `secrets` into `~/.cline/data/` |
| Qwen Code | `qwen.json` | Merge `env` into `~/.qwen/settings.json`, sync skills |

The JSON keys map directly to the platform's native format — no field name translation needed.

## Targets

For Cline, Codex, Claude, CodeBuddy, Gemini, Continue, and Qwen Code, sync first checks
the tool's home directory (`~/.cline`, `~/.codex`, `~/.claude`,
`~/.codebuddy`, `~/.gemini`, `~/.continue`, `~/.qwen`). If that root does not
exist, the target is skipped so sync does not create config for tools the user
has not installed.

Xcode CodingAssistant targets are checked separately. If
`~/Library/Developer/Xcode/CodingAssistant` does not exist, native CLI targets
still sync, but the Xcode-specific Codex / Claude / Gemini outputs are skipped.

| Target | Output |
|--------|--------|
| Cursor | Replace `mcpServers` in `~/.cursor/mcp.json` |
| CodeBuddy | Replace `mcpServers` in `~/.codebuddy/mcp.json`, sync `models.json`, skills |
| Codex CLI | Managed MCP + shared blocks in `~/.codex/config.toml` |
| Xcode Codex | `~/Library/.../CodingAssistant/codex/` |
| Claude Code | Replace `mcpServers` in `~/.claude.json` + Xcode Claude |
| Claude settings | Merge `env` + `hooks` into `~/.claude/settings.json`, set `~/.claude/config.json` `primaryApiKey` to `self` |
| Cline | Replace `mcpServers` in VSCode extension settings + skills sync + merge `globalState`/`secrets` into `~/.cline/data/` |
| Gemini CLI | Replace `mcpServers` in `~/.gemini/settings.json` + `~/.zshrc` env |
| Continue | Update `mcpServers` + `models` in `~/.continue/config.yaml`, creating it when `~/.continue` exists |
| Qwen Code | Merge `env` into `~/.qwen/settings.json`, sync skills to `~/.qwen/skills/` |

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

1. **One file to configure**: user only edits `env/secrets.json` — each platform has its own `{url, key/token}` object
2. **MCP separation**: one file per server — no monolithic config
3. **Platform spec compliance**: config keys match the platform's native naming exactly
4. **Zero field-name mapping**: renderers convert format (JSON→TOML, JSON→YAML), not field names
5. **Auto-discovery**: platforms are discovered from `env/platforms/` directory
6. **Secrets injection**: `${platform.field}` references are resolved from nested `env/secrets.json` at sync time

## Safety

- `env/secrets.json` is **gitignored** — never committed
- `env/mcp/*.json` and `env/platforms/*.json` are **committed** — use `${VAR}` placeholders, no real secrets
- `env/secrets.json.example` is **committed** — shows required keys with placeholder values
- `env/templates/` is **committed** — templates for adding new servers/platforms
