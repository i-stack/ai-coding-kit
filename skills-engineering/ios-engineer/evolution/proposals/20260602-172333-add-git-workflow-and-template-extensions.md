# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260602-172333-add-git-workflow-and-template-extensions
- Created At: 2026-06-02 17:23:33 +0800
- Active Version At Creation: v71

## 问题信号
- 2026-06-02 用户对 ios-engineer/references 做完整性 review，发现两个 P0 缺口：
  1. **Git 工作流缺 owner**：grep 全 29 个 ref 后确认，iOS 项目特有的 git 战术（pbxproj 冲突、storyboard/xib 合并、Asset Catalog 二进制资源、CocoaPods/SPM 锁文件提交、分支模型与 hotfix、cherry-pick / force-push 选型）没有单点 owner。`team_collaboration.md` 只覆盖通用 PR 拆分 / ownership / 技术债，`build_release_and_ci.md` 只覆盖依赖治理与发布流水线；两者都不解决 git 层冲突战术。结果是用户问"pbxproj 冲突怎么解 / Hotfix 怎么切"时，分流无单点路由。
  2. **设计模式选型碎片化**：SwiftUI propertyWrapper 选型（@State / @Binding / @StateObject / @Observable / @Bindable / @Environment）、依赖注入三选一（构造 / 属性 / 容器）、并发模型选型（async/await / AsyncSequence / Combine / callback / GCD）散落在 code_templates.md / ui_state_patterns.md / swift_concurrency.md / migration_strategy.md 多份文件，无单点决策表。用户问"我该用 @StateObject 还是 @Observable / 该不该上 Resolver / Combine 还是 AsyncSequence"时，必须跨文件跳读。

## 变更类型
- 新增能力

## 变更内容
- 新增文件：
  - `references/git_workflow.md`（覆盖 iOS 特有 git 战术：pbxproj/storyboard/xcassets 冲突、Pods/Package.resolved 提交策略、分支模型与 hotfix、提交与 PR 粒度、revert/reset/cherry-pick 选型表、.gitignore 基线、常见反模式）
- 修改文件：
  - `SKILL.md`：新增 `ROUTE-020` bullet 路由到 git_workflow.md，含 TRIGGER / SKIP 锚点对
  - `references/rule_index.md`：
    - "任务分流 ROUTE-NNN" 表新增 ROUTE-020 active 行
    - "OUT 子单元映射" 表新增 OUT-003 的 3 个子单元（SwiftUI propertyWrapper 选型 / 依赖注入三选一 / 并发模型选型），反向定位辅助
  - `references/code_templates.md`：
    - 目录追加 3 项
    - 新增 "## SwiftUI propertyWrapper 选型" 节（含 8 行包装器选型表 + iOS 17 决策树 + 版本前提声明）
    - 新增 "## 依赖注入三选一" 节（含 3 行 DI 方式选型表 + 强制规则 + 构造注入示例）
    - 新增 "## 并发模型选型" 节（含 6 行并发模型选型表 + 新代码默认顺序 + 版本前提声明）
- 替代或合并旧规则：
  - 无替代，纯新增能力。
  - 与现有 ref 关系：
    - git_workflow.md ↔ team_collaboration.md：互引不重复，前者 iOS git 战术、后者通用协作纪律
    - git_workflow.md ↔ build_release_and_ci.md：互引不重复，前者版本控制层、后者构建/CI/依赖治理层
    - code_templates.md 3 节 ↔ ui_state_patterns.md / swift_concurrency.md：选型表为入口，深入细节仍跳转专题 ref

## 预期收益
- ROUTE-020 提供 iOS git 战术单点路由，减少用户跨 ref 跳读、避免 PR 失误（如 pbxproj 冲突未本地 build 就 push、共享分支 force-push 等典型反模式）。
- code_templates.md 3 节把"散落的设计模式选型"收口到单文件查表，降低 SwiftUI 状态归属 / DI 方式 / 并发模型 3 类高频选型问题的回答时长。
- 新增内容均遵循现有 ref 风格：iOS 特化、含版本前提声明（命中 IR-006 触发维度）、含反模式列表、互引而非重复。

## 验证
- 结构校验：
  - `bash skills-engineering/ios-engineer/scripts/validate_rule_ids.sh` 通过：SKILL.md 与 rule_index.md 双向 ID 一致，ROUTE-020 新增对称登记。
  - `bash skills-engineering/ios-engineer/scripts/audit_ref_freshness.sh` 通过：新增 git_workflow.md 与修改的 code_templates.md / rule_index.md 首行 last-verified 均为 2026-06。
  - 跨文件共享概念检查：ROUTE-020 新增不涉及现有跨文件共享概念（四段式 / findings-first / 参数透传 / 残留风险声明 / 版本前提 / 前置确认 / 逻辑性 / 认知对手模式 / 提案候选信号阈值），无需同步其他 ref。
- 场景回放：
  - 本提案不修改任何现有 ROUTE / SYM / OUT / IR / GR 字面，不涉及已有验证场景；故不强制回放。
  - 后续如出现 git 工作流相关 task-type，可考虑在 evolution/scenarios 增量补一个场景规格。
- 残留风险：
  - 已覆盖：iOS 特有 git 战术的 owner 缺口（git_workflow.md + ROUTE-020）；SwiftUI propertyWrapper / DI / 并发模型选型碎片化（code_templates.md 3 节）。
  - 未覆盖：依赖管理（SPM ↔ Pods 冲突仲裁 / 二进制依赖）、安全/隐私（Keychain / Privacy Manifest）、数据持久化决策、推送/后台、本地化 —— 属于 P1/P2 缺口，待用户场景频次决定是否补。
  - 残留风险：git_workflow.md 中的部分团队约束（pbxproj PR 串行、storyboard 单 owner）是建议而非强制规则，落地需要团队达成共识；本 skill 只给建议，不强制。
  - 残留风险：propertyWrapper 选型表覆盖 iOS 17 Observable 宏，但若 iOS 18+ 新增包装器或语义变更，需更新；当前 last-verified 2026-06 仍在 12 个月新鲜度窗口内。

## 状态
- promoted
