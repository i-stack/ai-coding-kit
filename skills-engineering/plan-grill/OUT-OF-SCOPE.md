# plan-grill 范围外

本 skill 负责**实现方案的盘问与锁定**，不负责问题审查、代码审查、跨模型对抗。

## 不处理的内容

- **问题本身审查**：问题是否含逻辑错误、矛盾前提、真实需求拆解，由 `problem-analysis`（PA-001/002/003）负责。plan-grill 在 problem-analysis 完成后启动。
- **跨模型对抗审查**：PLAN.md 锁定后由已选 reviewer 对抗审查，是 `cross-model-review` 的职责。plan-grill 只产出 PLAN.md，不调用 reviewer。
- **已写代码的审查**：审查已实现的代码由 `ios-engineer/references/review_checklists.md` 或 `cross-model-review`（审查计划而非代码）处理。
- **执行计划**：plan-grill 只锁定计划，不执行。执行由后续对话或 ios-engineer skill 承接。

## 触发门控

仅在 problem-analysis 完成后触发。若问题本身未审查，先加载 problem-analysis。
