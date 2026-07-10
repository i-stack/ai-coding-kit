# auto-code-review 范围外声明

本 skill **不处理**以下场景：

## 1. 计划审查

- 审查 PLAN.md 或实现方案 → 使用 `cross-model-review` skill。
- 本 skill 只审查**代码实现**，不审查计划文档。

## 2. 非代码变更

- 纯文档更新（.md 文件）
- 配置文件微调（单行修改）
- typo 修复、格式化调整
- 这些场景跳过自动审查。

## 3. 无代码变更的对话

- 纯问答、解释、建议类回复
- 未产生实际文件修改
- 这些场景不触发审查。

## 4. 未显式启动

- 普通代码生成、修改完成、测试通过都不触发本 skill。
- 只有 `/auto-review`、`使用 auto-code-review` 等明确请求才启动。
- `AUTO_REVIEW_ENABLED=true` 仅表示能力可用，不构成用户授权。

## 5. 跨模型审查的替代

- 本 skill 不替代 `cross-model-review` 的 PLAN.md 审查流程。
- 两者互补：cross-model-review 审查计划，auto-code-review 审查实现。
- 完整工作流：plan-grill → cross-model-review → 实施 → auto-code-review。

## 6. 人工审查的替代

- 本 skill 不替代人工代码审查。
- 审查结果仅供 agent 和用户参考，最终决策由用户做出。
- deadlock 时必须交用户裁决，不自动合并。

## 7. 未授权修复

- `/auto-review` 默认只读，不授权主 agent 修改代码。
- 只有 `/auto-review --fix` 或明确“审查并修复”才进入修复循环。

## 8. 非 CLI reviewer 场景

- 本 skill 依赖 CLI 工具（codex/gemini/claude）进行跨模型审查。
- 不支持通过 API 直接调用模型（除非通过 CLI 封装）。
- 不支持 GUI 工具或 Web 界面的 reviewer。
