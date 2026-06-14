# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-114710-consolidate-delivery-and-param-duplicates
- Created At: 2026-04-30 11:47:10 +0800
- Active Version At Creation: v19

## 问题信号

### 交付要求（已覆盖 / 未覆盖 / 残留风险）在 4 处重复定义
- `SKILL.md` L15 "任何改动都必须声明「已覆盖、未覆盖、残留风险」"（核心铁律单一来源）
- `testing_strategy.md` L155 "每次交付都必须说明未覆盖风险"
- `testing_strategy.md` L12 / L28 / L59 模板中也出现 "未覆盖 / 残留风险" 字段
- `team_collaboration.md` L31 "PR 描述必须写清：背景、改动范围、风险、验证方式、未覆盖风险"
- `test_system_prompt.md` L80 "风险点：未覆盖路径、仍可能存在的边界风险、环境或 CI 风险、异步/并发/状态残留风险"

重复语义相近，措辞不一致（未覆盖风险 / 残留风险 / 未验证路径）。AI 在不同上下文读到不同措辞时可能当成不同规则机械叠加，输出重复 2-3 遍同一段声明。

### 参数透传规则在 architecture + review 重复完整语义
- `architecture_and_network.md` L32-37 "参数透传与数据来源" 完整规则（5 条）
- `review_checklists.md` L14 和 L23 两条检查项也把完整规则复述了一遍（只是加了问号变问句）：
  - L14 "新增字段、参数或状态是否已经沿完整调用链补齐真实数据来源，而不是只在局部声明变量或临时透传让当前代码通过？"
  - L23 "若新增值依赖上游透传，是否已经回溯到真实拥有者、构造点和映射层，而不是把中间层变成无语义的参数搬运站？"

问题：
- 检查项本应是短 "是/否" 过检点，现在把完整规则重写一遍。
- 后续修改 architecture 规则时 review_checklists 必须同步，维护成本 2 倍。

## 变更类型
- 合并重复：
  - 交付要求收敛到 SKILL.md 核心铁律单一定义，其他 ref 改为引用或简化措辞。
  - 参数透传完整规则只在 architecture_and_network.md 定义，review_checklists.md 改为短检查项（引用原规则）。

## 变更内容
- 修改文件：`references/testing_strategy.md`
  - L155 "每次交付都必须说明未覆盖风险" 退役（SKILL.md L15 已覆盖）。用"每次交付按 SKILL.md 核心铁律声明「已覆盖 / 未覆盖 / 残留风险」"一句引用替代，或者直接删除该行。本提案选择删除。
  - 不改动 L12 / L28 / L59 的模板字段（这些是输出模板的具体字段名，不是规则重复）。
- 修改文件：`references/team_collaboration.md`
  - L31 "PR 描述必须写清：背景、改动范围、风险、验证方式、未覆盖风险" 中的"未覆盖风险"字段保留（属于 PR 描述的字段要求，与 SKILL.md 输出铁律是不同场景，PR 描述是持久化产物）。不做改动。
- 修改文件：`references/test_system_prompt.md`
  - L80 "风险点：未覆盖路径、仍可能存在的边界风险、环境或 CI 风险、异步/并发/状态残留风险" 保留（这是 system prompt 内部对 AI 的字段要求，与 SKILL.md 铁律是执行时的 metadata 不是实时输出重复）。不做改动。
- 修改文件：`references/review_checklists.md`
  - L14 替换为短检查项：
    - 原：`新增字段、参数或状态是否已经沿完整调用链补齐真实数据来源，而不是只在局部声明变量或临时透传让当前代码通过？`
    - 改为：`新增字段 / 参数 / 状态是否已按 [architecture_and_network.md](architecture_and_network.md) "参数透传与数据来源" 完成链路检查？`
  - L23 替换为短检查项：
    - 原：`若新增值依赖上游透传，是否已经回溯到真实拥有者、构造点和映射层，而不是把中间层变成无语义的参数搬运站？`
    - 改为：`若新增值依赖上游透传，是否已回溯到真实拥有者 / 构造点 / 映射层？（详见 architecture_and_network.md "参数透传与数据来源"）`

## 替代或合并旧规则
- `testing_strategy.md` L155 完全退役，由 SKILL.md 核心铁律 L15 单一承担。
- `review_checklists.md` L14 / L23 的完整规则语义退役，由短检查项 + 引用承担；规则详细定义归 architecture_and_network.md。

## 预期收益
- "已覆盖/未覆盖/残留风险" 从 4 处重复定义变为 1 处权威定义 + 1 处 PR 描述字段（team_collaboration.md，职责不同）+ 1 处 AI 内部 prompt 字段（test_system_prompt.md，内部使用）。
- 参数透传规则从 architecture + review 双重定义变为 architecture 单一定义 + review 短检查项。
- AI 读 review_checklists.md 不再被"完整规则重述"当成新约束叠加，输出更简洁。
- 修改参数透传规则或交付要求时不再需要 2 处同步。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500（本提案不改 SKILL.md）。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入"review 这个改动"。期望 AI 按 findings-first（Proposal U）+ 最后声明已覆盖/未覆盖/残留风险（SKILL.md L15）；不重复输出 2-3 段相似的"风险"声明。
  - 场景 `parameter-pass-through`：用户输入"新增 currentModel 字段 A 类里拿不到"。期望 AI 读 architecture_and_network.md 完整规则；如果任务涉及 review，读 review_checklists.md 短检查项 + 按引用回到 architecture 详细规则。
- 残留风险：
  - team_collaboration.md 和 test_system_prompt.md 中的"未覆盖风险"字段保留，与 SKILL.md 核心铁律有字面重叠但语义不同（一个是规则、一个是字段），不强行收敛。若后续观察到 AI 仍然重复输出，单独再处理。
  - review_checklists.md 的短检查项依赖读者点进 architecture_and_network.md，如果用户只读审查清单可能错过细则；但这是交叉引用的正常代价，整体收益大于。

## 状态
- promoted
