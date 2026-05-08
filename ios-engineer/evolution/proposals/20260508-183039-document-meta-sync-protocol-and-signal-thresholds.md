# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-183039-document-meta-sync-protocol-and-signal-thresholds
- Created At: 2026-05-08 18:30:39 +0800
- Active Version At Creation: v57

## 问题信号
- validation_scenarios.md L8 仅说"先改 JSON，后同步本文"，缺改动核对清单 — 提案修改规则但漏改场景 expected_hits 易滑脱。
- usage_ledger.md 第 7 节告示 self-grading 偏差，但 summarize 阈值（MISSED_RULE_THRESHOLD=3 / TASK_TYPE_OTHER_THRESHOLD=5 / DEVIATION_THRESHOLD=2 / TOOL_DIVERGENCE_THRESHOLD=0.4）只在 scripts/summarize_usage_ledger.sh L69-L72 硬编码，文档无显式记录。

## 变更类型
- 新增能力（doc 层补齐元工程层四件套的执行细则；不改 ID 集合）

## 变更内容
- 修改文件：references/validation_scenarios.md
- 在 "## 使用规则" 节末追加执行步骤段，明确"改 JSON → 跑 validate_scenario_specs.sh → 同步本文场景描述 → 跑 validate_rule_ids.sh"四步顺序，并明确每步漏跑的失败现象。
- 修改文件：references/usage_ledger.md
- 在第 7 节后插入新第 8 节「提案候选信号阈值」，从 summarize 脚本 L69-L72 摘录 4 个常量并对应说明：
  - MISSED_RULE_THRESHOLD=3 → 候选"新增能力"提案信号
  - TASK_TYPE_OTHER_THRESHOLD=5 → 候选"新增 task_type"提案信号
  - DEVIATION_THRESHOLD=2 → 候选"修正表达"提案信号
  - TOOL_DIVERGENCE_THRESHOLD=0.4 → 候选"self-grading 偏差对比"提案信号
- 注明："阈值与 scripts/summarize_usage_ledger.sh L69-L72 一一对应；改文档同时改脚本，否则 summarize 输出与文档解释会漂移。"
- 原第 8 节「维护」顺延为第 9 节。
- 替代或合并旧规则：无；仅追加。

## 预期收益
- 元工程层四件套从隐式约定转为显式可执行步骤；新人接手提案不需读脚本源码就能理解阈值。
- 后续审计能直接查文档判断"为什么 summarize 没把这条 missed_rule 列为候选"。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 场景回放：6 场景结构校验；本提案不改 SKILL 输出行为。
- 残留风险：若后续 summarize 脚本阈值调整，文档可能漂移。建议把"脚本常量 ↔ 文档数字"的双向校验补到 validate_skill_evolution.sh，留作后续提案。

## 状态
- promoted
