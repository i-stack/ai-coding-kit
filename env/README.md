# env

配置数据源目录，`sync/` 引擎从此处读取所有平台和 MCP 服务器的定义。

## 目录结构

```text
env/
├── secrets.json              ← 你唯一需要填写的文件（gitignored）
├── secrets.json.example      ← 模板（已提交）
│
├── review.json               ← auto-code-review 配置（gitignored）
├── review.json.example       ← review 配置模板（已提交）
├── backup.json               ← 配置备份保存路径（gitignored）
├── backup.json.example       ← backup 配置模板（已提交）
│
├── mcp/                      ← 默认启用的 MCP 服务器定义
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
├── optional-mcps/            ← 可选 MCP 服务器（需手动启用）
│   ├── enabled.json          ← 启用状态记录
│   ├── filesystem-extra.json
│   ├── puppeteer.json
│   ├── wechat-bridge.json
│   └── README.md
│
├── platforms/                ← 平台专属配置
│   ├── claude.json
│   ├── cline.json
│   ├── codex.json
│   ├── codebuddy.json
│   ├── continue.json
│   ├── gemini.json
│   └── qwen.json
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

## review.json

跨模型代码审查（auto-code-review）的执行参数配置：

```json
{
  "enabled": true,
  "reviewers": [],
  "maxRounds": 3,
  "allowSelfReview": false
}
```

| 字段 | 说明 |
|------|------|
| `enabled` | 功能是否可用（`true` 只表示功能可用，不构成当前请求授权） |
| `reviewers` | 审查者列表（空数组则自动发现可用 CLI） |
| `maxRounds` | 最大审查轮次 |
| `allowSelfReview` | 是否允许自审 |

**加载优先级**：`env/review.json` → `.auto-review-config.json` → `AUTO_REVIEW_*` 环境变量。

复制 `review.json.example` 为 `review.json` 后填写即可。仅在用户显式启动 `/auto-review` 后加载。

## backup.json

`sync/scripts/backup-config.sh` 默认把同步前备份保存到 `~/.ai-coding-kit-backups`。
如果要改保存目录，复制 `backup.json.example` 为 `backup.json`：

```json
{
  "backupDir": "~/Backups/ai-coding-kit"
}
```

- `backupDir` 留空或删除时回退到默认 `~/.ai-coding-kit-backups`。
- 支持 `~` 和环境变量展开。
- 相对路径会按仓库根目录解析。
- `env/backup.json` 是本地用户配置，不提交。

## optional-mcps — 可选 MCP 服务器

将**非默认、社区/高级**的 MCP 服务器与开箱即用的 `env/mcp/` 集合分开，避免污染默认配置，同时保留「一键启用」能力。

### 工作机制

- `env/optional-mcps/*.json`：可选的 MCP 服务器定义（**不**自动同步）
- `sync/scripts/optional_mcps.sh enable <name>`：启用并同步到 `env/mcp/`
- `sync/scripts/optional_mcps.sh disable <name>`：禁用并移除
- 启用状态记录在 `env/optional-mcps/enabled.json`

### 用法

```bash
# 列出所有可选服务器及其启用状态
bash sync/scripts/optional_mcps.sh list

# 启用一个
bash sync/scripts/optional_mcps.sh enable puppeteer

# 禁用一个
bash sync/scripts/optional_mcps.sh disable puppeteer
```

### 可用服务器

| 服务器 | 说明 | 需要 secret |
|--------|------|-------------|
| `puppeteer` | 浏览器自动化（与默认 `playwright` 互补，择一启用） | 否 |
| `filesystem-extra` | 扩展文件系统访问 | 是（`filesystem_extra.root`） |
| `wechat-bridge` | 微信桥接 | 是（`wechat.token`） |

详见 [optional-mcps/README.md](optional-mcps/README.md)。

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
