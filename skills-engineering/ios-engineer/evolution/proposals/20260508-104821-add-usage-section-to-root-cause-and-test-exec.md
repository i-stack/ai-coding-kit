# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-104821-add-usage-section-to-root-cause-and-test-exec
- Created At: 2026-05-08 10:48:21 +0800
- Active Version At Creation: v37

## 问题信号
- 架构体检（M2 路线图）指出 `references/` 下多份 ref 缺统一的段首"适用场景"段，读者从 SKILL.md 跳转进入后需要读完一定篇幅才能回判是否进对文件，拖慢 ref 加载预算。
- 实际复盘后确认缺段首的只有 `root_cause_enforcement.md` 与 `test_execution_and_repair.md` 两份文件：前者以"# 根因修复铁律"直接进入 `## 目录` 与 `## 核心原则`；后者以"# 测试执行与失败修复"直接进入 `## 项目背景`。两者都已有隐含的用途描述文本，只是没有被放在统一标题下。
- 其余 23 份 ref 都以 `## 适用场景` 或等价的 `## 使用规则` / `## 触发条件` 作段首。

## 变更类型
- 修正表达：把已有的隐含用途描述提升为显式 `## 适用场景` 段首，并小幅补齐"本文件不处理什么"的边界声明，减少跨 ref 混读。

## 变更内容
- 修改文件：
  - `references/root_cause_enforcement.md`
    - 在 `# 根因修复铁律` 与 `## 目录` 之间插入 `## 适用场景` 段：列出排障、代码审查中判定"伪修复"、改动前确认证据/边界/影响面/残留风险等典型任务。
    - 复用原第 9 行关于"只定义排障纪律、证据标准和伪修复禁令"的边界声明，把它收敛在 `## 适用场景` 段落内，并把"通用输出模板归 SKILL.md 核心铁律"、"工具预算归 mcp_control.md"写明，明确本文件不承担的职责。
  - `references/test_execution_and_repair.md`
    - 在 `# 测试执行与失败修复` 与 `## 项目背景` 之间插入 `## 适用场景` 段：列出构建 iOS 测试体系、测试驱动最小修复、iOS 专有平台验证三类任务。
    - 复用顶部关于"构建可靠测试体系"的描述作为目标声明；追加一句"本文件不承担测试层次与场景模板设计，那归 testing_strategy.md"，避免与 testing_strategy.md 的职责重复。
- 替代或合并旧规则：
  - 无规则替代；本次仅提升隐含表达的可见性，不修改规则本身。

## 预期收益
- 从 SKILL.md 症状导航跳入任一 ref 后，读者通过前 8–15 行就能回判是否进对文件。
- `grep -L "适用场景\|## 触发\|## 使用" references/*.md` 结果从 2 收敛到 0，为后续在 `validate_skill_proposal.sh` 中加入"新建 ref 必须有段首"的守卫断言打好事实基线。
- 两文件都显式写明"不承担"的职责，减少与 SKILL.md / mcp_control.md / testing_strategy.md 的跨 ref 内容重叠风险。

## 验证
- 结构校验：
  - `grep -L "适用场景\|## 触发\|## 使用" references/*.md` 的输出应为空。
  - `bash scripts/validate_skill_evolution.sh` 9/9 base + 5/5 behavior 全绿，特别是 `[5/9] Validate internal markdown links` 保证新增的跨 ref 引用链路有效。
- 场景回放：
  - 场景 `root-cause-entry-clarity`：用户以"这段代码疑似强解包 crash，能确认根因吗"这类请求触发 root_cause_enforcement.md 时，AI 读到 `## 适用场景` 即可确认进对文件，无需读完目录与核心原则再回判。
  - 场景 `test-execution-entry-clarity`：用户以"iOS 工程测试为什么一到 swift test 就报 no such module UIKit"这类请求触发 test_execution_and_repair.md 时，AI 读到 `## 适用场景` 的"iOS 专有平台验证"一条即可确认进对文件。
- 残留风险：
  - 本次只补两份 ref 的段首，不处理"新建 ref 必须有段首"的守卫断言；该守卫是后续 M2 或 M3 的独立提案范围。
  - 历史快照（evolution/history/v1..v37）中的 ref 文件不回补段首，作为历史记录保留，与现行规则不同步属预期行为。

## 状态
- promoted
