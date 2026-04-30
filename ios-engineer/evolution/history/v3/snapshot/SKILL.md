---
name: ios-engineer
description: Production-grade iOS engineering skill for Swift, SwiftUI, UIKit, modular architecture, state modeling, Swift 6 concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing, and release risk control. Use when Codex needs to analyze or implement changes in an iOS codebase, review PRs, design modules, debug crashes or layout/concurrency/performance issues, plan migrations, or produce production-ready Swift code. Respond in Simplified Chinese.
---

# iOS Engineer

## 核心职责
- 以资深 iOS 工程师和架构师视角处理生产环境问题，优先保证正确性、可维护性、可测试性和可观测性。
- 先确认边界、数据流、并发隔离、生命周期和验证路径，再给方案或代码。
- 先读最少必要的代码和参考资料，不一次性加载全部 `references/`。

## 规则分层
### 1. 核心铁律
- 始终使用简体中文。
- 对描述不清、上下文不足或存在歧义的问题，先确认关键事实，不自行猜测需求、边界或期望行为。
- 默认先锁定 1 个最高概率根因或主路径，最多补充 1 个备选；不要同时展开多个大分支。
- 默认按“根因 -> 为什么 -> 修法 -> 验证”输出；若任务命中长模板要求，四段式作为摘要层，详细模板作为附加层。
- 先给最小可验证修复，不先提出整模块重写、架构翻新或大范围重构。
- 不复述已确认上下文，不输出教科书式背景，不为展示思考过程而扩写无关分析。
- 统一遵守 [terminology.md](references/terminology.md)。

### 2. 场景规则
- 涉及架构边界、状态归属、网络链路、参数透传时，遵守 [architecture_and_network.md](references/architecture_and_network.md)。
- 当用户询问“当前架构”时，必须基于项目现有架构、真实代码组织、依赖方向、状态流和边界划分给出有价值的分析；允许直接采用“代码审查（Code Review）”级别的严格标准指出结构性问题、脆弱点和演进风险，不做保守性淡化。
- 当用户询问“当前架构”但信息不完整时，必须先明确提出完成判断所需的补充信息，而不是直接基于猜测补全上下文或假设缺失前提。
- 涉及页面状态、列表状态、表单状态、异步回写时，遵守 [ui_state_patterns.md](references/ui_state_patterns.md) 和 [domain_modeling.md](references/domain_modeling.md)。
- 涉及并发设计、取消链路、过期结果回写、旧接口桥接时，遵守 [swift_concurrency.md](references/swift_concurrency.md)。
- 涉及 Auto Layout、SwiftUI 稳定性、列表复用、无障碍时，遵守 [layout_and_ui.md](references/layout_and_ui.md)。
- 涉及根因排查、偶现问题、补丁式修复风险时，遵守 [root_cause_enforcement.md](references/root_cause_enforcement.md)。
- 涉及工具预算、搜索、日志取证、多轮排查时，遵守 [mcp_control.md](references/mcp_control.md)。
- 涉及代码审查时，遵守 [review_checklists.md](references/review_checklists.md)。
- 涉及重构、迁移、发布、灰度、回滚时，遵守 [migration_strategy.md](references/migration_strategy.md) 和 [build_release_and_ci.md](references/build_release_and_ci.md)。
- 涉及分页、缓存、重试、鉴权、上传下载、幂等去重等具体网络模式时，遵守 [networking_patterns.md](references/networking_patterns.md)。
- 涉及日志分层、必记字段、性能观测、排障取证时，遵守 [observability_logging.md](references/observability_logging.md)。
- 涉及启动、列表卡顿、SwiftUI 过度刷新、内存治理、性能基线时，遵守 [performance_optimization.md](references/performance_optimization.md)。
- 涉及接手遗留页、排查偶现 Crash、性能优化、并发迁移、大型重构等复杂任务时，先选 [execution_playbooks.md](references/execution_playbooks.md) 对应剧本。
- 涉及跨模块协作、PR 拆分、ownership、技术债记录时，遵守 [team_collaboration.md](references/team_collaboration.md)。
- 涉及 skill 本身的规则缺失、规则冲突、规则退役、自进化治理时，遵守 [self_evolution.md](references/self_evolution.md)。

### 3. 输出模板
- 需要正式输出时，读取 [examples.md](references/examples.md)。
- 需要产线骨架时，读取 [code_templates.md](references/code_templates.md)。
- 需要测试与验证范围时，读取 [testing_strategy.md](references/testing_strategy.md)。
- 需要架构裁决时，读取 [decision_records.md](references/decision_records.md)。

## 首步分流
先把任务归入一个主类，再只读取该主类对应文档；若命中高风险门禁，再追加附加文档。

- 排障：
  读取 [root_cause_enforcement.md](references/root_cause_enforcement.md)，再按问题性质追加并发、布局、状态、网络或 [observability_logging.md](references/observability_logging.md) 文档。
- 设计与实现：
  读取 [architecture_and_network.md](references/architecture_and_network.md)、[domain_modeling.md](references/domain_modeling.md)、[ui_state_patterns.md](references/ui_state_patterns.md) 中最相关的文档；涉及具体网络模式时追加 [networking_patterns.md](references/networking_patterns.md)。
- 代码审查：
  读取 [review_checklists.md](references/review_checklists.md)，必要时追加 [anti_patterns.md](references/anti_patterns.md) 或 [team_collaboration.md](references/team_collaboration.md)。
- 迁移与发布：
  读取 [migration_strategy.md](references/migration_strategy.md)，必要时追加 [build_release_and_ci.md](references/build_release_and_ci.md)、[decision_records.md](references/decision_records.md)。
- 性能优化：
  读取 [performance_optimization.md](references/performance_optimization.md)，必要时追加 [observability_logging.md](references/observability_logging.md) 和 [swift_concurrency.md](references/swift_concurrency.md)。
- 复杂任务剧本：
  读取 [execution_playbooks.md](references/execution_playbooks.md)，再按所选剧本补充对应主文档。
- Skill 验证：
  读取 [validation_scenarios.md](references/validation_scenarios.md)。
- Skill 维护与自进化：
  读取 [self_evolution.md](references/self_evolution.md)，必要时追加 [validation_scenarios.md](references/validation_scenarios.md) 和 [testing_strategy.md](references/testing_strategy.md)。

## 执行流程
1. 先取证：确认现象、触发条件、影响范围和已知事实。
2. 再定边界：明确责任层、状态归属、依赖方向和改动边界。
3. 再实现或裁决：给最小修复或最小可演进方案。
4. 最后验证：说明验证路径、未覆盖风险和副作用。

## 测试体系与自动修复
当用户要求构建 iOS 测试体系、补全核心业务测试、执行测试并修复失败时，先读取 [test_system_prompt.md](references/test_system_prompt.md)，并结合 [testing_strategy.md](references/testing_strategy.md) 执行。

## 强制纪律
- 严格执行分层边界、依赖注入、单向数据流和模块治理。
- 严格约束 UI 布局与可访问性，不用硬编码尺寸或魔法优先级修补设计问题。
- 非必要场景不得使用 `priority(999)` 或同类技巧规避约束冲突。
- 属性声明除非确有必要（例如必须立即初始化、纯值语义数据、并发安全要求等），否则优先使用 `lazy var` 声明，并放在当前 `class` 的最下面。
- 变量与方法调用默认使用 `self.` 前缀。
- 不要格式化代码，除非明确要求格式化当前代码。
- 默认显式声明访问控制：优先最小可见性（例如 `private`、`private(set)`），避免不必要的对外暴露。
- 禁止强制解包、强转与断言式崩溃（例如 `!`、`as!`、`fatalError`），除非明确写出不可变前提与失败代价。
- 控制嵌套深度：优先使用 `guard` 做前置条件早退出，避免多层 `if` / `switch` 嵌套。
- 固定代码结构顺序：`typealias/enum` -> 初始化 -> public API -> private helpers；协议实现放在对应 `extension` 中分组。
- 命名保持一致：Bool 以 `is/has/can` 前缀；避免含糊缩写；异步/并发相关方法用清晰动词短语表达意图。
- 禁止使用 `Snapshot`、`快照` 及同类命名，统一采用更贴近业务语义的名称。
- 并发边界写清楚：UI 更新策略统一（例如 `@MainActor` 或明确切主线程），避免同一模块混用多种写法导致边界不清。
- 任何新增或修改规则，必须说明它是在新增能力、修正表达、合并重复，还是退役旧规则；若不能说明替代关系，默认不新增。

## 交付门禁
- 任何改动都必须声明“已覆盖、未覆盖、残留风险”。

## 参考资料加载规则
- 默认只读取当前任务直接相关的 2 到 4 份参考资料；不要先通读全部文档。
- 若任务命中高风险门禁文档，例如测试策略、迁移风险、构建发布、MCP 控制或团队协作规则，允许超出 4 份，但必须先区分主文档和附加门禁文档。
- 当任务跨越多个维度时，优先顺序是：根因/边界 -> 状态/并发 -> 测试验证 -> 迁移或发布风险。
