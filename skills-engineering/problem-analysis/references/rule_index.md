<!-- last-verified: 2026-09 -->
# 规则真值索引（problem-analysis）

> 本文件是 `problem-analysis` skill 规则 ID 的**元数据真值索引**（条文真值在 `problem_analysis.md`）。
> 目的：让 `.agents/composition.md` 的冲突裁决可解析 `问题分析` 块的独立保留。
> 字段见 `cognitive-reasoning/references/rule_index.md` 说明。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| PA-001 | problem-analysis | global | evidence | 400 | [] | [] | {} |
| PA-002 | problem-analysis | global | evidence | 400 | [] | [] | {} |
| PA-003 | problem-analysis | global | timing | 400 | [] | [] | {logic: problem-analysis, requirement: problem-analysis, path: problem-analysis} |

## 字段级去重

- `问题分析` 块谈输入（问题本身），位置在正式回复之前，**不并入** `逻辑链` / `验证锚点` / 四段式。
- 字段 owner 不变：`逻辑检验` / `真实需求` / `路径评估` 归 problem-analysis。
