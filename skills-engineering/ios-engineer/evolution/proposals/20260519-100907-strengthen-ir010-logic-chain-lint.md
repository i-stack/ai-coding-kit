# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260519-100907-strengthen-ir010-logic-chain-lint
- Created At: 2026-05-19 10:09:07 +0800
- Active Version At Creation: v67

## 问题信号
- IR-010 原 lint 只检查层级词和少量推理词，容易被“事实/证据/因为所以”等空泛锚点满足。
- 这种校验只能发现完全漏写，不能约束回复把关键结论、上游证据、结论强度和可证伪缺口放到同一个可审计对象里。

## 变更类型
- 修正表达

## 变更内容
- 修改文件：
  - `SKILL.md`：要求高风险判断或 usage-audit 声明命中 IR-010 时输出独立“逻辑链”块。
  - `references/logical_reasoning.md`：新增“逻辑链输出块”规范，固定字段为事实/证据、推断、结论强度、可证伪/缺口。
  - `references/rule_index.md`：同步 IR-010 摘要和共享概念索引，明确机械校验边界。
  - `scripts/lint_hit_rules.sh`：IR-010 改为检查独立“逻辑链”块、四字段和推理/不确定性标记。
- 替代或合并旧规则：无。

## 预期收益
- 让 IR-010 从弱关键词锚点升级为最低可审计输出契约。
- 降低“看起来有逻辑但缺少证据链、结论强度和可证伪缺口”的漏检概率。

## 验证
- 结构校验：`bash scripts/validate_rule_ids.sh` 通过；`SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 通过；`git diff --check` 通过。
- 场景回放：IR-010 weak smoke 失败，strong smoke 通过；内置 behavior validation 通过。
- 残留风险：机械校验仍不能证明推理为真，只能保证最低可审计结构存在；真正质量仍需人工或独立模型复审。

## 状态
- promoted
