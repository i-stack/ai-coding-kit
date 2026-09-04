# env

配置数据源目录，`sync/` 引擎从此处读取所有平台和 MCP 服务器的定义。

## 目录结构

```text
env/
├── secrets.json              ← 密钥配置：key/token/url（gitignored）
├── secrets.json.example      ← 模板（已提交）
├── config.json              ← 非密钥配置：安装根/路径覆盖（gitignored，可选）
├── config.json.example      ← 模板（已提交）
│
├── review.json               ← auto-code-review 配置（gitignored）
├── review.json.example       ← review 配置模板（已提交）
├── user-profile.json         ← 跨会话用户画像同步开关（gitignored）
├── user-profile.json.example ← 用户画像同步配置模板（已提交）
├── user-profile.md           ← 跨会话用户画像内容（gitignored）
├── user-profile.md.example   ← 用户画像内容模板（已提交）
│
├── mcp/                      ← 默认启用的 MCP 服务器定义
│   ├── github.json
│   ├── apifox.json
│   ├── filesystem.json
│   ├── playwright.json
│   ├── shell.json
│   ├── xcodebuild.json
│   ├── lanhu.json
│   └── moonvy.json
│
├── optional_mcps/            ← 可选 MCP 服务器（需手动启用）
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

复制 `review.json.example` 为 `review.json` 后填写即可（`bash install.sh` 会一并从模板创建，无需手动 cp）。仅在用户显式启动 `/auto-review` 后加载。

## user-profile.json + user-profile.md

跨会话用户画像用于让 Codex / Claude / Gemini 等 Agent 在不同会话中共享你的稳定偏好、角色和约束。

```bash
bash install.sh   # 创建 user-profile.json（enabled=auto）；user-profile.md 不自动创建
bash sync.sh      # 同步（画像文件缺失时自动跳过）
```

> `env/user-profile.md` 是含占位符的内容模板，`install.sh` 不会自动复制它，否则会被当成真实画像同步成假的全局用户画像。需要画像时再手动：
>
> ```bash
> cp env/user-profile.md.example env/user-profile.md   # 然后填写真实信息
> ```

`env/user-profile.json`：

```json
{
  "enabled": "auto",
  "source": "env/user-profile.md"
}
```

| 字段 | 说明 |
|------|------|
| `enabled` | `auto`：画像文件存在则同步，不存在则跳过；`on`：强制同步，不存在时报错；`off`：跳过同步 |
| `source` | 用户画像 Markdown 路径，支持 `~`、环境变量和相对仓库根目录的路径 |

同步时会把画像复制到 `~/.ai-coding-kit/USER.md`，并向各端 Agent preamble 注入 `user-profile` 托管块。
如需清理已注入托管块，运行：

```bash
bash skills-engineering/scripts/sync-user-profile.sh --remove
```

## mcp/ 同步开关（enabled）

`env/mcp/*.json` 默认全部同步到各平台。如需按需选择安装哪些 MCP 服务器，
在每个服务器的定义中加入 `"enabled": false` 即可跳过同步：

```json
// env/mcp/shell.json
{
    "name": "shell",
    "enabled": false,
    "command": "..."
}
```

| 取值 | 行为 |
|------|------|
| 缺省 / `true` | 同步到所有声明的平台（默认行为） |
| `false` | 不参与同步；下次 `bash sync.sh` 时会将该服务器从已同步的目标配置中自动移除（marker 清理），用户自己添加的同名服务器不受影响 |

`enabled` 与平台配置中 `api.enabled` 的语义一致：缺省即启用，只有显式 `false` 才关闭。
同样适用于 `env/optional_mcps/` 中启用后的可选服务器。

## optional_mcps — 可选 MCP 服务器

将**非默认、社区/高级**的 MCP 服务器与开箱即用的 `env/mcp/` 集合分开，避免污染默认配置，同时保留「一键启用」能力。

### 工作机制

- `env/optional_mcps/*.json`：可选的 MCP 服务器定义（**不**自动同步）
- `sync/scripts/optional_mcps.sh enable <name>`：启用并同步到 `env/mcp/`
- `sync/scripts/optional_mcps.sh disable <name>`：禁用并移除
- 启用状态记录在 `env/optional_mcps/enabled.json`

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

详见 [optional_mcps/README.md](optional_mcps/README.md)。

## 自定义安装路径（paths）

各平台的安装根目录默认是 `~/.codex`、`~/.claude`、`~/.gemini` 等固定位置。
如果某工具安装在非默认路径（例如自定义前缀、便携版、或 Xcode 的 CodingAssistant 目录被移动），
可以在 `config.json` 顶层增加 `paths` 对象来覆盖（`bash install.sh` 会自动从 `config.json.example` 创建该文件，也可手动 `cp env/config.json.example env/config.json`）：

```json
{
  "paths": {
    "codex": "/opt/codex",
    "claude": "/custom/.claude",
    "gemini": "/custom/.gemini",
    "codebuddy": "/custom/.codebuddy",
    "cursor": "/custom/.cursor",
    "cursor_project_roots": [
      "/path/to/appA",
      "/path/to/appB"
    ],
    "cline": "/custom/.cline",
    "continue": "/custom/.continue",
    "qwen": "/custom/.qwen",
    "xcode_coding_assistant": "~/Library/Developer/Xcode/CodingAssistant"
  }
}
```

- 键名与平台一致；留空字符串 `""` 或删除该键即回退默认路径。
- 设置后，该平台的所有派生路径（配置、settings、skills、MCP 文件等）都会基于覆盖值解析。
- `cursor_project_roots` 是额外的 Cursor 项目根列表，用于同步项目内 `.cursor/rules/*.mdc`；也可用 `CURSOR_PROJECT_ROOTS="/path/a:/path/b"` 临时覆盖。
- Codex 仍优先使用标准环境变量 `CODEX_HOME` / `CODEX_CONFIG`，其次才是此处覆盖。
- `paths` 不是密钥，放在 `env/config.json`（gitignored 的本地配置），不会参与 `${...}` 占位符注入，仅用于路径解析。

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

新增或调整平台 API 同步前，先阅读
[Platform Sync Contract](../docs/platform-sync-contract.md)。Claude 的当前配置是后续平台的参考样例：
只同步 API / MCP / preamble 所属字段，保留目标配置中的其它用户字段，并用
`api.enabled` 控制 API 字段写入与清理。

详见 [sync/README.md](../sync/README.md)。
