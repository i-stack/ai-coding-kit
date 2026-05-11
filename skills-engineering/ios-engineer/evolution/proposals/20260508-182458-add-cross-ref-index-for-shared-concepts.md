# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-182458-add-cross-ref-index-for-shared-concepts
- Created At: 2026-05-08 18:24:58 +0800
- Active Version At Creation: v54

## 问题信号
- self_evolution.md L72 已警示「跨文件共享概念改动需 grep 全量位置覆盖」，但全仓未给出真值索引；提案作者只能临时 grep 拼凑列表，易漏。
- 架构审计回放发现：IR-004 例外（findings-first）实际散落 5 处（SKILL.md IR-004 / SKILL.md OUT-002 / review_checklists.md §8 / examples.md §3 / migration_strategy.md L114），改 owner 时无清单可对账。

## 变更类型
- 新增能力（doc 层增设跨文件共享概念真值索引；不动 ID 集合，不引入新规则编号）

## 变更内容
- 修改文件：references/rule_index.md
- 在「退役记录」节后追加新章节「跨文件共享概念索引」，4 列表格：`概念 | Owner 位置 | 引用位置 | 修改协议`。
- 索引条目（已 grep 验证）：
  - 四段式输出：Owner = SKILL.md IR-004；引用 = examples.md §1/2/4/5/6、decision_records.md L5、test_execution_and_repair.md L82、validation_scenarios.md L26/L88、migration_strategy.md（剧本产物）。
  - findings-first 骨架：Owner = review_checklists.md §8；引用 = SKILL.md IR-004、SKILL.md OUT-002、examples.md §3、migration_strategy.md L114。
  - 参数透传与数据来源：Owner = architecture_and_network.md "参数透传与数据来源" 节；引用 = SKILL.md ROUTE-002、review_checklists.md §1 / §2、validation_scenarios.md 场景 2。
  - 任务分流主关键词集：Owner = SKILL.md ROUTE 表；引用 = rule_index.md ROUTE 摘要列。
- 修改协议每条标注："改 owner 时必须同步全部引用位置；改引用位置不动 owner 视为局部澄清。"
- 替代或合并旧规则：无；本提案不动既有规则，仅追加索引以兑现 self_evolution.md L72 的执行细则。

## 预期收益
- self_evolution.md L72 警示从口头约定升级为可对账表格。
- 后续提案做"跨文件共享概念"改动时，先查本表覆盖位置，避免 dead reference / 单点遗漏。
- 减少 grep 重复劳动，缩短 Step 4 验证时间。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh（12 步）+ scripts/validate_rule_ids.sh（双向断言 ID 一致）。
- 场景回放：6 场景结构校验；本提案不改输出行为，无场景级回归预期。
- 残留风险：索引表本身需后续提案维护——若新增 owner 文件未补入本表，约束失效。建议将"修改 SKILL.md / references 中带跨文件引用的概念前必须查本表"补入 self_evolution.md "明确禁止的模式"，留作后续提案。

## 状态
- promoted
