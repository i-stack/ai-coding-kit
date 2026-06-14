# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260611-194725-update-mcp-config-source-path
- Created At: 2026-06-11 19:47:25 +0800
- Active Version At Creation: v73

## 问题信号
- 仓库 MCP 配置源已从根级 `mcp/servers.json` 收敛到单一 `env/config.json`，但 `references/mcp_control.md` 仍指向旧路径，导致工具来源说明与当前同步架构不一致。

## 变更类型
- 修正表达

## 变更内容
- 修改文件：`references/mcp_control.md`
- 替代或合并旧规则：不改变 MCP 优先映射规则本身，仅将 MCP 同步来源描述从 `mcp/servers.json` / `mcp/` 修正为 `env/config.json` / `env/`。

## 预期收益
- iOS 工程任务中关于 MCP 工具来源的说明与当前仓库结构一致，避免后续维护者按已删除的根级 `mcp/` 配置目录排查。

## 验证
- 结构校验：运行 `validate_skill_proposal.sh`，确保 skill 结构、引用、rule id、usage ledger 与行为校验仍通过。
- 场景回放：以 `mcp-control` 场景确认本次仅修正文档路径，不改变 iOS 场景 MCP 优先级行为。
- 残留风险：历史 snapshot 中可能仍保留旧路径作为历史记录；active reference 已修正。

## 状态
- approved
