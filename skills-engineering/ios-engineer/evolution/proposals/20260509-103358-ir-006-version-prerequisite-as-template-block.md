# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260509-103358-ir-006-version-prerequisite-as-template-block
- Created At: 2026-05-09 10:33:58 +0800
- Active Version At Creation: v60

## 问题信号
- IR-006 现状是建议式约束："回答里必须出现一条显式的"版本前提"声明"，但没有把"声明"落到任何输出模板的固定字段，模型在执行时容易遗漏或把版本前提融进散文段，导致：
  - 无法机械校验是否遵守（不像 IR-008 三字段声明已经在 examples.md 各模板末尾以独立段落字面存在）；
  - 自评 hit-rules 时存在 self-grading 偏差，模型误报命中而实际产物未含版本前提；
  - 当下游回放场景（validation_scenarios.md 场景 3）需要核对时，找不到固定文字定位点。
- 横向对比 IR-008 治理：IR-008 的"残留风险声明"已在 examples.md L18 写死"必须作为独立段落字面存在，不允许把它们散写进"验证"段或合并成一段文字 —— 字段存在性需要可被机械校验"。IR-006 缺同等强度的字面化约束。

## 变更类型
- 修正表达（把 IR-006 的"必须声明"从描述式约束升级为模板硬字段；不新增能力、不退役旧规则、不改 ID 集合）

## 变更内容
- 修改文件：
  - SKILL.md：IR-006 文案在尾段追加一句："具体落点见 [examples.md](references/examples.md) §1/§2/§4/§5/§6 模板的"版本前提"块与 [review_checklists.md](references/review_checklists.md) §8 骨架的"版本前提"段；该段必须作为独立段落字面存在，不允许与"结论"或"为什么"合并。"
  - references/examples.md：
    - "## 使用规则" 节追加一条与 IR-008 同等强度的字面化约束："涉及并发 / 可用性 API / SwiftUI 行为 / 网络取消语义的输出，必须在"结论"段之前追加一个独立的"版本前提"块，二选一：写出工程读取的真值（如 `iOS 15.0 / Swift 5.9`），或显式假设值（如 `假设 iOS ≥ 15 / Swift ≥ 5.9，如不符请纠正`）。该块必须作为独立段落字面存在，不允许与"结论"或"为什么"合并、也不允许散写进散文（履行 IR-006）。"
    - §1 架构设计、§2 Bug 排查、§4 Swift 并发、§5 性能分析、§6 重构与迁移路线 五个模板各在"结论"段之上插入"版本前提"块。块字段：iOS / Swift 版本（真值或显式假设）。
    - §3 代码审查保持指向 review_checklists.md，不在本文件加块。
  - references/review_checklists.md：
    - §8 标准输出骨架在"审查结论"上方追加"版本前提"段，与 examples.md 同字段。
  - references/rule_index.md：
    - 铁律表 IR-006 行摘要列改为："涉及并发 / 可用性 API / SwiftUI 行为 / 网络取消语义的输出，"结论"前必须有独立"版本前提"块（真值或显式假设），字段存在性可机械校验"。
    - "## 跨文件共享概念索引" 表追加一行："版本前提声明（iOS / Swift 真值或显式假设）| owner: SKILL.md IR-006 | 引用位置: examples.md 使用规则 + §1/§2/§4/§5/§6 模板首段；review_checklists.md §8 骨架首段；validation_scenarios.md 场景 3 通过标准 | 修改协议: 改 owner 字面（如二选一表述）必须同步所有引用；新增模板必须同步插入"版本前提"块；该块作为独立段落字面存在不得合并入其他段。"
  - references/validation_scenarios.md：
    - 场景 3 通过标准末条措辞从"回答里显式出现版本前提..."改为"输出在"结论"段之前含独立的"版本前提"块（按 examples.md §4 模板），写出真值或显式假设（IR-006）"，与新模板字面对齐；失败信号同步加一句"未把版本前提作为独立块字面输出，仅在散文里隐含"。
- 替代或合并旧规则：本提案不替代任何 ID；只把 IR-006 的执行口径从"出现一条声明"收紧为"以独立模板块字面存在"，旧描述被新描述完全覆盖。

## 预期收益
- IR-006 落到独立模板块后，是否遵守可被机械校验（grep "版本前提" 段标题），与 IR-008 三字段声明同等可观测性。
- 减少模型 self-grading 偏差：自评 hit-rules: IR-006 时必须能在产物里指到字面块，否则不可声称命中。
- validation_scenarios.md 场景 3 等回放场景获得稳定文字定位点，下游 grader 对账成本降低。
- 与现有 IR-008 治理范式对齐，整套 IR 输出约束统一从"指令式"过渡到"模板字段式"。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 场景回放：6 场景结构校验；本提案行为面影响场景 3（并发状态错乱）的通过标准措辞，需要回放确认改后通过标准仍可执行。
- 残留风险：
  - 仅落到 5 个 examples.md 模板 + review_checklists.md §8；其它 ref（如 root_cause_enforcement.md / swift_concurrency.md 内嵌示例输出）未强制落块，靠"使用 examples.md 模板"间接覆盖。后续若发现 ref 内嵌输出绕过模板，需要再开提案。
  - "版本前提"段标题字面是机械校验的关键 anchor，未来重命名（如改成"运行时假设"）需要批量同步全部引用位置；rule_index.md 新增的修改协议条目会捕获该约束。

## 状态
- promoted
