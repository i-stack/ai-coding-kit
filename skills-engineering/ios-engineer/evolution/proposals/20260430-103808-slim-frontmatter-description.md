# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-103808-slim-frontmatter-description
- Created At: 2026-04-30 10:38:08 +0800
- Active Version At Creation: v8

## 问题信号
- SKILL.md frontmatter description 长达 475 字符，远超 skill router 匹配习惯长度（通常 < 200 字符）。
- 触发关键词（iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM）散落在 "Production-grade iOS engineering skill for..." 形容词短语之后，router 首读命中效率低。
- 描述中 "Production-grade"、"Use when Codex needs to analyze or implement changes in an iOS codebase, review PRs, design modules, debug crashes or layout/concurrency/performance issues, plan migrations, or produce production-ready Swift code" 是模板式填充短语，不构成差异化信号。
- 结尾 "Respond in Simplified Chinese" 属于行为规则，不应在 router 匹配输入中。行为规则应在 SKILL 正文（核心铁律已有此规则）。

## 变更类型
- 修正表达：精简 frontmatter description 到 router 友好长度，前置核心触发词，移除行为规则。

## 变更内容
- 修改文件：`SKILL.md`
  - frontmatter `description` 改为更紧凑、触发词前置的版本。
  - 原版（475 字符）：
    ```
    Production-grade iOS engineering skill for Swift, SwiftUI, UIKit, modular architecture, state modeling, Swift 6 concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing, and release risk control. Use when Codex needs to analyze or implement changes in an iOS codebase, review PRs, design modules, debug crashes or layout/concurrency/performance issues, plan migrations, or produce production-ready Swift code. Respond in Simplified Chinese.
    ```
  - 新版（目标 < 200 字符，核心触发词前置）：
    ```
    iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering: architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing. Covers design, implementation, and production risk control.
    ```
- 替代或合并旧规则：
  - "Production-grade"、"Use when Codex needs to..." 模板式填充 → 退役，不带入新版。
  - "Respond in Simplified Chinese" → 退役；该规则已在核心铁律 L15 "始终使用简体中文" 完整定义，不在 frontmatter 重复。
  - 触发关键词从形容词短语后提到句首，让 router 第一个匹配点是具体技术栈关键词。

## 预期收益
- Frontmatter description 长度减少约 50%，router 命中更精准。
- 技术栈关键词前置（iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM），提高"用户问 Xcode 构建问题" 这类场景的命中率。
- 移除行为规则使 frontmatter 只负责"匹配 skill"，正文只负责"行为约束"，职责边界清晰。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter YAML 合法。
  - 行数 ≤ 500。
  - 引用的所有 `references/*.md` 文件存在。
  - 分层守卫不受影响。
- 场景回放：
  - 无新增场景；本提案只改 frontmatter，不影响任务内规则。回放 `review` / `layout` 等场景应与 v8 表现一致。
- 残留风险：
  - 移除 "Respond in Simplified Chinese" 后，router 若只看 frontmatter 判断回复语言可能误判。但实际上 skill 触发后会加载正文，核心铁律 L15 仍在，行为不变。
  - 精简后英文技术栈名称占比上升，中文 description 空间被压缩。若后续发现中文用户搜索不到（例如搜"崩溃调试"），可再补中文技术关键词。

## 状态
- promoted
