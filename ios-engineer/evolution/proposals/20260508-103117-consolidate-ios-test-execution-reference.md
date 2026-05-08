# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-103117-consolidate-ios-test-execution-reference
- Created At: 2026-05-08 10:31:17 +0800
- Active Version At Creation: v35

## 问题信号
- `SKILL.md` 中新增了 `## iOS 构建与测试命令`，把具体 `xcodebuild` 命令直接放进主 skill。该内容属于测试执行细节，不属于主 skill 的分流和核心约束，增加了 `SKILL.md` 的上下文占用。
- 同一类验证命令已经存在于 `references/test_system_prompt.md` 的“推荐验证命令”中，形成了主 skill 与 reference 的重复定义。后续若命令规则调整，容易出现两处不一致。
- `test_system_prompt.md` 命名不准确：文件实际承载的是“构建测试体系、执行测试、分析失败、最小修复、回归验证”的流程，不是一次性 Prompt。
- 真实审查中已经暴露出命令表达需要持续打磨，例如 `.xcodeproj` 与 `.xcworkspace` 替换规则、iOS-only API 的平台验证规则。这类操作细节应该集中在测试执行 reference 中维护。

## 变更类型
- 合并重复：把 `SKILL.md` 中的 iOS 构建与测试命令合并到测试执行 reference。
- 修正表达：把 `Photos` 这类不够严谨的平台信号改为 `UIKit` / iOS-only API / 仅面向 iOS 的 framework。
- 退役规则：退役 `SKILL.md` 中独立的 `## iOS 构建与测试命令` 章节。
- 退役旧命名：将 `test_system_prompt.md` 重命名为 `test_execution_and_repair.md`。

## 变更内容
- 修改文件：
  - `SKILL.md`
    - 删除 `## iOS 构建与测试命令` 具体命令段。
    - 将输出模板中的测试执行入口从 `references/test_system_prompt.md` 改为 `references/test_execution_and_repair.md`。
  - `references/test_system_prompt.md` → `references/test_execution_and_repair.md`
    - 文件标题从 `测试体系与自动修复 Prompt` 改为 `测试执行与失败修复`。
    - 去掉整段 ```text Prompt 包装，改成可复用 reference 流程。
    - 新增/合并 `## 验证命令`，集中维护 iOS Simulator SDK 构建、测试、destination 查询和同名模拟器 UDID 选择规则。
    - 保留原有测试范围、测试质量、代码设计、执行流程、最终输出和工作原则。
- 替代或合并旧规则：
  - `SKILL.md` 的 `## iOS 构建与测试命令` → 合并到 `references/test_execution_and_repair.md` 的 `## 验证命令`。
  - `references/test_system_prompt.md` 的“推荐验证命令” → 被新的 `## 验证命令` 替代，覆盖 `.xcworkspace`、`.xcodeproj`、`-showdestinations`、`id=<SimulatorUDID>` 等更完整场景。
  - `test_system_prompt.md` 文件名 → 被 `test_execution_and_repair.md` 替代，避免把长期 reference 命名成一次性 prompt。

## 预期收益
- `SKILL.md` 回到“核心约束 + 任务分流 + 输出模板入口”的职责，不承载具体命令实现。
- iOS 测试执行命令只有一个维护位置，降低重复定义和规则漂移风险。
- 新文件名更准确表达职责，AI 在命中“执行测试并修复失败”任务时更容易理解该 reference 的用途。
- 测试执行 reference 同时覆盖 `swift test` 平台误用、workspace/project 差异、destination 精确选择，减少把环境命令错误误判为源码错误的概率。

## 验证
- 结构校验：
  - 已检查当前 `SKILL.md` 和 `references/` 下不再存在 `test_system_prompt` 或 `iOS 构建与测试命令` 旧入口残留。
  - 已确认 `SKILL.md` 新入口指向 `references/test_execution_and_repair.md`，目标文件已存在。
  - 历史快照和旧 proposal 中的 `test_system_prompt.md` 引用保留不改，作为历史记录处理。
- 场景回放：
  - 场景 `执行 iOS 测试并修复失败`：期望 AI 从 `SKILL.md` 输出模板入口读取 `test_execution_and_repair.md` + `testing_strategy.md`，并在 `## 验证命令` 中选择 iOS Simulator / 真机目标，而不是使用 macOS destination 或裸 `swift test` 作为最终验证。
  - 场景 `SPM 包依赖 UIKit 导致 swift test 报 no such module UIKit`：期望 AI 判断这是验证命令平台错误的高概率信号，改用 `xcodebuild build/test -destination 'platform=iOS Simulator,...'` 验证，而不是直接宣告源码在 iOS 下不可编译。
  - 场景 `只有 .xcodeproj 无 workspace`：期望 AI 将示例中的 `-workspace <App.xcworkspace>` 替换为 `-project <App.xcodeproj>`。
- 残留风险：
  - 当前只迁移 active skill 与 references，未批量重写 `evolution/history/` 和旧 proposals 中的历史引用。
  - 尚未运行自动演化校验脚本；本提案目前保持 `draft`，后续可补跑 `validate_skill_evolution.sh` 和 `validate_skill_proposal.sh` 后再推进状态。

## 状态
- draft
