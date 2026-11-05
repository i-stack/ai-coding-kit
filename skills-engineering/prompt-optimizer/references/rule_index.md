<!-- last-verified: 2026-11 -->
# 规则 ID 索引（prompt-optimizer）

## 使用规则
- 本文件是 [SKILL.md](../SKILL.md) 内 `POPT-NNN` 规则的真值索引。新增 / 修改 / 退役 ID **先改本文，再同步 SKILL.md**。
- ID 格式：`^[A-Z]+-\d{3}$`，前缀 `POPT-` 专用于 prompt-optimizer（Prompt Optimizer）自有契约，不与 plan-grill 的 `PG-`、historical-recall 的 `HR-` 或全局 `GR-` 冲突。
- 编号可有空洞，无强制连续约束；新增条目用前缀内最大编号 +1。
- ID 一旦发布不复用：退役后保留在「退役记录」节，标 `retired` 并指明替代 ID；退役 ID 在 SKILL.md 中不应再出现。
- 行为门禁 `scripts/validate-skill-behavior.sh` 的 Check 2 会断言：SKILL.md 声明的每个 `POPT-NNN` 均在本文件以表格行 `| POPT-NNN |` 定义，且定义锚点须为标题 `## POPT-NNN` / 括号 `[POPT-NNN]` / 表格 `| POPT-NNN |` 之一；不一致即非零退出。

## Prompt Optimizer 规则 POPT-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| POPT-001 | active | 触发门控：仅主动触发（@prompt-optimizer 或「帮我优化提问」「优化这个 prompt」「改写我的问题」），不做「发送时自动拦截」 | `## 六条核心规则` |
| POPT-002 | active | 历史召回：改写前 recall 相似历史；历史澄清结论仅作待验证线索（HR-004），据此跳过盘问须标注「未澄清假设（来源：历史线索）」 | 同上 |
| POPT-003 | active | 盘问判定与澄清：复用 plan-grill PG-000 门控 + PG-001~PG-003（仅 interview，不产出 PLAN.md）；第②项按逐字段替换测试判定，判否则标「未澄清假设」 | 同上 |
| POPT-004 | active | 改写：把原始提问重写为结构化高质量提示词，满足四字段与改写验收判据（对象/事实前提不变、指代具体化、假设显式标注） | 同上 |
| POPT-005 | active | 透明确认与回答：展示优化稿并以「请确认或修正以上优化稿；确认前不回答原问题。」收尾；确认前不回答，确认后基于确认版回答；用户显式跳过确认时仍先展示、标注「未确认假设」后作答，改写改变对象或事实前提时硬否决 | 同上 |
| POPT-006 | active | 回写闭环：归档 QUESTION.md / CLARIFICATION.md / OPTIMIZED.md 到 .plan-reviews/<date-slug>/（PROMPT-OPTIMIZATION.md 仅存一行标题；OPTIMIZED.md 容纳确认版 / 修正版 / 豁免确认版）并 sync 回灌知识库 | 同上 |

## 退役记录

| ID | Status | 退役原因 | 替代 ID |
|----|--------|----------|---------|
| （暂无） | | | |
