# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-183824-add-bidirectional-owner-boundary-statements
- Created At: 2026-05-08 18:38:24 +0800
- Active Version At Creation: v58

## 问题信号
- 架构审计指出三对 ref 文件主题重叠：架构对 / 测试对 / 审查对。每对中**仅一侧**有显式分工声明，另一侧无反向声明，使用者读"无声明那一侧"时不知道相邻文件是否承担互补职责。
- 现状：
  - `architecture_analysis.md` L10 已声明 "本文件只定义评估类输出..."；`architecture_and_network.md` 无反向声明。
  - `test_execution_and_repair.md` L9 已声明 "本文件不承担测试层次划分..."；`testing_strategy.md` 无反向声明。
  - `review_checklists.md` L74 (尾部) 已指向 anti_patterns.md；`anti_patterns.md` 无反向声明。

## 变更类型
- 修正表达（补齐三对重叠文件的双向 owner 边界声明；不动内容、不动 ID 集合）

## 变更内容
- 修改文件：
  - references/architecture_and_network.md：在 "## 适用场景" 节末追加一行声明："本文件承担**实施类**架构设计与改造写法。**评估类**输出（架构体检 / 健康度评分 / 系统性风险排查 / 重构路线图）归 [architecture_analysis.md](architecture_analysis.md)。"
  - references/testing_strategy.md：在 "## 使用规则" 末追加一行："本文件承担**测试规划**（层次划分 / 覆盖策略 / stub 设计）。**测试执行与失败修复**（跑测试 / 分析失败 / 平台验证排查）归 [test_execution_and_repair.md](test_execution_and_repair.md)。"
  - references/anti_patterns.md：在 "## 使用规则" 末追加一行："本文件是**反模式库**（识别条件 / 风险 / 修法）。**审查检查表与可合入判定**归 [review_checklists.md](review_checklists.md)；二者配合使用——审查时先按 review_checklists.md 维度过检，命中时回查本文件对应反模式条目。"
- 替代或合并旧规则：无；本提案只补缺，不动既有声明。

## 预期收益
- 三对重叠文件双向声明完备；读"无声明侧"时不再需要对照另一侧才能理解分工。
- 后续 grep "本文件不承担" / "本文件承担" 能稳定列出所有 owner 边界，便于自动化校验。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh。
- 场景回放：6 场景结构校验；本提案不改输出行为。
- 残留风险：每对的具体内容重叠未消除（如缓存策略在两侧讲法不同等具体重叠），仅做边界声明，重叠收紧留给后续提案。

## 状态
- promoted
