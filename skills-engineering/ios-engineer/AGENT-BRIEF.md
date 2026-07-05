# ios-engineer Agent 调用指南

## 一句话描述

iOS / Swift / SwiftUI / UIKit / Xcode 工程全生命周期——架构、并发、网络、性能、崩溃调试、代码审查、重构、迁移与测试。

## 何时调用

代理应在以下任一场景自动加载本 skill：

| 触发信号 | 示例 |
|---------|------|
| 平台关键词 | iOS、iPhone、iPad、macOS (Catalyst)、Apple Watch、Apple TV、Xcode |
| 语言/框架关键词 | Swift、SwiftUI、UIKit、Objective-C、Combine、async/await |
| 问题类型 | 崩溃、Crash、内存泄漏、卡顿、布局错位、约束冲突 |
| 工程关键词 | CocoaPods、SPM、Carthage、Xcode build、TestFlight、App Store、WidgetKit、App Extensions、小组件 |
| 审查/迁移 | 代码审查(PR Review)、重构、迁移、架构升级 |

## 关键行为

1. **认知对手模式**：技术决策/架构取舍/根因归因时，严格按 `cognitive_adversary_mode.md` 执行 Step 0–6。
2. **版本前提**：涉及并发/可用性 API/SwiftUI 行为时，必须输出显式版本前提声明。
3. **任务分流**：按 ROUTE 表精确路由，默认只加载 2–4 份 reference，控制上下文规模。
4. **四段式输出**：根因 → 为什么 → 修法 → 验证。
5. **残留风险声明**：任何改动必须声明已覆盖/未覆盖/残留风险。

## 不调用的情况

- 非 Apple 平台开发
- 后端服务/API 实现
- Web 前端开发
- 通用 DevOps（Docker / Kubernetes / 非 iOS 相关 CI）
- 纯设计/UX 讨论
- 非技术内容

详见 `OUT-OF-SCOPE.md`。
