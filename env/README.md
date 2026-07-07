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
│   └── moonvy.json
│
├── platforms/                ← 平台专属配置
│   ├── claude.json
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
