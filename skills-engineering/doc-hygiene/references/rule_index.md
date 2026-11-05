<!-- last-verified: 2026-08 -->
# 规则真值索引（doc-hygiene）

> 本文件是 `doc-hygiene` skill 规则 ID 的**元数据真值索引**（条文真值在 `doc_hygiene.md`）。
> 字段语义见 `cognitive-reasoning/references/rule_index.md`。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| DH-001 | doc-hygiene | global | structure | 500 | [] | [] | {} |
| DH-002 | doc-hygiene | global | structure | 500 | [] | [] | {} |
| DH-003 | doc-hygiene | global | structure | 500 | [] | [] | {} |

## 演进注意

- DH-* 前缀即表达 owner = doc-hygiene。
- 新增规则须在此登记；退役 ID 须同步删除 SKILL.md 内联引用（`validate-rule-ids.sh` 双向校验）。
