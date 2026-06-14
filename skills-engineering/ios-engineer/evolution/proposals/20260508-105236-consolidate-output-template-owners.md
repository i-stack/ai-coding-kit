# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-105236-consolidate-output-template-owners
- Created At: 2026-05-08 10:52:36 +0800
- Active Version At Creation: v38

## 问题信号
- "四段式输出（根因 / 为什么 / 修法 / 验证）"与"findings-first 标准输出骨架（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）"是本 skill 的两个核心输出契约，但其规范定义在多个文件里重复落地，形成漂移风险：
  - `SKILL.md:12` 与 `SKILL.md:58` 都把 findings-first 的五段标签（"审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求"）写入正文，与 `review_checklists.md:76-92` 的 `## 8. 标准输出骨架` 构成重复定义。
  - `references/migration_strategy.md:114` 直接引用"严重问题 / 一般问题"两个具体小节名作为迁移额外检查项的归类标签，如果 review_checklists.md 后续调整小节命名会静默漂移。
  - `references/test_execution_and_repair.md:82` 使用 "根因、为什么、修法、验证方式" 的散文变体，与 SKILL.md 里 canonical 的 "根因 / 为什么 / 修法 / 验证" 命名不一致。
  - `references/self_evolution.md:70` 已经把"四段式输出 / findings-first 骨架"列入跨文件共享概念清单，但未标注 owner，后续校验脚本无法据此生成"非 owner 文件不得含完整定义"的断言。
- 架构体检 Top 5 风险 R4 明确要求本轮 M2 治理期完成 owner 化，防止任一非 owner 文件因误改导致五段标签或四段命名悄悄漂移。

## 变更类型
- 合并重复：把 findings-first 五段标签的唯一定义点锁定在 `references/review_checklists.md`；SKILL.md 与其他 ref 只能引用不得复述。
- 修正表达：统一 test_execution_and_repair.md 的四段式措辞为 canonical 的 "根因 / 为什么 / 修法 / 验证"。
- 新增能力：在 self_evolution.md 的共享概念清单里标注 owner，为未来在 validate_skill_evolution.sh 中加守卫断言打基线。

## 变更内容
- 修改文件：
  - `SKILL.md`
    - 第 12 行："代码审查 / PR Review 例外" 的括注从复述五段标签改为指向 owner，格式统一为 "见 [review_checklists.md](references/review_checklists.md) 第 8 节"。
    - 第 58 行输出模板条目同样移除括注里的五段标签复述，改为 "使用 [review_checklists.md](references/review_checklists.md) 第 8 节的 findings-first 标准输出骨架"。
  - `references/migration_strategy.md`
    - 第 114 行去掉 "迁移相关问题在'严重问题 / 一般问题'中按上述额外检查项命中与否分类" 里对两个具体小节名的硬引用，改为 "迁移相关的额外检查项按其严重级落入该骨架对应小节"。
  - `references/test_execution_and_repair.md`
    - 第 82 行把 "并输出根因、为什么、修法、验证方式" 对齐成 "并按四段式（根因 / 为什么 / 修法 / 验证）输出结论"，与 SKILL.md 核心铁律措辞一致。
  - `references/self_evolution.md`
    - 第 70 行 "常见跨文件共享概念举例" 的"四段式输出"和"findings-first 骨架"后面各追加 owner 标注 "（owner: SKILL.md 核心铁律）" / "（owner: review_checklists.md 第 8 节）"，把 owner 关系固化在规则条款里。
- 替代或合并旧规则：
  - 五段标签 "审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求" 只保留在 `review_checklists.md:76-92` 的 `## 8. 标准输出骨架` 中。
  - 四段式 canonical 措辞 "根因 / 为什么 / 修法 / 验证" 只由 SKILL.md 核心铁律定义，其它 ref 以引用或统一短语使用。

## 预期收益
- findings-first 五段标签与四段式命名的 owner 单点收敛，后续调整只改 owner 文件即可，不需要跨文件同步。
- `grep -nE "审查结论.*严重问题.*一般问题" references/*.md SKILL.md` 从多条收敛到仅 review_checklists.md 一处。
- self_evolution.md 显式标注 owner，为 M3 阶段在 `validate_skill_evolution.sh` 加 "非 owner 文件不得含完整定义" 的断言打好落点。
- 消除 test_execution_and_repair.md 里四段式的散文变体，降低 AI 对四段式措辞的漂移概率。

## 验证
- 结构校验：
  - `grep -nE "审查结论.*严重问题.*一般问题" SKILL.md references/*.md` 预计只命中 `references/review_checklists.md`。
  - `grep -n "根因、为什么、修法、验证方式" references/*.md` 预计为空（原 test_execution_and_repair.md:82 的散文变体已统一）。
  - `bash scripts/validate_skill_evolution.sh` 9/9 base + 5/5 behavior 全绿；特别是 `[4/9] Validate layering guardrails` 必须保持通过（本提案未改变分层责任，仅收敛 owner）。
  - `bash scripts/test_proposal_scripts.sh` 保持 Passed=39 Failed=0。
- 场景回放：
  - 场景 `findings-first-single-source`：在代码审查任务中，SKILL.md 的导航将用户指向 review_checklists.md；read 后读者能在第 8 节直接看到完整五段骨架；SKILL.md / examples.md / migration_strategy.md 中只有引用没有重复定义。
  - 场景 `four-stage-phrasing-canonical`：测试失败排障任务命中 test_execution_and_repair.md:82 时，AI 按 "根因 / 为什么 / 修法 / 验证" 输出结论，与 SKILL.md 核心铁律措辞一致，不再出现"验证方式"等散文变体。
- 残留风险：
  - `self_evolution.md:70` 的"网络链路 / 错误分层 / 状态分层 / 建模分层 / 日志分层 / 任务分流 / 术语定义" 还没标 owner，本提案暂不处理；这几个概念需要先分别盘点 owner 候选，属于 M2 后期或 M3 的独立提案。
  - 历史快照（evolution/history/v1..v38）不回改，保留 owner 化前的原貌作为历史记录。

## 状态
- promoted
