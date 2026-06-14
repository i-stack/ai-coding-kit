# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-182705-add-out-subunit-mapping-table
- Created At: 2026-05-08 18:27:05 +0800
- Active Version At Creation: v55

## 问题信号
- OUT-003 → code_templates.md 内含 6 个独立模板（ViewModel / UseCase / Repository / APIClient / Coordinator / Actor），从 OUT-003 触发后无法反向定位到具体模板章节。
- ROUTE-017 → execution_playbooks.md 内含 5 条剧本，剧本无独立 ID。
- OUT-006 同时映射 testing_strategy.md + test_execution_and_repair.md，分工需读双文件首段才能区分。

## 变更类型
- 新增能力（doc 层增设 OUT 子单元映射；不引入新 ID 前缀，不动 validate_rule_ids.sh 维护面）

## 变更内容
- 修改文件：references/rule_index.md
- 在「输出模板 OUT-NNN」表后追加新章节「OUT 子单元映射」，4 列表格：`OUT-ID | 子单元名 | 文件锚点 | 适用场景一句话`。
- 索引条目：
  - OUT-003 → ViewModel / UseCase / Repository / APIClient / Coordinator / Actor 模板（6 项，对应 code_templates.md §1-§6）。
  - OUT-006 → 双文件分工：testing_strategy.md（测试分层与覆盖策略）+ test_execution_and_repair.md（测试执行与失败修复）。
  - ROUTE-017 → 接手遗留页面 / 反复偶现 Crash 系统排查 / 性能专项 / 并发架构迁移 / 大型重构落地（5 项，对应 execution_playbooks.md 同名章节）。
- 表头声明："本表是反向定位辅助，不替代 OUT-NNN ID 治理；新增模板 / 剧本时同步更新本表。"
- 替代或合并旧规则：无；仅追加 doc 层映射。

## 预期收益
- 反向维护时（如 ViewModel 模板需要调整），从 OUT-003 直接定位到 code_templates.md §1。
- 后续若 self_evolution.md 加"修改 H2 标题须同步本表"禁令，本表是落点。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh。
- 场景回放：6 场景结构校验；本提案不改输出行为。
- 残留风险：子单元名靠 ref 文件 H2 标题保持一致——若 H2 改名而本表未跟，索引失效；建议后续提案在 self_evolution.md "明确禁止的模式" 节追加禁令。

## 状态
- promoted
