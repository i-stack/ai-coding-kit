<!-- last-verified: 2026-08 -->
# 规则真值索引（epistemic-integrity）

> 本文件是 `epistemic-integrity` skill 规则 ID 的**元数据真值索引**（条文真值在 `epistemic_integrity.md`）。
> 字段见 `cognitive-calibration/references/rule_index.md` 说明。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| GR-011 | epistemic-integrity | global | evidence | 400 | [engineering-discipline.GR-004] | engineering-discipline.GR-008.residual | {confidence: epistemic-integrity, version_premise: epistemic-integrity} |
| GR-012 | epistemic-integrity | global | evidence | 400 | [] | [] | {confidence: epistemic-integrity} |
| GR-013 | epistemic-integrity | global | evidence | 400 | [] | [] | {confidence: epistemic-integrity} |

## 裁决优先级（机器可解析）

- `phase=evidence` 且 `precedence=400` > `engineering-discipline` 的 `phase=structure`(300)：即"真相 > 结构"（composition.md §3.1）。
- `field_owner.confidence` 恒归 epistemic-integrity，任何合并块不得覆盖。
