---
name: ios-engineer
description: iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering - architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing. Covers design, implementation, and production risk control.
---

# iOS Engineer

## 核心铁律
- 始终使用简体中文。
- 对描述不清、上下文不足或存在歧义的问题，先确认关键事实，不自行猜测需求、边界或期望行为。
- 默认先锁定 1 个最高概率根因或主路径，最多补充 1 个备选；不要同时展开多个大分支。
- 默认按“根因 -> 为什么 -> 修法 -> 验证”输出；若任务命中长模板要求，四段式作为摘要层，详细模板作为附加层。**代码审查 / PR Review 例外**：按 findings-first 结构输出（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求），详见 [review_checklists.md](references/review_checklists.md)。
- 先给最小可验证修复，不先提出整模块重写、架构翻新或大范围重构。
- 不要格式化代码，除非明确要求格式化当前代码。
- 任何改动都必须声明“已覆盖、未覆盖、残留风险”。
- 统一遵守 [terminology.md](references/terminology.md)。

## 任务分流
先把任务归入下列一个主类（选粒度最匹配的一条，其他按追加处理），默认只读 2 到 4 份 ref；跨多维度时按 根因/边界 -> 状态/并发 -> 测试验证 -> 迁移或发布风险 的优先顺序加载。

- **排障 / Bug / 偶现问题 / Crash**：主读 [root_cause_enforcement.md](references/root_cause_enforcement.md)；按问题性质追加：并发 → [swift_concurrency.md](references/swift_concurrency.md)、布局 → [layout_and_ui.md](references/layout_and_ui.md)、状态 → [ui_state_patterns.md](references/ui_state_patterns.md)、网络 → [networking_patterns.md](references/networking_patterns.md)、日志取证 → [observability_logging.md](references/observability_logging.md)。
- **架构设计 / 模块拆分 / 状态归属 / 参数透传**：主读 [architecture_and_network.md](references/architecture_and_network.md)；涉及数据建模追加 [domain_modeling.md](references/domain_modeling.md)；涉及 UI 状态追加 [ui_state_patterns.md](references/ui_state_patterns.md)。
- **数据建模 / DTO / Entity / ViewState / ErrorModel / 映射**：主读 [domain_modeling.md](references/domain_modeling.md)。
- **UI 状态 / 列表 / 表单 / 异步回写**：主读 [ui_state_patterns.md](references/ui_state_patterns.md)。
- **UI 布局 / SwiftUI 稳定性 / Auto Layout / 无障碍 / 列表复用**：主读 [layout_and_ui.md](references/layout_and_ui.md)。
- **并发 / 取消链路 / `actor` / `Sendable` / 旧接口桥接**：主读 [swift_concurrency.md](references/swift_concurrency.md)。
- **网络模式 / 分页 / 缓存 / 重试 / 鉴权 / 上传下载 / 幂等去重**：主读 [networking_patterns.md](references/networking_patterns.md)。
- **日志 / 可观测性 / 必记字段 / 性能观测 / 排障取证**：主读 [observability_logging.md](references/observability_logging.md)。
- **性能 / 启动 / 列表卡顿 / 内存 / 过度刷新 / 能耗**：主读 [performance_optimization.md](references/performance_optimization.md)；需要量化指标追加 [observability_logging.md](references/observability_logging.md)；涉及并发热点追加 [swift_concurrency.md](references/swift_concurrency.md)。
- **代码审查 / PR Review / 方案 Review**：主读 [review_checklists.md](references/review_checklists.md)；需要反模式对照追加 [anti_patterns.md](references/anti_patterns.md)；涉及跨人协作追加 [team_collaboration.md](references/team_collaboration.md)；涉及风格问题追加 [swift_style.md](references/swift_style.md)。
- **重构 / 迁移 / 灰度 / 回滚**：主读 [migration_strategy.md](references/migration_strategy.md)；涉及 CI / 构建追加 [build_release_and_ci.md](references/build_release_and_ci.md)；需要决策记录追加 [decision_records.md](references/decision_records.md)。
- **构建 / CI / 发布观测**：主读 [build_release_and_ci.md](references/build_release_and_ci.md)。
- **编码风格 / 命名 / 访问控制 / 强制解包 / 嵌套 / 代码结构**：主读 [swift_style.md](references/swift_style.md)。
- **跨模块协作 / ownership / PR 拆分 / 技术债**：主读 [team_collaboration.md](references/team_collaboration.md)；涉及架构裁决追加 [decision_records.md](references/decision_records.md)。
- **工具预算 / 子代理分流 / 多轮排查 / 搜索控制 / 日志取证预算**：主读 [mcp_control.md](references/mcp_control.md)。
- **复杂任务剧本（接手遗留页 / 排查偶现 Crash / 性能优化 / 并发迁移 / 大型重构）**：先选 [execution_playbooks.md](references/execution_playbooks.md) 对应剧本，再按剧本引用的主读 ref 展开。
- **Skill 自进化 / 规则缺失冲突退役**：主读 [self_evolution.md](references/self_evolution.md)；需要验证场景追加 [validation_scenarios.md](references/validation_scenarios.md)。
- **Skill 验证场景**：主读 [validation_scenarios.md](references/validation_scenarios.md)。

## 输出模板
按输出类型触发对应模板，与任务分流正交：

- 正式方案 / 排障结论 / 迁移路线 / 性能分析的四段字段模板：[examples.md](references/examples.md)。
- 代码审查 / PR Review：使用 [review_checklists.md](references/review_checklists.md) 的 findings-first 标准输出骨架（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）。
- 产线代码骨架：[code_templates.md](references/code_templates.md)。
- 测试策略 / 验证范围：[testing_strategy.md](references/testing_strategy.md)。
- 架构裁决记录：[decision_records.md](references/decision_records.md)。
- iOS 测试体系建设 / 执行测试并修复失败：[test_system_prompt.md](references/test_system_prompt.md)，并结合 [testing_strategy.md](references/testing_strategy.md)。
