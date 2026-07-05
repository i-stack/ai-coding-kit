# skills-engineering — 给人类的上下文

## 这是什么？

`skills-engineering` 是一个**受控工程规则平台**，通过 Skill（技能）形式向 AI Agent（Claude Code、Codex、Cursor、Gemini、Xcode）提供领域工程指导和纪律约束。

它与 mattpocock/skills 不同——这里是"受控治理"，不是"技能市场"。

## 快速开始

### 1. 查看所有 Skill

```bash
bash scripts/list-skills.sh
```

### 2. 同步到本地 Agent

```bash
bash scripts/sync-skills.sh
```

### 3. 验证同步完整性

```bash
bash scripts/verify-sync.sh
```

## Skill 分类

| Skill | 类型 | 说明 |
|-------|------|------|
| `ios-engineer` | 领域 | iOS/Swift/SwiftUI 工程全流程 |
| `engineering-discipline` | 纪律 | 安全合规、最小修复、防 Diff 噪声 |
| `epistemic-integrity` | 纪律 | 真值接地——不编造、不伪装确定 |
| `logical-reasoning` | 纪律 | 论证链可追溯、因果克制 |
| `problem-analysis` | 前置 | 问题分析——充分理解后再行动 |
| `cognitive-expansion` | 认知 | 打破知识茧房、邻域启发 |

## 治理模型

- **规则 ID 体系**：IR/SYM/ROUTE/OUT/GR/PA 分类标识
- **受控演进**：规则变更需绑定治理记录
- **Usage Ledger**：使用观测与效果评估
- **ROUTE 定向**：症状 → 路由 → 按需加载

## 关键文件

| 文件 | 用途 |
|------|------|
| `*/SKILL.md` | Skill 主入口 |
| `*/AGENT-BRIEF.md` | Agent 快速决策参考 |
| `*/OUT-OF-SCOPE.md` | 职责范围外声明 |
| `*/references/` | 详细规则文档 |
| `scripts/` | 同步/校验/工具脚本 |
| `docs/` | 使用文档 |
| `.claude-plugin/` | Claude Code 插件配置 |
| `.agents/` | Agent 调用规范 |
| `.out-of-scope/` | 仓库级约束 |
