# cross-model-review 范围外

本 skill 负责**已锁定计划的跨模型对抗审查**，不负责盘问锁定、问题审查、代码审查、计划执行。

## 不处理的内容

- **计划锁定**：盘问用户锁定 PLAN.md 是 `plan-grill`（PG-001~004）的职责。cross-model-review 只审查已锁定的 PLAN.md。
- **问题审查**：问题本身的逻辑有效性、真实需求拆解由 `problem-analysis`（PA-001~003）负责，先于 plan-grill。
- **已写代码的审查**：审查已实现的代码（而非计划）由 `ios-engineer/references/review_checklists.md` 处理。本 skill 只审查 PLAN.md。
- **计划执行**：cross-model-review 只审查，不实施。实施由后续对话或 ios-engineer skill 承接。两幕期间不写任何代码。
- **单模型审查**：本 skill 必须跨 provider。同 provider 审查（如 Claude 审 Claude 的计划）失去对抗价值，不予执行。

## 触发门控

仅在 PLAN.md 已存在时触发。若无 PLAN.md，先加载 plan-grill。
