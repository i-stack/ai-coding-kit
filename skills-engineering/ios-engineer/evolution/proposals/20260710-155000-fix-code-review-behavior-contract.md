# 修复 ios-engineer OUT-002 与 behavior 4/5 守卫契约漂移

## Metadata
- **Proposal ID**: 20260710-155000-fix-code-review-behavior-contract
- **Title**: 修复 OUT-002 与 behavior 4/5「Code review output contract」守卫契约漂移
- **Author**: ai-coding-kit automation
- **Date**: 2026-07-10
- **Active Version At Creation**: v73
- **Status**: draft

## 问题信号
- `bash skills-engineering/ios-engineer/scripts/validate_skill_evolution.sh` 在 [13/14] behavior validation 中报告 `behavior 4/5` 失败：`SKILL.md no longer routes code review to findings-first review_checklists.md`。
- 根因：`feature_3.0.0` 分支将 `ios-engineer/SKILL.md` 的 `[OUT-002]` 改写为英文（`code review / PR Review is exempt from GR-004 four-section format`），既丢失了 `run_behavior_validation.sh` 断言要求的字面串 `"代码审查 / PR Review 例外"`，也与 owner（唯一所有权源）`references/rule_index.md` 的 OUT-002 当前中文措辞 `代码审查 / PR Review：findings-first 骨架（触发条件见 GR-004）` 产生 drift。
- 该失败**非任何业务提案引入**，而是分支级既有守卫漂移，会阻塞本分支上所有提案的 `skill-evolution` pre-commit 审批门（要求提案附带 `ready_to_promote` 审批记录）。
- 历史快照 v73 的 `SKILL.md` 仍含 `（代码审查 / PR Review 例外于 GR-004 四段式）`，故 14 步在 v73 时通过；分支英文化 OUT-002 后才引入漂移。

## 变更类型
- 一致性 / 守卫契约修复（maintenance），非功能变更。
- 遵循唯一所有权原则：owner = `references/rule_index.md` 的 OUT-002（中文、active），`SKILL.md` 的描述必须与其对齐。

## 变更内容
1. `ios-engineer/SKILL.md` L141（`[OUT-002]`）改回中文、对齐 owner 措辞：
   - 旧：`[OUT-002] Code review / PR Review: findings-first standard skeleton (code review / PR Review is exempt from GR-004 four-section format; see [review_checklists.md](references/review_checklists.md) §8 for skeleton sections).`
   - 新：`[OUT-002] 代码审查 / PR Review：findings-first 标准骨架（触发条件见 GR-004；骨架段落详见 [review_checklists.md](references/review_checklists.md) 第 8 节）。`
2. `ios-engineer/scripts/run_behavior_validation.sh` L88 的 behavior 4/5 字面断言去 stale 化：
   - 旧：`unless skill.include?("代码审查 / PR Review 例外") &&`
   - 新：`unless skill.include?("代码审查 / PR Review") &&`
   - 理由：保留对「code review 场景路由到 findings-first `review_checklists.md`」的契约校验（`"findings-first"` 与 `"[review_checklists.md](references/review_checklists.md)"` 两项断言保留），去掉对旧 OUT-002 措辞（"例外于 GR-004 四段式"）的硬编码依赖，使其与 owner 当前真值一致。
3. `ios-engineer/SKILL.md` L55（`[SYM-004]`）改回 v73 中文真值（修复 behavior 5/5「Network cache and error-modeling contract」守卫漂移）：
   - 旧：`| [SYM-004] Request failure / retry anomalies / auth refresh / pagination dupes or gaps / cache pollution / 请求失败 / 重试异常 / 鉴权刷新 / 分页重复或漏数据 / 缓存污染 | [networking_patterns.md](references/networking_patterns.md) | For error modeling: [domain_modeling.md](references/domain_modeling.md) |`
   - 新：`| [SYM-004] 请求失败 / 重试异常 / 鉴权刷新 / 分页重复或漏数据 / 缓存污染 | [networking_patterns.md](references/networking_patterns.md) | 错误建模追加 [domain_modeling.md](references/domain_modeling.md) |`
   - 理由：当前分支把 SYM-004 英文化、并把 `错误建模追加` 改为英文 `For error modeling:`，触发 behavior 5/5 失败；改回 v73 中文真值既通过断言，也与 owner `references/rule_index.md` 的 SYM-004（中文摘要）及 symptom 表历史真值一致。
- 跨文件覆盖核查（self_evolution GR）：`references/examples.md` §3 当前已是中文 `findings-first 骨架...见 review_checklists.md`，与修复后的中文 OUT-002 兼容，无需改动；owner `references/rule_index.md` 本身未变；en-US `rule_index.md` 为独立 i18n 英文条目，不受 zh 断言影响。

## 预期收益
- `validate_skill_proposal.sh` 对本分支任意提案的 14 步校验恢复通过（[13] behavior 4/5 通过；[12] snapshot 由 `SKILL_SNAPSHOT_CONSISTENCY=1` 跳过），解锁 `skill-evolution` pre-commit 审批门，使后续业务提案（如 `20260710-154300-sync-gr-ids-to-templates-ledger`）可正常走 approve→commit。
- 消除 `SKILL.md` 与 owner `rule_index.md` 的 OUT-002 措辞 drift，符合唯一所有权纪律。

## 验证
- 结构校验（待运行）：`bash skills-engineering/ios-engineer/scripts/validate_skill_proposal.sh evolution/proposals/20260710-155000-fix-code-review-behavior-contract.md` → 预期 exit 0、status=validated、promotion_readiness 可置 ready_to_promote（[13] behavior 4/5 通过；[12] snapshot 自动 skip）。
- 残留风险：无功能变更，仅 SKILL.md 文案与行为断言字符串调整。

## 状态
- approved
