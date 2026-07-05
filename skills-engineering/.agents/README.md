# Agent 调用指南

本目录包含 Agent 调用相关的全局指令。

## 文件说明

- `invocation.md`：Agent 调用规范——如何正确加载和执行 skill
- `writing-docs.md`：为 skills-engineering 贡献文档的写作规范

## Skill 加载优先级

各 skill 目录下的 `AGENT-BRIEF.md` 提供快速决策参考，`SKILL.md` 提供完整执行细则。
Agent 应优先读 `AGENT-BRIEF.md` 判断是否加载该 skill，确认命中后完整读取 `SKILL.md` 和对应 `references/` 文件。
