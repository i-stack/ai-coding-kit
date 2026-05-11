# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-145745-enforce-reference-target-verification
- Created At: 2026-04-30 14:57:45 +0800
- Active Version At Creation: v29

## 问题信号
- v26 引入的 AA 规则（"跨文件 grep"约束）在最近一次验证中暴露一个盲点：
  - AA 要求"grep 该概念的所有出现位置"——防住"改 A 漏改 B"类问题（✓ 对 Issue 1/2 有效）。
  - AA **没要求**"验证引用目标内容是否真的存在"——防不住"引用指向不存在内容"的 dead reference 问题（✗ Issue 3 未被防住）。
- 具体证据：Proposal DD Issue 3：
  - Proposal CC（v28）把 performance_optimization.md 的"常用工具"小节退役，改为 `见 observability_logging.md "性能观测"`。
  - CC 写这行引用时，没有先验证 observability_logging.md "性能观测" 是否实际包含完整工具清单（Time Profiler / Core Animation / Allocations / Leaks / Memory Graph 等）。
  - 实际 observability 只点名了 OSLog / Points of Interest / MetricKit 三个，其他 6 个工具从未被写入目标文件。结果形成 dead reference（引用指向不存在内容）。
  - Proposal DD 才补齐工具用途到 observability，使引用变为有效引用。
- 这类问题的根因：提案作者在"退役 A + 引用 B"时，假设 B 已经包含被引用的内容，没有实际打开 B 确认。当 B 的内容是期望"新增"而不是"已有"时，就会留下 dead reference。
- 符合 self_evolution.md 触发信号："某条规则在真实任务里持续带来误导、过度展开或错误约束"（AA 规则缺失"引用目标验证"导致 CC 类 dead reference 发生后才被发现）。

## 变更类型
- 新增能力：在 `self_evolution.md` 补强 AA 规则——要求"使用跨文件引用时必须验证引用目标内容是否实际存在"。

## 变更内容
- 修改文件：`references/self_evolution.md`
  - 在 "候选版约束" 节，紧接 AA 规则（跨文件 grep）之后新增一条 EE 规则：
    ```
    - 提案中使用"见 X 文件某节"这类跨文件引用时，必须先打开 X 文件该节确认实际包含被引用的内容；不得引用"未来意图承担但当前缺失"的内容。若引用的内容在目标文件尚不存在，要么同时在本提案中补齐目标文件内容，要么在提案"变更内容"中显式标注 "需配合另一提案补齐目标文件 X 的某节"，不得单独提交。
    ```
  - 在 "明确禁止的模式" 节，紧接 AA 禁止模式之后新增一条：
    ```
    - 使用跨文件引用（"见 X 文件"、"详见 Y"、"按 Z 执行"）时，未验证目标文件实际包含被引用内容就提交候选版（dead reference）。
    ```

## 替代或合并旧规则
- 不退役任何现有规则。EE 是对 AA 的补强——AA 防"grep 漏位置"，EE 防"引用目标不存在"。
- 两条规则协同：AA 保证横向（所有引用点被改到）；EE 保证纵向（每条引用点指向真实存在的内容）。

## 预期收益
- 消除 Proposal CC 类 dead reference 问题的复发：未来"退役 A 改为引用 B" 时强制验证 B 包含该内容。
- 审查提案时可明确判定："你退役了 A 但没在 B 补上对应内容，按 EE 拒绝"。
- AA + EE 协同覆盖跨文件改动的两类主要失误（grep 漏位置 + 引用目标缺失）。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 本提案修改的是 `self_evolution.md` 自身，属于流程元规则变更；使用 `review` 场景作为代理，验证新增规则不阻塞常规审查任务。
  - 真实验证要到下一次"退役 A 改为引用 B" 类提案时才能观察是否生效。
- 残留风险：
  - EE 仍依赖提案作者按文字要求执行验证，无自动拦截。后续可在 `scripts/validate_skill_proposal.sh` 增加"解析提案中的引用，对每个引用跑 grep 确认目标文件实际包含该关键词"的自动检查。该脚本改动超出本提案范围，记录为后续候选。
  - "引用目标内容是否存在"的判断是语义判断，不是字面匹配。例如 CC 引用 "见 observability 性能观测" 期望的是"工具用途"，而 observability 该节有"性能观测"小节但内容不匹配；需要提案作者理解被引用内容的语义要求，不能仅靠 grep 关键词存在。

## 状态
- promoted
