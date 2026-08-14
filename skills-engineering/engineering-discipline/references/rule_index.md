<!-- last-verified: 2026-08 -->
# 规则真值索引（engineering-discipline）

> 本文件是 `engineering-discipline` skill 规则 ID 的**元数据真值索引**（条文真值在 `engineering_discipline.md`）。
> 目的：让 `.agents/composition.md` 的冲突裁决从"散文协议"升级为"机器可解析数据"。
> 字段见 `cognitive-reasoning/references/rule_index.md` 说明。
> `validate_rule_ids.sh` 校验 SKILL.md 声明 ID 与本文 active 行双向一致。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| GR-001 | engineering-discipline | global | safety | 900 | [] | [] | {} |
| GR-002 | engineering-discipline | global | timing | 300 | [] | [] | {} |
| GR-003 | engineering-discipline | global | evidence | 300 | [] | [] | {} |
| GR-004 | engineering-discipline | global | structure | 300 | [] | [] | {why: engineering-discipline, risk: engineering-discipline, covered: engineering-discipline} |
| GR-005 | engineering-discipline | global | structure | 300 | [] | [] | {} |
| GR-006 | engineering-discipline | global | structure | 300 | [] | [] | {} |
| GR-007 | engineering-discipline | global | structure | 300 | [] | [] | {} |
| GR-008 | engineering-discipline | global | structure | 300 | [] | [] | {covered: engineering-discipline, uncovered: engineering-discipline, residual: engineering-discipline} |

## 字段级去重（与 cognitive-reasoning）

- GR-010「逻辑链(可证伪/缺口)」可并入 GR-004 的 `why` 段（不删字段，只合并块）。
- GR-011「验证锚点(版本前提)」可并入 GR-008 的 `residual` 段。
- 合并时字段 owner 不变：confidence 归 cognitive-reasoning（GR-011~013），covered/uncovered/residual 归 engineering-discipline。
