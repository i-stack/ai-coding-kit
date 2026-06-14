# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-105026-retire-circular-scope-rule
- Created At: 2026-04-30 10:50:26 +0800
- Active Version At Creation: v11

## 问题信号
- Proposal H 在 v10 引入的核心铁律 L10 "仅在用户明确要求处理 iOS 代码、iOS 架构设计、Swift / SwiftUI / UIKit 相关实现、Xcode 构建发布等 iOS 生态任务时生效；非 iOS 项目、平台横向对比（iOS vs Android 选型）默认不触发本 skill，若已触发应主动说明适用边界并退场" 是循环定义：
  - Skill 本身名为 `ios-engineer`，frontmatter description 已限定 iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM 生态。
  - Skill router 只在任务匹配该 description 时才加载本 skill；读者读到这条铁律的唯一前提就是"任务已被判定为 iOS 相关"。
  - 因此条款的前半句"仅在 iOS 时生效"永远为真，不可能触发；后半句"若误触发则退场"场景极少，真发生时 AI 的通用判断力足以识别并退场，不需要专门铁律。
- 这条铁律是为了解决"用户问 iOS vs Android 选型如何应对"而写，但那种问题属于 skill router 层判断，不是 skill 内部铁律层应当承担的职责。
- 循环规则占 1 行主文件空间，对 AI 行为无独立驱动力，符合 self_evolution.md "在真实任务里持续带来误导、过度展开或错误约束" 的退役信号。

## 变更类型
- 退役规则：移除循环自指的范围约束铁律。

## 变更内容
- 修改文件：`SKILL.md`
  - 退役核心铁律 L10（"仅在用户明确要求处理 iOS 代码..."整行）。
- 替代或合并旧规则：
  - 条款职责由 frontmatter `description` 承担（Proposal I 已把触发词前置，足以让 router 精准判断）。
  - 边缘场景退场（例如用户问跨端选型）属于 AI 通用识别能力范围，不需要在 skill 内部写单独铁律。

## 预期收益
- SKILL.md 从 48 行降到 47 行。
- 核心铁律从 9 条减到 8 条，剩余每条都在 skill 已被激活的前提下才有意义，消除循环定义。
- 读者进入 skill 后直接看到"已经在 iOS 语境"的约束集，不再被"先判断是否该用本 skill"的元规则干扰。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：退役 L10 后，AI 收到 "review 这个 iOS 改动" 时仍按核心铁律 + 任务分流 → review_checklists.md 执行，行为不变（因为 skill 已加载即意味着 iOS 语境）。
- 残留风险：
  - 若未来出现 skill router 误触发（例如用户问 Flutter 跨端但 skill 错误加载），退役后 AI 不再有"主动退场"的显式铁律提示。但这属于 router 层问题，应在 router 或 frontmatter 层面解决，不应由 skill 内部规则补偿。

## 状态
- promoted
