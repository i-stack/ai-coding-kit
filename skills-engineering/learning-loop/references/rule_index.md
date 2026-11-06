<!-- last-verified: 2026-11 -->
# 规则真值索引（learning-loop）

> 本文件是 `learning-loop` skill 规则 ID 的元数据真值索引（条文真值在 `learning_loop.md`）。
> 字段语义见 `cognitive-reasoning/references/rule_index.md`。

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| LL-001 | learning-loop | global | timing | 500 | [] | [] | {} |
| LL-002 | learning-loop | global | structure | 500 | [] | [] | {} |
| LL-003 | learning-loop | global | structure | 500 | [] | [] | {} |
| LL-004 | learning-loop | global | structure | 500 | [] | [] | {} |
| LL-005 | learning-loop | global | evidence | 500 | [] | [] | {} |
| LL-006 | learning-loop | global | evidence | 500 | [] | [] | {} |
| LL-007 | learning-loop | global | safety | 500 | [] | [] | {} |
| LL-008 | learning-loop | global | evidence | 500 | [] | [] | {} |

## 使用规则

- ID 格式 `^[A-Z]+-\d{3}$`；前缀 `LL-` 专用于 learning-loop，不与 `PG-` / `GR-` / `HR-` / `POPT-` 冲突。
- 编号可有空洞，无强制连续约束；新增条目用前缀内最大编号 +1。
- ID 发布后不复用；退役条目保留在退役记录节并标 `retired`。
- 条文定义锚点为 `learning_loop.md` 中的 `## LL-NNN` 标题；`validate-skill-behavior.sh` 断言 SKILL.md 声明与 references 定义双向一致。

## 退役记录

| ID | Status | 退役原因 | 替代 ID |
|----|--------|----------|---------|
| （暂无） | | | |
