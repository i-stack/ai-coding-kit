# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260430-141450-review-findings-first-consistency
- Created At: 2026-04-30 14:14:50 +0800
- Active Version At Creation: v23

## 问题信号
前面 Proposal U（v19 审查 findings-first 例外）和 Proposal W2（v22 命中维度过检）把审查场景的输出和过检规则调整了，但没有同步下游的判定条件、SKILL.md 输出模板、和其他 ref 的审查格式定义。留下 3 处不一致：

- **review_checklists.md 内部自相矛盾**：
  - L4-5（使用规则，W2 已改）："先识别命中哪些维度 ... 未命中维度显式标注 未涉及 或 无证据"
  - L69（可合入条件）："正确性、架构、并发、性能、UI、测试均过检" — 仍是全维度
  - 结果：局部改动（只命中 UI + 测试）的 PR 永远无法"可合入"，因为其他 4 维度被标为"未涉及"而不是"过检"，不满足 L69 条件。
- **SKILL.md L43 归类错误**：
  - L12（核心铁律，U 已改）："代码审查例外：按 findings-first 结构输出，详见 review_checklists.md"
  - L43（输出模板）："正式方案 / 审查结论 / 排障结论 / 迁移路线 / 性能分析的四段字段模板：examples.md"
  - 结果："审查结论"仍归在 examples.md 四段模板里，与 L12 的 findings-first 例外直接冲突。AI 读这两行会看到不一致。
- **migration_strategy.md L106 独立定义审查格式**：
  - "审查输出标准" 小节重新定义了"问题是什么 / 为什么是问题 / 影响范围 / 推荐修法 / 是否需要补测试"5 段格式，与 review_checklists.md 的 findings-first 标准输出骨架（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）不同。
  - 结果：做迁移审查时，AI 读到两套格式可能混用或犹豫。

## 变更类型
- 修正表达：把 review_checklists.md 的"可合入"条件与"命中维度过检"对齐；SKILL.md 输出模板拆分 findings-first 引用；migration_strategy.md 只保留迁移审查额外检查项，审查格式引用 review_checklists.md。

## 变更内容
- 修改文件：`references/review_checklists.md`
  - 修改 L69 "可合入" 条件：
    - 原：
      ```
      适用于：
      - 正确性、架构、并发、性能、UI、测试均过检
      - 剩余问题只属于低风险优化项
      ```
    - 改为：
      ```
      适用于：
      - 命中维度均过检；未命中维度已标注 未涉及 / 无证据
      - 无不可合入问题
      - 验证覆盖当前改动范围
      - 剩余问题只属于低风险优化项
      ```
- 修改文件：`SKILL.md`
  - 修改 "输出模板" L43 及新增一行：
    - 原 L43：`正式方案 / 审查结论 / 排障结论 / 迁移路线 / 性能分析的四段字段模板：[examples.md](references/examples.md)。`
    - 改为两行：
      - `正式方案 / 排障结论 / 迁移路线 / 性能分析的四段字段模板：[examples.md](references/examples.md)。`
      - `代码审查 / PR Review：使用 [review_checklists.md](references/review_checklists.md) 的 findings-first 标准输出骨架（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）。`
- 修改文件：`references/migration_strategy.md`
  - 退役 "审查输出标准" 小节（含 "审查结论格式" 子节，共约 13 行）。
  - 替换为迁移审查的额外检查项：
    ```
    ## 迁移审查额外检查项
    做迁移相关 PR 审查时，除 [review_checklists.md](review_checklists.md) 的 6 维检查外，补充以下迁移专项检查：
    - 是否按阶段拆分（建抽象 / 接兼容层 / 迁调用方 / 删旧实现 / 收口验证），而不是单次大变更？
    - 是否有兼容层且定义了生命周期（何时删除、删除前置条件）？
    - 是否明确灰度范围和回滚触发条件（Crash / 指标异常 / 业务失败率）？
    - 是否验证了新旧链路行为一致性？
    - 若涉及并发或状态模型迁移，是否专项验证取消、回写、隔离？

    审查输出格式：遵守 [review_checklists.md](review_checklists.md) 的 findings-first 标准输出骨架；迁移相关问题在"严重问题 / 一般问题"中按上述额外检查项命中与否分类。
    ```
- 替代或合并旧规则：
  - review_checklists.md 的 "可合入" 条件 L69 原全维度过检退役，替换为与 L4-5 "命中维度" 策略一致的版本。
  - SKILL.md L43 的 "审查结论" 归类退役，拆出专门的审查模板行指向 review_checklists.md。
  - migration_strategy.md 的独立 "审查输出标准" 退役，只保留迁移专项检查项，审查输出格式由 review_checklists.md 单一承担。

## 预期收益
- review_checklists.md 内部不再自相矛盾：只命中 UI 的 PR 可以合入，只要命中维度过检 + 其他维度正确标注。
- SKILL.md 输出模板与核心铁律 L12 一致，AI 读到时不会在 "四段式 vs findings-first" 之间犹豫。
- migration_strategy.md 不再独立维护一套审查格式；迁移审查和普通审查都用同一份 findings-first 模板，格式差异由"专项检查项"承担，不是格式重写。
- 3 处修正后，审查场景的规则、判定、输出格式全部指向 review_checklists.md 单一来源。

## 验证
- 结构校验：
  - `SKILL.md` frontmatter 合法，行数 ≤ 500。
  - `SKILL.md` 引用的所有 `references/*.md` 文件存在。
  - `root_cause_enforcement.md` / `examples.md` 分层守卫不受影响。
- 场景回放：
  - 场景 `review`：用户输入 "review 这个纯 UI 文案改动"。期望 AI 判 "命中维度：UI / 测试；未命中：正确性 / 架构 / 并发 / 性能"，命中维度过检无严重问题 → "可合入"，不再被 L69 全维度要求卡住。
  - 场景 `migration`：用户输入 "review 这次并发迁移 PR"。期望 AI 按 review_checklists.md findings-first 结构输出 + 迁移专项检查项命中与否，不再同时套用两套格式。
- 残留风险：
  - review_checklists.md L69 的 "验证覆盖当前改动范围" 是新增条件，依赖 AI 判断"改动范围"。如果后续观察到判断不稳定，单独提案加识别条件。
  - migration_strategy.md 保留 "迁移审查额外检查项"，如果未来发现这些检查项与 review_checklists.md 的 6 维某些条款重复，再单独合并。

## 状态
- promoted
