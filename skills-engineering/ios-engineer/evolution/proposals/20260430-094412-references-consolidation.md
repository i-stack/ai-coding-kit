# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-094412-references-consolidation
- Created At: 2026-04-30 09:44:12 +0800
- Active Version At Creation: v1

## 问题信号
- `references/refactoring_and_migration.md` 与 `references/migration_risk_control.md` 约 50% 内容重叠（阶段化迁移、兼容层、灰度回滚、验证策略、常见反模式），SKILL.md 中把两份都列为迁移场景规则导致上下文膨胀、优先级不清。
- `references/execution_playbooks.md`、`references/networking_patterns.md`、`references/observability_logging.md`、`references/performance_optimization.md`、`references/team_collaboration.md` 五份文档未在 SKILL.md 中被引用，任务分流无法命中，实际变成孤儿文档，既消耗维护成本又无法发挥作用。
- `anti_patterns.md` ↔ `review_checklists.md`、`architecture_and_network.md` ↔ `networking_patterns.md`、`domain_modeling.md` ↔ `ui_state_patterns.md`、`root_cause_enforcement.md` ↔ `swift_concurrency.md`、`decision_records.md` ↔ `team_collaboration.md`、`execution_playbooks.md` ↔ `root_cause_enforcement.md` 之间存在概念相邻但边界清晰的文档对，读者无法主动发现相关文档。

## 变更类型
- 合并重复：`refactoring_and_migration.md` + `migration_risk_control.md` → `migration_strategy.md`（主变更）。
- 修正表达：在 SKILL.md 场景规则和首步分流中补引用 5 份孤儿文档。
- 修正表达：在 6 组概念相邻文档之间补 "See also" 交叉引用。

## 变更内容
- 修改文件：
  - 新增 `references/migration_strategy.md`：合并两份迁移文档，按 "使用规则 → 重构原则 → 风险识别 → 阶段化迁移 → 兼容层策略 → 灰度与回滚 → 验证策略 → 发布前检查 → 审查输出标准 → 常见反模式" 组织。
  - 删除 `references/refactoring_and_migration.md`。
  - 删除 `references/migration_risk_control.md`。
  - 修改 `SKILL.md`：
    - 将"涉及重构、迁移、发布、灰度、回滚时"行替换为引用 `migration_strategy.md` + `build_release_and_ci.md`。
    - 将"迁移与发布"首步分流替换为引用 `migration_strategy.md`。
    - 在"场景规则"中新增引用：`execution_playbooks.md`（复杂任务剧本）、`networking_patterns.md`（具体网络模式）、`observability_logging.md`（日志与排障取证）、`performance_optimization.md`（性能优化）、`team_collaboration.md`（多人协作规范）。
    - 在"首步分流"中对应加行：排障追加可观测性、设计实现追加具体网络模式、审查追加性能/协作（根据任务类型）。
  - 在 `architecture_and_network.md` 网络层设计末尾追加：`详细请求/分页/缓存/鉴权/上传下载模式见 networking_patterns.md`。
  - 在 `review_checklists.md` 末尾追加：`常见反模式对照 anti_patterns.md`。
  - 在 `decision_records.md` 使用规则末尾追加：`跨人决策同步与 ownership 见 team_collaboration.md`。
  - 在 `domain_modeling.md` ViewState 建模小节末尾追加：`UI 状态机与异步回写建模见 ui_state_patterns.md`。
  - 在 `root_cause_enforcement.md` 证据要求末尾追加：`并发相关证据链建模见 swift_concurrency.md；日志分层与必记字段见 observability_logging.md`。
  - 在 `execution_playbooks.md` 各剧本说明后追加：`排障剧本遵守 root_cause_enforcement.md 根因纪律；迁移剧本遵守 migration_strategy.md 风险门禁`。
- 替代或合并旧规则：
  - `refactoring_and_migration.md` 的"重构原则 / 巨型文件拆分 / 迁移策略 / 审查输出标准 / 验证清单"合并入新文件对应小节。
  - `migration_risk_control.md` 的"风险识别 / 阶段化迁移 / 兼容层策略 / 灰度与回滚 / 验证策略 / 发布前检查 / 常见反模式"合并入新文件对应小节，去重阶段化迁移和兼容层策略中的表述重复。
  - 两份文件中重复出现的"常见反模式"统一合并为一份，避免相同规则在两个文件中分别维护。

## 预期收益
- 迁移场景读者只需加载一份 `migration_strategy.md` 即可拿到重构原则 + 风险控制完整视角，减少约 700 字上下文重复和规则优先级冲突。
- 5 份孤儿文档正式进入分流路径，任务命中率提升，避免任务因缺少引用而绕行。
- "See also" 交叉引用减少读者主动发现相关文档的成本，避免只读主文档时遗漏协作性规则。
- SKILL.md 引用完整后可作为 references 目录的 single source of truth，未来新增文档必须同步登记，降低再次出现孤儿文档的概率。

## 验证
- 结构校验：
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `SKILL.md` 行数仍 ≤ 500。
  - `agents/openai.yaml` YAML 结构合法。
  - `root_cause_enforcement.md` 不引入 MCP 控制章节；`examples.md` 不引入根因或 MCP 控制章节。
- 场景回放：
  - 场景 `migration`：用户输入"准备把这个老的聊天页从 callback 迁到 async/await，给一个落地方案"。期望命中四段式 + 阶段计划 + 兼容层 + 回滚，并只引用 `migration_strategy.md`，不再同时引用两份旧文档。
- 残留风险：
  - 新文件行数可能接近 150 行上限，需确认未超出；若超出，下次提案进一步拆分"重构原则"到独立章节或单独文档。
  - `execution_playbooks.md` 已加入分流，后续若发现它与 `root_cause_enforcement.md`、`migration_strategy.md` 再出现重复，需要单独提案处理。
  - 概念相邻文档的 See also 只单向添加，未来若发现读者从另一方向查找仍然错过，需补全双向引用。

## 状态
- promoted
