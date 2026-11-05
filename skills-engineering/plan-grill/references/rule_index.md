<!-- last-verified: 2026-11 -->
# 规则 ID 索引（plan-grill）

## 使用规则
- 本文件是 [SKILL.md](../SKILL.md) 内 `PG-NNN` 规则的真值索引。新增 / 修改 / 退役 ID **先改本文，再同步 SKILL.md**。
- ID 格式：`^[A-Z]+-\d{3}$`，前缀 `PG-` 专用于 plan-grill（Plan Grill）自有契约，不与 ios-engineer 的 `IR-/SYM-/ROUTE-/OUT-`、全局 `GR-` 或 historical-recall 的 `HR-` 冲突。
- 编号可有空洞，无强制连续约束；新增条目用前缀内最大编号 +1。
- ID 一旦发布不复用：退役后保留在「退役记录」节，标 `retired` 并指明替代 ID；退役 ID 在 SKILL.md 中不应再出现。
- 行为门禁 `scripts/validate-skill-behavior.sh` 的 Check 2 会断言：SKILL.md 声明的每个 `PG-NNN` 均在本文件以表格行 `| PG-NNN |` 定义，且定义锚点须为标题 `## PG-NNN` / 括号 `[PG-NNN]` / 表格 `| PG-NNN |` 之一；不一致即非零退出。

## Plan Grill 规则 PG-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| PG-000 | active | 需求清晰度门控：仅当阻塞性决策无法从代码或上下文查明、且不同答案会实质改变交付结果时自动进入盘问 | `## 七条核心规则` |
| PG-001 | active | 逐一提问：一次只问一个问题，等用户回答后再继续 | 同上 |
| PG-002 | active | 给推荐答案：每个问题须给出推荐答案 + 一句理由 | 同上 |
| PG-003 | active | 遍历设计树：沿决策树按依赖顺序解决；能查代码的不问用户 | 同上 |
| PG-004 | active | 锁定产出：共识后写入工作区根 `.plan-reviews/<plan-slug>/PLAN.md` 并读回验证七段完整；确认前不执行 | 同上 |
| PG-005 | active | 架构分析委托：跨文件依赖且已加载平台 engineer 时，按该 skill 的快速架构分析模板填写 architecture-analysis.md | 同上 |
| PG-006 | active | 历史召回委托全局 historical-recall；本 skill 不内联调用；召回内容只作待验证线索 | 同上 |

## 退役记录

| ID | Status | 退役原因 | 替代 ID |
|----|--------|----------|---------|
| （暂无） | | | |
