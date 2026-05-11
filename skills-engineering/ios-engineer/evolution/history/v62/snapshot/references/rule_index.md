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
| IR-006 | active | 涉及并发 / 可用性 API / SwiftUI 行为 / 网络取消语义的输出，"结论"前必须有独立"版本前提"块（真值或显式假设），字段存在性可机械校验 | 同上 |
| IR-007 | active | 不要格式化代码，除非明确要求 | 同上 |
| IR-008 | active | 任何改动都必须声明「已覆盖、未覆盖、残留风险」 | 同上 |

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

每条 ROUTE 的 TRIGGER / SKIP 锚点对落在 SKILL.md 内对应 bullet 下方；本表"摘要"列只保留主关键词集，避免 SKILL.md 与本表双重维护 TRIGGER / SKIP。

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
| ROUTE-012 | active | 重构落地 / 迁移 / 灰度 / 回滚 → migration_strategy.md | 同上 |
| ROUTE-013 | active | 构建 / CI / 发布观测 → build_release_and_ci.md | 同上 |
| ROUTE-014 | active | 编码约定 / 术语 / 命名 / 访问控制 → ios_conventions.md | 同上 |
| ROUTE-015 | active | 跨模块协作 / ownership / PR 拆分 / 技术债 → team_collaboration.md | 同上 |
| ROUTE-016 | active | 工具预算 / 子代理分流 / 多轮排查 / 搜索控制 → mcp_control.md | 同上 |
| ROUTE-017 | active | 复杂任务剧本（升级判据见 SKILL.md `### 路由优先级`）→ execution_playbooks.md | 同上 |
| ROUTE-018 | active | Skill 自进化 / 规则缺失冲突退役 / Skill 验证场景 → self_evolution.md | 同上 |

## 输出模板 OUT-NNN

| ID | Status | 摘要 | SKILL.md 锚点 |
|----|--------|------|---------------|
| OUT-001 | active | 正式方案 / 排障结论 / 迁移路线 / 性能分析的四段字段模板 → examples.md | `## 输出模板` |
| OUT-002 | active | 代码审查 / PR Review：findings-first 骨架（触发条件见 IR-004）→ review_checklists.md 第 8 节 | 同上 |
| OUT-003 | active | 产线代码骨架 → code_templates.md | 同上 |
| OUT-004 | active | 测试策略 / 验证范围 → testing_strategy.md | 同上 |
| OUT-005 | active | 架构裁决记录 → decision_records.md | 同上 |
| OUT-006 | active | iOS 测试体系建设 / 执行测试并修复失败 → test_execution_and_repair.md + testing_strategy.md | 同上 |

## OUT 子单元映射

`OUT-NNN` 编号映射到的 ref 文件常包含多个独立子单元（模板章节、剧本章节、双文件分工）。本表是反向定位辅助，不替代 OUT-NNN ID 治理；新增模板 / 剧本时同步更新本表。

| OUT-ID | 子单元名 | 文件锚点 | 适用场景 |
|--------|----------|----------|----------|
| OUT-003 | ViewModel 模板 | [code_templates.md](code_templates.md) "## ViewModel 模板" | UIKit MVVM / SwiftUI 状态驱动页面 / 列表表单详情页状态编排 |
| OUT-003 | UseCase 模板 | [code_templates.md](code_templates.md) "## UseCase 模板" | 业务规则聚合 / 多数据源编排 / 领域层输入输出建模 |
| OUT-003 | Repository 模板 | [code_templates.md](code_templates.md) "## Repository 模板" | 远端 + 本地缓存聚合 / 解耦 Service 与业务层 |
| OUT-003 | APIClient 模板 | [code_templates.md](code_templates.md) "## APIClient 模板" | URLSession + async/await / 强类型错误建模 |
| OUT-003 | Coordinator 模板 | [code_templates.md](code_templates.md) "## Coordinator 模板" | UIKit 导航编排 / Feature 路由解耦 |
| OUT-003 | Actor 模板 | [code_templates.md](code_templates.md) "## Actor 模板" | 共享可变状态隔离 / Token 刷新 / 内存缓存 / 请求去重 |
| OUT-006 | 测试规划（分层与覆盖策略） | [testing_strategy.md](testing_strategy.md) | 设计测试时按层选 stub / 决定覆盖范围 |
| OUT-006 | 测试执行与失败修复 | [test_execution_and_repair.md](test_execution_and_repair.md) | 跑测试 / 分析失败 / 决定补还是修 |
| ROUTE-017 | 接手遗留页面 | [execution_playbooks.md](execution_playbooks.md) "## 接手遗留页面" | 超大 ViewController / 状态散落 / UIKit + SwiftUI 混合老页面 |
| ROUTE-017 | 反复偶现 Crash 系统排查 | [execution_playbooks.md](execution_playbooks.md) "## 反复偶现 Crash 系统排查" | 难复现崩溃 / 线上偶发异常 / 随机状态错乱 |
| ROUTE-017 | 性能专项 | [execution_playbooks.md](execution_playbooks.md) "## 性能专项" | 启动慢 / 列表卡顿 / 页面刷新重 / 内存异常增长 |
| ROUTE-017 | 并发架构迁移 | [execution_playbooks.md](execution_playbooks.md) "## 并发架构迁移" | callback 迁 async/await / GCD 迁结构化并发 / 串行队列迁 actor |
| ROUTE-017 | 大型重构落地 | [execution_playbooks.md](execution_playbooks.md) "## 大型重构落地" | 模块拆分 / 导航重建 / 状态模型重建 / 网络层重构 |

## 退役记录

| ID | Status | 退役原因 | 替代 ID | 退役提案 |
|----|--------|----------|---------|----------|
| ROUTE-019 | retired | 与 ROUTE-018 真重复：ROUTE-019 把"Skill 验证场景"路由到 validation_scenarios.md，而 ROUTE-018 已声明"需要验证场景追加 validation_scenarios.md"。退役后"Skill 验证场景"关键词并入 ROUTE-018 主关键词集。 | ROUTE-018 | 20260508-154338-retire-route-019-merge-into-018 |
| IR-009 | retired | 是 9 条 IR 里唯一把执行委托给 ref 的 meta-IR（"统一遵守 ios_conventions.md"），与其它 8 条具体行为指令不同层；其职能已被 ROUTE-014（"编码约定 → ios_conventions.md"）覆盖。退役后 IR 层仅保留具体行为指令，表达一致。 | ROUTE-014 | 20260508-155152-retire-ir-009-meta-ir |

## 跨文件共享概念索引

兑现 [self_evolution.md](self_evolution.md) "候选版约束" 中"涉及跨文件共享概念的提案必须 grep 全量位置覆盖"的执行细则。修改 owner 位置时必须同步遍历所有引用位置；改引用位置不动 owner 视为局部澄清，不进入跨文件提案范围。

| 概念 | Owner 位置 | 引用位置 | 修改协议 |
|------|-----------|---------|----------|
| 四段式输出（根因 → 为什么 → 修法 → 验证） | [SKILL.md](../SKILL.md) IR-004 | [examples.md](examples.md) §1/§2/§4/§5/§6；[decision_records.md](decision_records.md) L5；[test_execution_and_repair.md](test_execution_and_repair.md) L82；[validation_scenarios.md](validation_scenarios.md) L26 / L88；[migration_strategy.md](migration_strategy.md)（剧本产物层） | 改 owner 必须同步所有引用；任一引用句式偏离 owner 即视为漂移 |
| findings-first 骨架（review 输出） | [review_checklists.md](review_checklists.md) §8 | [SKILL.md](../SKILL.md) IR-004 例外条款；[SKILL.md](../SKILL.md) OUT-002；[examples.md](examples.md) §3；[migration_strategy.md](migration_strategy.md) L114 | 改 owner 骨架字段必须同步 SKILL.md IR-004 / OUT-002 描述与 examples.md §3 引用句 |
| 参数透传与数据来源 | [architecture_and_network.md](architecture_and_network.md) "参数透传与数据来源" 节 | [SKILL.md](../SKILL.md) ROUTE-002；[review_checklists.md](review_checklists.md) §1 / §2；[validation_scenarios.md](validation_scenarios.md) 场景 2 | 改 owner 节标题必须同步 review_checklists.md 内对该节的字面引用；改概念定义必须同步 SKILL.md ROUTE-002 关键词 |
| 任务分流主关键词集 | [SKILL.md](../SKILL.md) ROUTE 表 | 本文件 ROUTE-NNN 摘要列；[mcp_control.md](mcp_control.md)（按工具预算分流） | 改 SKILL.md ROUTE 关键词必须同步本文件摘要列；新增 ROUTE 必须同步 [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh) 双向断言；新增 / 调整 ROUTE 的 TRIGGER / SKIP 锚点不改本表摘要列，只有主关键词集变化时才同步本表 |
| 残留风险声明（已覆盖 / 未覆盖 / 残留风险 三字段） | [SKILL.md](../SKILL.md) IR-008 | [examples.md](examples.md) 使用规则 + §1/§2/§4/§5/§6 模板末段；[review_checklists.md](review_checklists.md) §8 骨架末段；[code_templates.md](code_templates.md) 使用规则 | 改 owner 字段名或字段数必须同步三份引用文件对应段；三字段必须以独立段落字面存在，不得合并进"验证"段或"验证缺口"段；新增/缩减字段须先调整 owner 再批量同步所有引用位置 |
| 版本前提声明（iOS / Swift 真值或显式假设） | [SKILL.md](../SKILL.md) IR-006 | [examples.md](examples.md) 使用规则 + §1/§2/§4/§5/§6 模板首段；[review_checklists.md](review_checklists.md) §8 骨架首段；[validation_scenarios.md](validation_scenarios.md) 场景 3 通过标准 | 改 owner 字面（含二选一表述、触发维度集合）必须同步所有引用；新增模板必须同步插入"版本前提"块；该块作为独立段落字面存在不得合并入"结论"或"为什么"段；段标题"版本前提"是机械校验 anchor，重命名需批量同步全部引用位置 |
| 提案候选信号阈值 | [scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) L69-L72（4 个 `*_THRESHOLD` 常量） | [usage_ledger.md](usage_ledger.md) 第 8 节阈值表；[scripts/validate_skill_evolution.sh](../scripts/validate_skill_evolution.sh) `[11/13]` 步 | 改任一侧必须同步另一侧；validate_skill_evolution.sh `[11/13]` 步会自动断言不一致；新增第 5 个阈值需同步更新本表 + 文档 + 校验正则 |
