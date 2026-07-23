# optional_mcps — 可选 MCP 服务器目录

对齐 Hermes Agent 的 `optional_mcps/` 思路：把**非默认、社区/高级**的 MCP 服务器与开箱即用的 `env/mcp/` 集合分开，避免污染默认配置，同时保留「一键启用」能力。

## 工作机制

- `env/optional_mcps/*.json`：可选的 MCP 服务器定义（**不**自动同步）。
- `sync/scripts/optional_mcps.sh enable <name>`：把定义复制到 `env/mcp/<name>.json`，由于 `env/mcp/*.json` 会被 `sync.sh` 自动发现，下一次 `sync.sh` 即生效。
- `sync/scripts/optional_mcps.sh disable <name>`：从 `env/mcp/` 移除并停止同步。
- 启用状态记录在 `env/optional_mcps/enabled.json`（本地状态，**不提交**，已加入 `.gitignore`；脚本缺失时自动重建为 `{}`）。

## 用法

```bash
# 列出所有可选服务器及其启用状态
bash sync/scripts/optional_mcps.sh list

# 启用一个
bash sync/scripts/optional_mcps.sh enable puppeteer

# 禁用一个
bash sync/scripts/optional_mcps.sh disable puppeteer

# 启用后照常同步
bash sync.sh
```

## 新增一个可选服务器

1. 在 `env/optional_mcps/` 放 `<name>.json`（格式同 `env/mcp/*.json`，敏感值用 `${...}` 占位）。
2. 若需要 secret，在 `env/secrets.json.example` 增加对应字段说明，并提醒用户填写 `env/secrets.json`。
3. 运行 `bash sync/scripts/optional_mcps.sh enable <name>`。

## 示例

| 服务器 | 说明 | 需要 secret |
|--------|------|-------------|
| `puppeteer` | 浏览器自动化（与默认 `playwright` 互补，择一启用） | 否 |
| `filesystem-extra` | 扩展文件系统访问 | 是（`filesystem_extra.root`） |
| `wechat-bridge` | 微信桥接（演示） | 是（`wechat.token`） |
