# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-141100-bootstrap-rule-ids
- Created At: 2026-05-08 14:11:00 +0800
- Active Version At Creation: v43

## 问题信号
- Step 1（v43）落地了 evolution/scenarios/ 6 份 JSON 规格，但场景里的 `expected_hits.anchor` 仍是 `SKILL.md:13` 行号锚点——行号会随编辑漂移，且无法从 missed_rules 列表直接判断「漏的是哪条规则」。
- 后续 Step 3（usage ledger）需要把每次任务的 `expected_rules: [...]` / `hit_rules: [...]` 写成稳定 ID；当前 SKILL.md 没有 ID 体系。
- 用户在 SkillOps 闭环讨论中明确希望以「IR-001 / ROUTE-XXX」形式的 ID 作为命中率统计单位。

## 变更类型
- 新增能力（不退役、不替代任何旧规则；anchor 字段保留与 rule_id 并行）

## 变更内容
- 修改文件：
  - `SKILL.md`：为铁律 8 条、症状导航 7 行、任务分流 19 个 bullet、输出模板 6 个 bullet 共 40 条结构化规则前置 `[ID]` 标记（IR-001~008、SYM-001~007、ROUTE-001~019、OUT-001~006）
  - 新增 `references/rule_index.md`：40 条 ID 的真值索引（status / 摘要 / 锚点位置 / 退役记录）
  - 新增 `scripts/validate_rule_ids.sh`：双向一致性、ID 格式、唯一性、status 枚举、scenarios 引用合法性
  - 修改 `scripts/validate_scenario_specs.sh`：为 `expected_hits[].rule_id` / `failure_signals[].rule_id` 加可选字段校验（仅校验格式，ID 真实性由 validate_rule_ids.sh 负责）
  - 修改 `scripts/validate_skill_evolution.sh`：插入 `[7/11] Validate rule IDs` 步骤，原 [7-10] 顺延为 [8-11]
  - 修改 `evolution/scenarios/*.json` 6 份：把 `anchor: "SKILL.md:NN"` 翻译为 `rule_id: "IR-XXX"`；`anchor` 字段保留以兼容指向 references/*.md 的内容
  - 修改 `references/self_evolution.md`：新增「规则 ID 治理」章节，约束 ID 生命周期与 rule_index.md 一致性
  - 修改 `references/validation_scenarios.md`：追加一句允许 `rule_id` 字段
- 替代或合并旧规则：无；anchor 字段不废弃

## 预期收益
- 让 missed_rules / hit_rules 在 ledger 与 scenarios 中具备稳定身份证：行号漂移不再影响统计，跨提案命中率可比
- 以最小变动面铺开：SKILL.md 仅加前缀不动语义；rule_index.md 是新文件无破坏性；scripts 按现有 ruby-in-bash 风格新增 1 个、改 1 个；scenarios 字段平行追加
- 为 Step 3（usage ledger）提供 rule_id 词表；此后 ledger 的 `expected_rules` / `hit_rules` 字段直接用 IR-NNN / ROUTE-NNN

## 验证
- 结构校验：
  - `bash scripts/validate_rule_ids.sh` SKILL.md 与 rule_index.md 双向一致、scenarios 引用全部合法
  - `bash scripts/validate_scenario_specs.sh` 含 rule_id 字段后仍 6 specs 合法
  - `bash scripts/validate_skill_evolution.sh` 11 步全绿
  - 反向验证：故意把 rule_index.md 中 IR-008 改成 IR-099，应报双向不一致错；故意在场景 rule_id 填 IR-999，应报「未知 ID」错
- 场景回放：6 个固定场景人工自评分；本提案不增减场景，只验证 ID 加入未引入回归
- 残留风险：
  - references/*.md 内细粒度规则尚未 ID 化；如果 Step 3 ledger 显示 SKILL.md 级别 ID 不够细，再下沉
  - record_validation_scenario.sh 的 hits 字段仍是自由文本，未来 grader 接入时统一升级
  - evolution/scenarios/ 仍不在快照范围，drift 不会被 [9/11] 快照一致性捕获

## 状态
- promoted
