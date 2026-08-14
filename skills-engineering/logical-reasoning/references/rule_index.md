<!-- last-verified: 2026-08 -->
# 规则真值索引（logical-reasoning）

> 本文件是 `logical-reasoning` skill 规则 ID 的**元数据真值索引**（条文真值在 `logical_reasoning.md`）。
> 字段语义见 `cognitive-calibration/references/rule_index.md`。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| GR-010 | logical-reasoning | global | evidence | 300 | [] | engineering-discipline.GR-004.why | {confidence: epistemic-integrity, 逻辑链: logical-reasoning} |

## 字段级去重

- GR-010 的「逻辑链(可证伪/缺口)」可并入 engineering-discipline GR-004 的 `why` 段（不删字段，只合并块）。
- `field_owner.逻辑链` 恒归 logical-reasoning；`field_owner.confidence` 归 epistemic-integrity（见 epistemic-integrity rule_index GR-011）。
