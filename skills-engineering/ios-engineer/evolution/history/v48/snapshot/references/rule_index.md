# 规则 ID 索引

## 使用规则
- 本文件是 [SKILL.md](../SKILL.md) 内 rule-ID 的真值索引。新增 / 修改 / 退役 ID **先改本文，再同步 SKILL.md**。
- 自动校验脚本 [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh) 断言两侧 ID 集合双向一致；不一致即非零退出。
- ID 格式：`^[A-Z]+-\d{3}$`，前缀分四类：
  - `IR-NNN` — 核心铁律（Iron Rule），全局生效
  - `SYM-NNN` — 症状导航表行（Symptom routing row）
  - `ROUTE-NNN` — 任务分流 bullet（Task routing entry）
  - `OUT-NNN` — 输出模板条目（Output template entry）
- ID 一旦发布不复用：退役后保留在「退役记录」节，标 `retired`，并指明替代 ID（无替代标 `retired-no-replacement`）。退役 ID 在 SKILL.md 中**不应再出现**——校验脚本会报警。
- ID 不携带语义后缀（不写 `ROUTE-LAYOUT-001` 这种）；语义靠本表的「摘要」列传达，避免重命名/拆分时出现 ID 含义漂移。
- 编号可有空洞（如 `IR-002` 之后跳到 `IR-007`），无强制连续约束；新增条目优先使用前缀内最大编号 +1。

## 铁律 IR-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| IR-001 | active | 始终使用简体中文 | `## 核心铁律` |
| IR-002 | active | 描述不清 / 上下文不足 / 歧义时先确认关键事实，不自行猜测 | 同上 |
| IR-003 | active | 默认先锁定 1 个最高概率根因或主路径，最多补充 1 个备选 | 同上 |
| IR-004 | active | 默认按「根因 → 为什么 → 修法 → 验证」四段式输出；review 例外走 findings-first | 同上 |
| IR-005 | active | 先给最小可验证修复，不先提出整模块重写或大范围重构 | 同上 |
| IR-006 | active | 涉及并发 / 可用性 API / SwiftUI 行为 / 网络取消语义的建议，输出前必须先求证 `IPHONEOS_DEPLOYMENT_TARGET` 与 `SWIFT_VERSION` | 同上 |
| IR-007 | active | 不要格式化代码，除非明确要求 | 同上 |
| IR-008 | active | 任何改动都必须声明「已覆盖、未覆盖、残留风险」 | 同上 |
| IR-009 | active | 统一遵守 [ios_conventions.md](ios_conventions.md) | 同上 |

## 症状导航 SYM-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| SYM-001 | active | Crash / 崩溃 / 断言 / 强解 / 野指针 → root_cause_enforcement.md | `### 症状导航` |
| SYM-002 | active | UI 错位 / 约束冲突 / 列表跳动 / 无障碍 → layout_and_ui.md | 同上 |
| SYM-003 | active | 状态错乱 / 异步回写 / 旧请求覆盖 → ui_state_patterns.md | 同上 |
| SYM-004 | active | 请求失败 / 鉴权刷新 / 分页或缓存问题 → networking_patterns.md | 同上 |
| SYM-005 | active | 卡顿 / 启动慢 / 内存上涨 / 能耗 → performance_optimization.md | 同上 |
| SYM-006 | active | 命名混乱 / 强制解包 / 访问控制 → ios_conventions.md | 同上 |
| SYM-007 | active | 老项目越改越乱 / 不敢动某块 / 接手陌生项目无入口 → architecture_analysis.md | 同上 |

## 任务分流 ROUTE-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| ROUTE-001 | active | 排障 / Bug / 偶现问题 / Crash → root_cause_enforcement.md | `## 任务分流` |
| ROUTE-002 | active | 架构设计 / 模块拆分 / 状态归属 / 参数透传 → architecture_and_network.md | 同上 |
| ROUTE-003 | active | 架构分析 / 项目健康度 / 重构路线图 → architecture_analysis.md | 同上 |
| ROUTE-004 | active | 数据建模 / DTO / Entity / ViewState / ErrorModel → domain_modeling.md | 同上 |
| ROUTE-005 | active | UI 状态 / 列表 / 表单 / 异步回写 → ui_state_patterns.md | 同上 |
| ROUTE-006 | active | UI 布局 / SwiftUI 稳定性 / Auto Layout / 无障碍 → layout_and_ui.md | 同上 |
| ROUTE-007 | active | 并发 / 取消链路 / actor / Sendable → swift_concurrency.md | 同上 |
| ROUTE-008 | active | 网络模式 / 分页 / 缓存 / 重试 / 鉴权 → networking_patterns.md | 同上 |
| ROUTE-009 | active | 日志 / 可观测性 / 必记字段 / 排障取证 → observability_logging.md | 同上 |
| ROUTE-010 | active | 性能 / 启动 / 列表卡顿 / 内存 / 能耗 → performance_optimization.md | 同上 |
| ROUTE-011 | active | 代码审查 / PR Review / 方案 Review → review_checklists.md | 同上 |
| ROUTE-012 | active | 重构 / 迁移 / 灰度 / 回滚 → migration_strategy.md | 同上 |
| ROUTE-013 | active | 构建 / CI / 发布观测 → build_release_and_ci.md | 同上 |
| ROUTE-014 | active | 编码约定 / 术语 / 命名 / 访问控制 → ios_conventions.md | 同上 |
| ROUTE-015 | active | 跨模块协作 / ownership / PR 拆分 / 技术债 → team_collaboration.md | 同上 |
| ROUTE-016 | active | 工具预算 / 子代理分流 / 多轮排查 / 搜索控制 → mcp_control.md | 同上 |
| ROUTE-017 | active | 复杂任务剧本 → execution_playbooks.md | 同上 |
| ROUTE-018 | active | Skill 自进化 / 规则缺失冲突退役 / Skill 验证场景 → self_evolution.md | 同上 |

## 输出模板 OUT-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| OUT-001 | active | 正式方案 / 排障结论 / 迁移路线 / 性能分析的四段字段模板 → examples.md | `## 输出模板` |
| OUT-002 | active | 代码审查 / PR Review 使用 review_checklists.md 第 8 节 findings-first 骨架 | 同上 |
| OUT-003 | active | 产线代码骨架 → code_templates.md | 同上 |
| OUT-004 | active | 测试策略 / 验证范围 → testing_strategy.md | 同上 |
| OUT-005 | active | 架构裁决记录 → decision_records.md | 同上 |
| OUT-006 | active | iOS 测试体系建设 / 执行测试并修复失败 → test_execution_and_repair.md + testing_strategy.md | 同上 |

## 退役记录

| ID | Status | 退役原因 | 替代 ID | 退役提案 |
|----|--------|----------|---------|----------|
| ROUTE-019 | retired | 与 ROUTE-018 真重复：ROUTE-019 把"Skill 验证场景"路由到 validation_scenarios.md，而 ROUTE-018 已声明"需要验证场景追加 validation_scenarios.md"。退役后"Skill 验证场景"关键词并入 ROUTE-018 主关键词集。 | ROUTE-018 | 20260508-154338-retire-route-019-merge-into-018 |
