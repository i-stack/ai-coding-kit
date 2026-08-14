# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260814-140000-usage-ledger-task-id-evidence-class
- Created At: 2026-08-14 14:00:00 +0800
- Active Version At Creation: v73

## 问题信号
- 第四阶段「可观测性闭环」要求把 usage audit 与任务结果关联，回答：哪条规则常命中 / 误触发 / 只增格式不提升成功率 / 哪个模型版本遵循最差。
- 既有 `usage_ledger.md` 仅有 `session_id` 关联键，缺「同一真实任务的稳定关联键」（`task_id`），导致独立复验与原始任务无法对齐；且汇总口径未声明证据分级，易把模型自评与独立复验混为同一证据强度。

## 变更类型
- 修正表达 / 新增字段（在 references/usage_ledger.md 增加 `task_id` schema 字段与证据分级汇总说明；属第四阶段可观测性闭环的一部分）。

## 变更内容
- 修改文件：`skills-engineering/ios-engineer/references/usage_ledger.md`
  - 用途段：明确汇总按工具、任务类型、规则、证据等级分别报告，避免模型自评与独立复验混为同一证据强度。
  - Schema 示例与字段表：新增 `task_id`（string | null，否）作为同一真实任务的稳定关联键，独立复验与原始任务使用相同值。
- 不替代或合并任何既有 GR 规则；`SKILL.md`、rule ID 未变动。
- 配套脚本（`summarize_usage_ledger.sh` 的 by_evidence_class / linked_tasks 聚合、`validate_usage_ledger.sh` 的 task_link_coverage）在同轮提交中同步落地。

## 预期收益
- 使 usage audit 能按 `task_id` 将原始任务与独立复验对齐，支撑第四阶段 4 个核心问题的可查询闭环。
- 证据分级汇总避免自评偏差污染成功率统计。

## 验证
- 结构校验：纯 references schema 文本澄清 + 新增字段说明，不触碰 SKILL.md body 行为契约字面串；`validate_usage_ledger.sh` 对 `task_id`/`evidence_class` 字段无破坏。
- 场景回放：不适用（无行为契约字面串变更）。
- 残留风险：无（仅新增可选字段与汇总口径说明，向后兼容已有 usage.jsonl 条目 `task_id=null`）。

## 状态
- approved
