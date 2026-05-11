# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-110854-require-version-baseline-confirmation
- Created At: 2026-05-08 11:08:54 +0800
- Active Version At Creation: v40

## 问题信号
- 架构体检 R5 指出本 skill 全库未声明 iOS SDK / Swift 版本基线：grep 全库无 "iOS 17"、"iOS 18"、"Swift 6"、"Swift 5.10" 等明确版本锚点。
- 实际工程的 Deployment Target 与 Swift 版本差异显著影响并发、可用性 API、SwiftUI 行为类建议的有效性：
  - Swift 6 默认严格并发检查，会让 `swift_concurrency.md` 中关于 `@MainActor`、`Sendable` 的若干建议从"推荐"升级为"必需"，反之亦然。
  - iOS 15 / 16 / 17 / 18 在 SwiftUI 状态、`Observable`、`Observation` 框架、`async let` 取消语义上行为差异明显。
  - `networking_patterns.md` 中的 `URLSession async/await` 与 `Task` 取消链路在 iOS 15 与 iOS 18 上 API 表面不同。
- 在没有显式版本基线声明的当前状态下，AI 容易用最近熟悉的 API 假设作为默认，输出会对低基线项目过激进、对高基线项目过保守。
- 经决策（2026-05-08）选择"不预设默认基线"路线：不写死任何具体 iOS / Swift 版本作为默认假设；改为约束每次进入版本敏感任务前必须先从工程读取实际基线，再给针对性建议。

## 变更类型
- 新增能力：在 SKILL.md 核心铁律新增一条"版本敏感建议必须先确认工程基线"的硬约束。
- 新增能力：在 execution_playbooks.md 使用规则段新增一条等价的剧本前置步骤，覆盖所有涉及并发 / API 选择 / SwiftUI 行为的剧本。
- 修正表达：在 ios_conventions.md 顶部声明本文件不预设 iOS / Swift 版本基线，所有版本相关建议必须由实际工程基线决定。

## 变更内容
- 修改文件：
  - `SKILL.md`
    - 在"核心铁律"段新增一条："涉及并发（`@MainActor` / `actor` / `Sendable` / `async let`）、可用性 API、SwiftUI 行为、网络取消语义的建议，输出前必须先从工程读取 `IPHONEOS_DEPLOYMENT_TARGET` 与 `SWIFT_VERSION`；版本未知时不得给具体 API 选择或并发模式建议，应先向用户或工程文件求证。本 skill 不预设默认基线。"
    - 该条放在"先给最小可验证修复"之后、"不要格式化代码"之前，与既有"先锁定主路径 / 最小修复优先 / 已覆盖未覆盖残留风险"等条目并列，不增加段落。
  - `references/execution_playbooks.md`
    - 在"使用规则"段最后追加一条："任何剧本若涉及并发模型、可用性 API、SwiftUI 行为或迁移建议，进入步骤 1 前必须先确认 `IPHONEOS_DEPLOYMENT_TARGET` 与 `SWIFT_VERSION`；版本未知时不得给具体 API 选择或并发模式建议。"
    - 不在 5 个剧本各自的 "步骤" 列表里重复追加 Step 0；保持单点声明。
  - `references/ios_conventions.md`
    - 在"使用规则"段最后追加一条："本文件不预设 iOS / Swift 版本基线；并发写法、可用性 API、SwiftUI 行为类约束的具体取舍由实际工程的 `IPHONEOS_DEPLOYMENT_TARGET` 与 `SWIFT_VERSION` 决定。版本敏感建议详见 SKILL.md 核心铁律。"
- 替代或合并旧规则：
  - 无规则替代；本提案是新增前置约束，与既有规则不冲突。

## 预期收益
- AI 在并发迁移、可用性 API 选择、SwiftUI 行为分析这三类版本敏感任务上不会再用过期或未来 API 假设代替工程实际基线。
- 把"先确认版本"作为强制前置步骤，消除"输出后才被用户指出基线不对、需要返工"的浪费。
- 通过"不预设基线"路线避免随版本演进周期性更新 SKILL.md 默认值——基线信息一直保留在工程本身，本 skill 只约束求证流程。

## 验证
- 结构校验：
  - `bash scripts/validate_skill_evolution.sh` 9/9 base + 5/5 behavior 全绿。
  - `grep -n "IPHONEOS_DEPLOYMENT_TARGET\|SWIFT_VERSION" SKILL.md references/*.md` 应在 SKILL.md、execution_playbooks.md、ios_conventions.md 三处命中。
  - `bash scripts/test_proposal_scripts.sh` 保持 Passed=39 Failed=0。
- 场景回放：
  - 场景 `concurrency-migration-asks-for-baseline-first`：用户请求"把这个 callback 接口迁移到 async/await"时，AI 应先要求用户提供或在工程中读取 Swift 版本（决定是否启用严格并发）与 Deployment Target（决定可用 API），再给具体迁移方案。
  - 场景 `availability-api-asks-for-baseline-first`：用户请求"用 `Observable` 框架重构 ViewModel"时，AI 应先确认 Deployment Target ≥ iOS 17（`@Observable` 引入版本），版本不足时给出 `ObservableObject` 替代或建议升级。
  - 场景 `swiftui-behavior-asks-for-baseline-first`：用户请求"为什么这个 SwiftUI 视图刷新过度"时，AI 应先确认 iOS 版本（iOS 17+ 的 `Observation` 框架与 iOS 16 及以下的 `ObservableObject` 触发模型不同），再分析。
- 残留风险：
  - 本提案约束的是输出行为，不是机器可验证的语法。`validate_skill_evolution.sh` 无法直接断言"AI 在版本敏感场景先求证"；该层约束的回归保护依赖未来在 `validation_scenarios.md` / 行为校验场景里加入显式断言，属后续提案范围。
  - 不预设基线意味着每次相关任务都需要一次额外的版本确认；在简单一次性问题上会有轻微交互开销，是为换取准确性付出的成本。

## 状态
- promoted
