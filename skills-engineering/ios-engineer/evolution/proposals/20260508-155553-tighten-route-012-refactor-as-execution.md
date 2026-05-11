# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-155553-tighten-route-012-refactor-as-execution
- Created At: 2026-05-08 15:55:53 +0800
- Active Version At Creation: v50

## 问题信号
- v47 SKILL.md 审查发现 [ROUTE-003] 和 [ROUTE-012] 关键词「重构」重叠：
  - ROUTE-003 主读 architecture_analysis.md，关键词含"**重构路线图**"（规划层 / 分析阶段）
  - ROUTE-012 主读 migration_strategy.md，关键词首位"**重构**"（执行层）
- 用户只说"重构"会落 ROUTE-012；加"路线图"才落 ROUTE-003。临界输入如"我想重构一下老代码"会优先命中 ROUTE-012 的执行路线，但用户可能只想要规划/分析层的建议。自进化触发信号「表达不清导致执行结果偏移」。
- 语义梳理：
  - "重构路线图" = 分析 + 规划 = 架构分析剧本的一部分（ROUTE-003）
  - "**重构落地**" = 拿着路线图执行代码重写 = 迁移策略的具体步骤（ROUTE-012）
  - 用"重构落地"替换"重构"后，ROUTE-012 聚焦执行语义，和 ROUTE-003 的规划语义分层更清。

## 变更类型
- 修正表达（保留 ROUTE-003、ROUTE-012 两个 ID，不退役、不替代；只把 ROUTE-012 的首关键词"重构"改为"重构落地"；ROUTE-003 不动）

## 变更内容
- 修改文件：
  - `SKILL.md` 第 46 行：[ROUTE-012] 关键词列表首位"重构"改为"重构落地"；其它关键词（迁移 / 灰度 / 回滚）和主读 / 追加 ref 不变。
  - `references/rule_index.md` 第 56 行：ROUTE-012 摘要同步改为"重构落地 / 迁移 / 灰度 / 回滚 → migration_strategy.md"。
- 不修改：
  - [ROUTE-003]：含"重构路线图"不动；它继续承担"分析 + 规划"层。
  - migration_strategy.md：ref 内容不动。
  - 其它 ROUTE / IR / OUT 规则。
- 替代或合并旧规则：无（ROUTE-012 ID 沿用）

## 预期收益
- "重构"（规划 vs 执行）的语义二义在 SKILL.md 关键词层被消解：用户想规划时说"重构路线图"命中 ROUTE-003，想落地执行时说"重构落地 / 迁移 / 灰度"命中 ROUTE-012。
- 用户只说"重构"时的单词命中不再优先落到 ROUTE-012 的执行分支；这在实际使用中更符合"先规划后执行"的工作流。代价：若用户确实只想要执行层建议，需要加"落地 / 实施 / 执行"修饰才能命中 ROUTE-012——这是设计意图。
- SKILL.md 与 rule_index.md 行数不变。

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` 保持通过（ID 不动，仅关键词文字替换）。
  - `SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh` 12 步全绿。
- 场景回放：
  - 6 个固定场景（layout / parameter-pass-through / concurrency / review / migration / mcp-control）里只有 migration 场景会涉及 ROUTE-012 领域；但 migration 场景的 expected_hits 不引用 ROUTE-012 的具体关键词（场景通过 rule_id 引用 ID 而非关键词原文）。预期全部 pass。
- 残留风险：
  - 若用户历史任务里仅用"重构"单词触发过 ROUTE-012，本提案后该单词不再命中 ROUTE-012 的首关键词，可能落到 ROUTE-003 的"重构路线图"前缀匹配。大多数情况下这反而更合适（先规划后执行），但会造成 usage_ledger 上的命中路径迁移。真实任务回放如果频繁出现"用户只想执行层建议但被带进架构分析剧本"，可再下沉。
  - ROUTE-017（复杂任务剧本）里仍包含"大型重构"关键词——那是剧本入口层，与 ROUTE-012 的"重构落地"不冲突（剧本先决定走不走剧本，再决定进哪条 ROUTE）。此处暂不动，待 F-5（ROUTE-017 入口条件收紧）处理。

## 状态
- promoted
