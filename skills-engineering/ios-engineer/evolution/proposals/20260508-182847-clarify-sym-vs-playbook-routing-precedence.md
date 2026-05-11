# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-182847-clarify-sym-vs-playbook-routing-precedence
- Created At: 2026-05-08 18:28:47 +0800
- Active Version At Creation: v56

## 问题信号
- 用户描述"反复偶现 Crash"时，SYM-001 → root_cause_enforcement.md 与 ROUTE-017 → execution_playbooks.md "反复偶现 Crash 系统排查" 剧本两条入口都成立。
- SKILL.md "症状导航" 节首句仅说 "先按症状选入口；命中后再回到下方任务分流"，缺明确升级阈值。
- ROUTE-017 行内括号"需满足跨多日 / 跨多模块 / 已尝试常规排障无果 / 需要分阶段落地至少一项"易被忽略。

## 变更类型
- 修正表达（提升升级判据可见度，不改 ID 集合）

## 变更内容
- 修改文件：SKILL.md
- 在 `## 任务分流` 段落首句之后、`### 症状导航` 之前，插入新子节 `### 路由优先级`：
  ```
  ### 路由优先级
  - 默认走 SYM 表 → 主读 ref 单点路由（最小心智成本）。
  - 升级到 ROUTE-017 剧本必须显式满足以下任一条件：跨多日 / 跨多模块 / 已尝试常规排障无果 / 需要分阶段落地。
  - 仅"问题复杂"或"涉及多个 ref"不算升级条件 — 多 ref 用 ROUTE 主读 + 追加机制覆盖即可。
  - 升级判据满足时，ROUTE-017 取代 SYM 主读，但 SYM 表仍作症状定位辅助。
  ```
- 同步收紧 ROUTE-017 行：把行内"（需满足... 至少一项才走剧本；否则走 SYM 与 ROUTE 单点路由）"括号删除，改为"升级判据见 `### 路由优先级`"。
- 修改文件：references/rule_index.md
- ROUTE-017 摘要列从"复杂任务剧本 → execution_playbooks.md"改为"复杂任务剧本（升级判据见 SKILL.md 路由优先级）→ execution_playbooks.md"。
- 替代或合并旧规则：无；ROUTE-017 既有"至少一项"表述被提升到独立子节并去重。

## 预期收益
- 偶现 Crash / 性能问题等高频场景的入口选择不再依赖隐性判断。
- ROUTE-017 行长度缩短，行内冗余条件移除，只保留指向。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh。
- 场景回放：场景 3（concurrency）/ 场景 6（mcp-control）— 两场景都应路由到 SYM 而非剧本。
- 残留风险：新子节增加 SKILL.md 行数（约 +6 行）；当前 SKILL.md 61 行，加后 ≈67 行，仍在合理范围。

## 状态
- promoted
