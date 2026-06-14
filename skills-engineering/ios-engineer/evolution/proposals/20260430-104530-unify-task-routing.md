# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-104530-unify-task-routing
- Created At: 2026-04-30 10:45:30 +0800
- Active Version At Creation: v10

## 问题信号
- SKILL.md 分流机制分散在三个章节：`### 2. 场景规则`（16 条）、`### 3. 输出模板`（5 条）、`## 首步分流`（8 个任务类别）。三者的本质都是"触发 → 读某份 ref"，只是分类维度不同（按关键词 / 按输出类型 / 按任务类别）。
- 同一份 ref 在三个章节中重复出现：`architecture_and_network.md` 出现在场景规则 L21 + 首步分流 L50；`observability_logging.md` 出现在场景规则 L30 + 首步分流 L48/L56；`testing_strategy.md` 出现在输出模板 L40/L42 + 首步分流 L62。AI 每次加载需扫三层才能定位主 ref。
- 场景规则触发粒度不一致：L29 很细（"分页、缓存、重试、鉴权、上传下载、幂等去重等具体网络模式"），L33 很粗（"跨模块协作、PR 拆分、ownership、技术债记录"），L35 是元规则级（"skill 本身的规则缺失"）。同一列表混三种粒度。
- 首步分流的"必要时追加"没有判断标准，AI 自由裁量导致命中不稳定。
- 从 AI 使用角度看，只需要一份"任务类型 → 主读 ref + 可追加 ref"的明确查表；现有三层结构是文档冗余，不是分层设计。

## 变更类型
- 合并重复：把 场景规则 + 首步分流 合并为单一 "任务分流表"，每份 ref 有且只有一个"主读"位置。
- 修正表达：统一分流条目的触发词粒度（按任务类型而不是关键词列表），把"必要时追加"改为明确的"按 X 情况追加 Y"。
- 退役规则：输出模板节保留（因为"输出驱动"和"任务驱动"是不同心智模型），但合并其中与场景规则重复的条目。

## 变更内容
- 修改文件：`SKILL.md`
  - 退役整个 `### 2. 场景规则` 章节（15 条）。
  - 退役整个 `## 首步分流` 章节（8 类 + 首段说明）。
  - 合并为单一 `## 任务分流` 章节，按任务类型归类，每类一条"主读 + 可追加"条目。15 类覆盖：
    1. 排障 / Bug / 偶现问题 → 主读 root_cause_enforcement.md
    2. 架构设计 / 模块拆分 / 状态归属 / 参数透传 → 主读 architecture_and_network.md
    3. 数据建模 / DTO / Entity / ViewState → 主读 domain_modeling.md
    4. UI 状态 / 列表 / 表单 / 异步回写 → 主读 ui_state_patterns.md
    5. UI 布局 / SwiftUI 稳定性 / Auto Layout / 无障碍 → 主读 layout_and_ui.md
    6. 并发 / 取消链路 / actor / Sendable / 旧接口桥接 → 主读 swift_concurrency.md
    7. 网络模式 / 分页 / 缓存 / 重试 / 鉴权 / 上传下载 / 幂等 → 主读 networking_patterns.md
    8. 日志 / 可观测性 / 排障取证 → 主读 observability_logging.md
    9. 性能 / 启动 / 列表卡顿 / 内存 / 过度刷新 → 主读 performance_optimization.md
    10. 代码审查 / PR Review → 主读 review_checklists.md
    11. 重构 / 迁移 / 灰度 / 回滚 → 主读 migration_strategy.md
    12. 构建 / CI / 发布 → 主读 build_release_and_ci.md
    13. 编码风格 / 命名 / 强制解包 / 嵌套 → 主读 swift_style.md
    14. 协作 / ownership / PR 拆分 / 技术债 → 主读 team_collaboration.md
    15. 工具控制 / 多轮排查 / 搜索预算 → 主读 mcp_control.md
    16. 复杂任务剧本（接手遗留页 / 偶现 Crash / 性能优化 / 并发迁移 / 大型重构） → 先选 execution_playbooks.md 剧本
    17. 反模式识别 → 审查时追加 anti_patterns.md
    18. Skill 自进化治理 → 主读 self_evolution.md
    19. Skill 验证场景 → 主读 validation_scenarios.md
  - 保留 `### 3. 输出模板`，但作为独立 `## 输出模板` 一级章节（不再嵌在"规则分层"下）；共 5 条触发式引用（examples / code_templates / testing_strategy / decision_records / test_system_prompt）。
  - 保留核心铁律（Proposal H 定稿的 9 条）。
- 修改后主文件结构：
  ```
  frontmatter
  # iOS Engineer
  ## 核心铁律（9 条，含 terminology 引用）
  ## 任务分流（19 类，每类主读 + 可追加）
  ## 输出模板（5 条触发式引用）
  ```
- 替代或合并旧规则：
  - 场景规则 16 条 → 并入任务分流，每条按任务类型重写；重复的触发词（例如 "架构边界" 和 "架构设计"）合并。
  - 首步分流 8 类 → 并入任务分流，原有"排障 / 设计与实现 / 代码审查 / 迁移与发布 / 性能优化 / 复杂任务剧本 / Skill 验证 / Skill 维护" 重新映射到新 19 类（粒度更细）。
  - "必要时追加"替换为"按 X 情况追加 Y"，让 AI 有明确判断条件。
  - 首步分流的"默认 2-4 份"和"跨维度优先顺序"两条保留，放在任务分流章节的首段作为加载约束。

## 预期收益
- SKILL.md 章节数从 4 个（核心铁律 / 场景规则 / 输出模板 / 首步分流）降到 3 个（核心铁律 / 任务分流 / 输出模板）。
- 每份 ref 在"任务分流"表中有且只有一个"主读"位置。AI 加载后可直接 O(1) 定位对应 ref，不再需要三层扫描。
- 任务分流条目粒度统一（按任务类型），不再混合关键词 / 输出类型 / 任务类别三种维度。
- "按 X 情况追加" 替换"必要时追加"后，追加引用的触发条件可被 AI 机械判断，行为一致性提升。
- SKILL.md 预计行数 45-50 行，actionable 密度 > 90%。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在（本提案不新增不删除 ref）。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
  - 手动核对：25 份 references（含输出模板）每份都在任务分流或输出模板中出现，没有漏引用；每份 ref 在任务分流中只有一个主读位置。
- 场景回放：
  - 场景 `layout`：用户输入"消息气泡高度偶发错误..."。期望 AI 命中"排障 / Bug"→ root_cause_enforcement.md，再按"UI 布局"追加 layout_and_ui.md；加载路径从 2 层扫描变为 1 层。
  - 场景 `migration`：用户输入"把聊天页从 callback 迁到 async/await"。期望命中"重构 / 迁移"→ migration_strategy.md 主读，按"并发"追加 swift_concurrency.md，按"决策记录"追加 decision_records.md。
  - 场景 `parameter-pass-through`：用户输入"新增字段 currentModel 在 A 类里拿不到"。期望命中"架构设计 / 参数透传" → architecture_and_network.md 主读，不再需要扫三层。
- 残留风险：
  - 19 类任务分流条目数量偏多，若条目彼此边界模糊（例如"架构设计" vs "数据建模" vs "UI 状态"），AI 可能命中多条。需要在分流首段明确说明"若多类命中，选粒度最匹配的一条，其他按追加处理"。
  - 退役场景规则后，原本作为"触发→ref"备忘清单的读者会失去该章节；但任务分流提供等效且更清晰的映射，实际不损失信息。
  - Proposal D 的"当前架构咨询"已下沉到 architecture_and_network.md 内部，场景规则退役不影响该规则生效。

## 状态
- promoted
