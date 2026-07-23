# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260723-152751-expand-description-platforms
- Created At: 2026-07-23 15:27:51 +0800
- Active Version At Creation: v73

## 问题信号
- 当前 `SKILL.md` frontmatter 的 `description` 仅是英文简略描述，覆盖
  `iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM` 与少量动词
  （architecture/concurrency/networking/performance/crash debugging/...）。
- 缺少对下列平台与技术栈的覆盖：iPadOS / macOS(Catalyst) / watchOS /
  tvOS、Objective-C / Objective-C++、Combine / async-await、Carthage /
  WidgetKit / App Extensions / TestFlight / App Store。
- 未表达中文诊断关键词（卡顿 / 启动慢 / 内存上涨 / 能耗异常 / 崩溃 / 闪退 /
  野指针 / EXC_BAD_ACCESS / 断言 / 布局错位 / 约束冲突 / 列表跳动 / 复用错乱 /
  无障碍 / 代码审查 / 重构 / 迁移）。导致技能在跨 Apple 平台与诊断场景下
  的可发现性与自动触发命中率不足。

## 变更类型
- 修正表达（frontmatter `description` 扩写，提升跨平台与诊断场景的触发覆盖）。

## 变更内容
- 修改文件：`skills-engineering/ios-engineer/SKILL.md`（仅 frontmatter `description` 一行）。
- 旧：
  `description: iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering - architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing. Covers design, implementation, and production risk control.`
- 新：
  `description: iOS / iPadOS / macOS (Catalyst) / watchOS / tvOS engineering with Swift, SwiftUI, UIKit, Objective-C, Objective-C++, Combine, async/await, Xcode, CocoaPods, SPM, Carthage, WidgetKit, App Extensions, TestFlight, App Store. Covers architecture, concurrency (actor / Sendable / @MainActor), networking, performance (卡顿 / 启动慢 / 内存上涨 / 能耗异常), crash debugging (崩溃 / 闪退 / 野指针 / EXC_BAD_ACCESS / 断言), UI & layout (布局错位 / 约束冲突 / 列表跳动 / 复用错乱 / 无障碍), code review (代码审查 / PR Review), refactoring (重构), migration (迁移 / 架构升级), testing. 设计、实现与生产风险控制。`
- 仅扩展描述文本，不替代或合并任何 body 规则；`references/` 未变动。

## 预期收益
- 提升 iOS-engineer 技能在跨 Apple 平台（iPadOS/macOS/watchOS/tvOS）、
  Objective-C/Objective-C++、Combine/async-await、WidgetKit/App Extensions 等
  场景下的自动触发命中率。
- 补充中文诊断术语，使中文工单/报错描述更易命中本技能。

## 验证
- 结构校验：`SKIP_SNAPSHOT_CONSISTENCY=1 bash scripts/validate_skill_proposal.sh evolution/proposals/20260723-152751-expand-description-platforms.md` → 预期 status=validated（纯 frontmatter 变更，不触碰 body 行为契约）。
- 场景回放：不适用（无 body 规则变更，无行为漂移风险）。
- 残留风险：无（仅元数据描述扩写，不影响任何 GR 规则或 behavior 校验字面串）。

## 状态
- approved
