# env

配置数据源目录，`sync/` 引擎从此处读取所有平台和 MCP 服务器的定义。

## 目录结构

```text
env/
├── secrets.json              ← 你唯一需要填写的文件（gitignored）
├── secrets.json.example      ← 模板（已提交）
│
├── mcp/                      ← MCP 服务器定义
│   ├── github.json
│   ├── apifox.json
│   ├── filesystem.json
│   ├── playwright.json
│   ├── shell.json
│   ├── xcodebuild.json
│   ├── lanhu.json
│   ├── moonvy.json
│   ├── postgres.json
│   └── sqlite.json
│
├── platforms/                ← 平台专属配置
│   ├── claude.json
│   ├── cline.json
│   ├── codex.json
│   ├── codebuddy.json
│   ├── continue.json
│   ├── gemini.json
│
└── templates/                ← 新增 MCP/平台的参考模板
    ├── mcp.template.json
    └── platform.template.json
```

## secrets.json

嵌套结构，每个平台一个对象：

```json
{
  "github":   { "token": "ghp_xxx" },
  "codex":    { "url": "https://api.example.com/v1", "key": "sk-xxx" },
  "claude":   { "token": "sk-ant-xxx" },
  ...
}
```

新增平台时只需在此文件中追加对应的 `{url, key/token}` 即可。

## 自定义安装路径（paths）

各平台的安装根目录默认是 `~/.codex`、`~/.claude`、`~/.gemini` 等固定位置。
如果某工具安装在非默认路径（例如自定义前缀、便携版、或 Xcode 的 CodingAssistant 目录被移动），
可以在 `secrets.json` 顶层增加 `paths` 对象来覆盖：

```json
{
  "paths": {
    "codex": "/opt/codex",
    "claude": "/custom/.claude",
    "gemini": "/custom/.gemini",
    "codebuddy": "/custom/.codebuddy",
    "cursor": "/custom/.cursor",
    "cline": "/custom/.cline",
    "continue": "/custom/.continue",
    "qwen": "/custom/.qwen",
    "xcode_coding_assistant": "~/Library/Developer/Xcode/CodingAssistant"
  }
}
```

- 键名与平台一致；留空字符串 `""` 或删除该键即回退默认路径。
- 设置后，该平台的所有派生路径（配置、settings、skills、MCP 文件等）都会基于覆盖值解析。
- Codex 仍优先使用标准环境变量 `CODEX_HOME` / `CODEX_CONFIG`，其次才是此处覆盖。
- `paths` 不是密钥，不会参与 `${...}` 占位符注入，仅用于路径解析。

## 占位符机制

所有 `mcp/` 和 `platforms/` 下的配置使用 `${platform.field}` 语法引用 secrets：

```json
// env/mcp/github.json
{ "headers": { "Authorization": "Bearer ${github.token}" } }

// env/platforms/codex.json
{ "base_url": "${codex.url}", "env": { "DATAEYES_API_KEY": "${codex.key}" } }
```

同步时由 `sync/platforms/common.py` 自动替换为真实值。

## 模板

- `templates/mcp.template.json` — 新增 MCP 服务器时复制并填写
- `templates/platform.template.json` — 新增平台时复制并填写

详见 [sync/README.md](../sync/README.md)。
