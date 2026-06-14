# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-113828-review-finding-first-exception
- Created At: 2026-04-30 11:38:28 +0800
- Active Version At Creation: v18

## 问题信号
- SKILL.md 核心铁律 L12 "默认按'根因 -> 为什么 -> 修法 -> 验证'输出" 是"结论优先"（conclusion-first）。
- `examples.md` 第 3 节"代码审查答法"给的也是四段式（结论 / 为什么 / 修法 / 验证）。
- 但 `review_checklists.md` L74 "标准输出骨架" 给的是另一种结构：审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求（**findings-first**）。
- 审查场景的最佳实践是 **findings-first**：先让读者看到所有发现的问题按严重度排序，再给结论；结论优先会让"结论"脱离具体 findings 证据，降低审查可读性。
- 当前三处模板互相叠加，AI 在审查时可能：(a) 只用四段式，丢失 findings 分级；(b) 只用 findings-first 但不说根因为什么；(c) 混用两种结构导致输出混乱。

## 变更类型
- 新增能力：在 SKILL.md 核心铁律明确"审查场景是四段式例外"；在 examples.md 把"代码审查答法"对齐为 findings-first 结构。

## 变更内容
- 修改文件：`SKILL.md`
  - 修改核心铁律 L12：
    - 原：`默认按"根因 -> 为什么 -> 修法 -> 验证"输出；若任务命中长模板要求，四段式作为摘要层，详细模板作为附加层。`
    - 改为：`默认按"根因 -> 为什么 -> 修法 -> 验证"输出；若任务命中长模板要求，四段式作为摘要层，详细模板作为附加层。**代码审查 / PR Review 例外**：按 findings-first 结构输出（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求），详见 [review_checklists.md](references/review_checklists.md)。`
- 修改文件：`references/examples.md`
  - 修改 "3. 代码审查答法" 小节的输出结构（L66-83）：
    - 原四段式（结论 / 为什么 / 修法 / 验证）替换为 **findings-first** 结构：
      ```
      ## 3. 代码审查答法
      适用于：PR Review、方案 Review、重构 Review。

      输出结构（findings-first，与其他场景的四段式不同）：

      ```text
      审查结论
      - 不可合入 / 可修改后合入 / 可合入

      严重问题（按正确性 → 架构 → 并发 → 性能 → UI → 测试排序）
      1. 问题 1：描述 + 影响 + 修法
      2. ...

      一般问题
      1. ...

      验证缺口
      - 缺哪些测试或验证

      最终要求
      - 合入前必须完成什么
      ```

      执行要求：
      - 严重问题先于风格问题。
      - 正确性先于可读性。
      - 风险先于偏好。
      - 不在审查场景使用"根因 → 为什么 → 修法 → 验证"四段式；findings 本身已包含这些维度。
      ```
- 替代或合并旧规则：
  - 审查场景的输出结构从 examples.md 和 review_checklists.md 两处并存改为 examples.md 单一定义，review_checklists.md 的 "标准输出骨架" 与 examples.md 一致。
  - 四段式仍是默认，只在明确审查场景退让。

## 预期收益
- 审查场景的输出结构有明确单一来源，不再在四段式 vs findings-first 之间混乱。
- SKILL.md 核心铁律显式标注例外，避免 AI 机械套用四段式到所有输出。
- findings-first 让审查输出更贴近真实代码审查的组织方式：问题按严重度列出 → 再给结论 → 再要求验证补强。
- review_checklists.md 和 examples.md 对齐到同一结构，维护成本下降。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入"review 这个改动"。期望 AI 按 findings-first 输出（严重问题 → 一般问题 → 验证缺口 → 最终要求），而不是把代码审查当成排障问题套四段式。
  - 场景 `migration` / `parameter-pass-through`：期望 AI 仍按四段式输出，不受本例外影响。
- 残留风险：
  - SKILL.md 行数可能从 47 增加 1 行（核心铁律 L12 末尾追加例外说明）；仍远低于 500 行上限。
  - examples.md 改写后行数变化约 +5 行。
  - review_checklists.md L74 "标准输出骨架" 已经是 findings-first 结构，本提案不动该文件，只让 examples.md 对齐。

## 状态
- promoted
