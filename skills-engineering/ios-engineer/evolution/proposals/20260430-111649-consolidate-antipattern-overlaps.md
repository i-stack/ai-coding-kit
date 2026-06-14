# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-111649-consolidate-antipattern-overlaps
- Created At: 2026-04-30 11:16:49 +0800
- Active Version At Creation: v12

## 问题信号
- `anti_patterns.md` 是"反模式库"的主归属文件，但 `root_cause_enforcement.md` 的"伪修复禁令"和 `swift_concurrency.md` 的"高风险信号"与其存在直接内容重复：
- root_cause_enforcement.md "伪修复禁令"（6 条）中 4 条与 `anti_patterns.md` 第 6 节"排障反模式 - 补丁式修复"和第 2 节"并发反模式 - DispatchQueue.main.async 掩盖时序"重复：
  - "新增兜底 `if`" = anti_patterns "补丁式修复 - 增加 `if`、延迟、重载、兜底分支压住问题"
  - "`DispatchQueue.main.async` / `asyncAfter` 拖延时序" = anti_patterns "DispatchQueue.main.async 掩盖时序问题"
  - "多写一层容错分支但不解释结构原因" = anti_patterns "补丁式修复" 核心语义
  - "靠重试、延迟、判空碰运气" = anti_patterns "补丁式修复" 核心语义
- swift_concurrency.md "高风险信号"（5 条）中 2 条与 `anti_patterns.md` 重复：
  - "用 DispatchQueue.main.async 掩盖真正的时序问题" = anti_patterns "DispatchQueue.main.async 掩盖时序问题" 原文
  - "为了通过编译随意加 nonisolated、@preconcurrency、@unchecked Sendable" = anti_patterns "滥用 @unchecked Sendable" 核心语义
- 同一条反模式（例如 `DispatchQueue.main.async` 掩盖时序）在 3 个文件中各写一次，读者加载任一文件都要重新处理同样信息；修改规则时也必须 3 处同步。

## 变更类型
- 合并重复：以 `anti_patterns.md` 为反模式单一归属；`root_cause_enforcement.md` 和 `swift_concurrency.md` 退役重复条款，只保留各自领域独特专项 + 追加交叉引用。

## 变更内容
- 修改文件：`references/root_cause_enforcement.md`
  - "伪修复禁令" 小节（共 6 条）：
    - 退役第 1 条 "新增兜底 `if`"（重复 anti_patterns 补丁式修复）。
    - 退役第 2 条 "`DispatchQueue.main.async` / `asyncAfter` 拖延时序"（重复 anti_patterns）。
    - 退役第 5 条 "多写一层容错分支但不解释结构原因"（重复 anti_patterns 补丁式修复）。
    - 退役第 6 条 "靠重试、延迟、判空碰运气"（重复 anti_patterns 补丁式修复）。
    - 保留第 3 条 "反复 `reloadData`、`setNeedsLayout`、`layoutIfNeeded`"（iOS UI 排障唯一专项）。
    - 保留第 4 条 "增加临时布尔标记位压住现象"（排障唯一专项）。
    - 小节末尾追加交叉引用："更广泛的排障反模式（现象即根因、补丁式修复）参考 [anti_patterns.md](anti_patterns.md) 第 6 节。"
- 修改文件：`references/swift_concurrency.md`
  - "高风险信号" 小节（共 5 条）：
    - 退役第 4 条 "用 DispatchQueue.main.async 掩盖真正的时序问题"（重复 anti_patterns 原文）。
    - 退役第 5 条 "为了通过编译随意加 nonisolated、@preconcurrency、@unchecked Sendable"（重复 anti_patterns "滥用 @unchecked Sendable"）。
    - 保留第 1 条 "在非主隔离域修改 UI 相关状态"（并发隔离专项，anti_patterns 未覆盖）。
    - 保留第 2 条 "多个任务竞争写同一份可变数据"（并发竞争专项，anti_patterns 未覆盖）。
    - 保留第 3 条 "任务取消后仍回写 UI"（过期回写专项，anti_patterns 未覆盖）。
    - 小节末尾追加交叉引用："更广泛的并发反模式（散落式 Task、滥用 @unchecked Sendable、DispatchQueue.main.async 掩盖时序）参考 [anti_patterns.md](anti_patterns.md) 第 2 节。"
- 替代或合并旧规则：
  - 被退役的 6 条（root_cause 4 条 + swift_concurrency 2 条）全部由 `anti_patterns.md` 承担，不丢失任何约束。
  - 两个 ref 的小节保留领域唯一条款，作为"细化加强" 而不是"完整清单"。

## 预期收益
- 反模式规则的归属统一：anti_patterns.md 成为反模式库的唯一完整来源；root_cause_enforcement.md 和 swift_concurrency.md 只保留各自领域的专项增强。
- 未来修改反模式规则时不再需要 3 处同步，降低规则不一致的维护风险。
- root_cause_enforcement.md 和 swift_concurrency.md 文件瘦身（各减 2-4 条），读者加载这两份文件时不再重复处理同样反模式。
- 两个 ref 新增的交叉引用让读者知道"还有更多反模式可参考"，避免错过完整视图。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响（本提案不引入新章节）。
- 场景回放：
  - 场景 `concurrency`：用户输入"搜索页快速输入结果串线"。期望 AI 读 swift_concurrency.md 命中"任务取消后仍回写 UI"（保留专项）+ 按交叉引用可访问 anti_patterns.md 的完整反模式库。
  - 场景 `layout`：用户输入"消息气泡高度偶发错误..."。期望 AI 读 root_cause_enforcement.md 命中"反复 reloadData / setNeedsLayout / layoutIfNeeded"（保留专项）。
- 残留风险：
  - 交叉引用只单向（root_cause → anti_patterns、swift_concurrency → anti_patterns），anti_patterns.md 不反向提示；但 anti_patterns.md 本身是完整清单，不需要反向指回专项文件。
  - 其他 ref（networking_patterns、performance_optimization、team_collaboration 等）也有各自的"常见反模式"小节；本提案不处理它们。若后续发现类似重复，单独提案。

## 状态
- promoted
