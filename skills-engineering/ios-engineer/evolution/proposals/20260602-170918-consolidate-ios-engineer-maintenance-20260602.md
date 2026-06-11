# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260602-170918-consolidate-ios-engineer-maintenance-20260602
- Created At: 2026-06-02 17:09:18 +0800
- Active Version At Creation: v70

## 问题信号
- 2026-06-02 横向审计发现 ios-engineer active ref 中存在 deprecated ID 残留、rule_index.md 摘要列散文引用旧 ID、lint_hit_rules.sh 与 rule_index.md 的 SIGNALS 字符锚点不一致。
- architecture_and_network.md / networking_patterns.md / domain_modeling.md 对部分反模式重复定义，增加上下文膨胀与 owner 漂移风险。
- layout_and_ui.md 保留项目特定聊天列表置顶模板，不适合作为通用 iOS skill ref。

## 变更类型
- 修正表达 / 合并重复 / 退役规则

## 变更内容
- 修改文件：
  - SKILL.md
  - references/rule_index.md
  - references/architecture_and_network.md
  - references/networking_patterns.md
  - references/domain_modeling.md
  - references/decision_records.md
  - references/examples.md
  - references/code_templates.md
  - references/review_checklists.md
  - references/validation_scenarios.md
  - references/root_cause_enforcement.md
  - references/usage_ledger.md
  - references/layout_and_ui.md
  - scripts/lint_hit_rules.sh
  - MAINTENANCE-LOG-2026-06-02.md
- 替代或合并旧规则：
  - 删除 active rule_index.md 中 IR-002/003/004/005/007/008/010 deprecated 行及对应委托 SIGNALS，当前引用统一落到 GR-002/003/004/005/007/008/010。
  - OUT-002 摘要列从旧 IR-004 改为 GR-004；GR-010 SIGNALS 引用统一为 ASCII quotes。
  - NetworkManager 与 localizedDescription 反模式定义收口到 anti_patterns.md §1 / §4，其它 ref 只保留跳转。
  - 移除 layout_and_ui.md 中项目特定 UITableView 聊天置顶模板。

## 预期收益
- 减少 deprecated ID 在 active 文档中的误导，避免 usage-audit 与 lint 命中旧规则。
- 明确反模式 owner，降低多文件重复定义导致的漂移。
- 保持 ios-engineer 通用性，避免项目内业务模板污染通用 UI 布局 ref。

## 验证
- 结构校验：
  - bash scripts/validate_rule_ids.sh 通过。
  - bash scripts/validate_usage_ledger.sh 通过。
  - bash scripts/audit_ref_freshness.sh 通过，28 个 ref 均 FRESH；本轮修改过的 ref 已更新 last-verified 到 2026-06。
  - SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_evolution.sh 通过。
  - bash scripts/validate_skill_evolution.sh 仅因 working tree 与 active snapshot v70 存在预期 drift 失败，正是本提案需要晋升的对象。
- 场景回放：
  - 基础行为验证随 SKIP_SNAPSHOT_CONSISTENCY=1 validate_skill_evolution.sh 执行并通过。
- 残留风险：
  - evolution 历史归档、active_version.json notes、usage.jsonl 历史观测保留旧 IR 字符串，按历史记录不追溯修改。
  - 删除 deprecated 行后，validate_rule_ids.sh 的 retired/deprecated 拦截集合只保留当前 rule_index.md 内的 retired ID；后续若要禁止旧 IR 字符串回流，需要单独扩展 lint。
  - 原聊天置顶模板不再保存在 ios-engineer skill 内；如项目仍需要，应迁移到项目级文档。

## 状态
- promoted
