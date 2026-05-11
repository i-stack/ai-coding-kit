# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260509-105234-hit-rules-external-linter-script
- Created At: 2026-05-09 10:52:34 +0800
- Active Version At Creation: v63

## 问题信号
- usage_ledger.md §7 已显式承认 "三端 audit 块由 LLM 自评，存在 self-grading 偏差—data 应被视作有偏的草稿"，并把权威性外推给 validation_scenarios + scenario JSON 回放。但回放成本高，不适合每次 audit 后做轻量校验。
- 至 v63，IR-002 / IR-006 / IR-008 都已落到模板硬字段（前置确认 / 版本前提 / 残留风险声明），文本中存在稳定 anchor。这些 anchor 让"模型自报 hit-rules: IR-006"是否真的成立可外部机械验证——但当前没有脚本做这件事。
- 缺口：模型可以在 audit 块里写 `hit-rules: IR-006`，但实际响应里压根没有"版本前提"段落，ledger 仍正常入账，污染下游聚类。

## 变更类型
- 新增能力（增加一个外部 linter 脚本，对 audit 块声明的 hit-rules 与响应文本做模板字段对账；不改任何规则 ID、不改输出模板）

## 变更内容
- 修改文件：
  - scripts/lint_hit_rules.sh（新增）：读入 transcript 文件，对每个 `<usage-audit>` 块的 `hit-rules` 列表做以下检查：
    - 把当前 audit 块之前、上一个 audit 块结束之后（首块则文件起点）的文本视为"该次响应正文"。
    - 对每个声明的 rule_id 查 SIGNALS 表：
      - IR-001：响应正文含中文字符（`\p{Han}`）。
      - IR-002：响应正文含独立的 `^前置确认\s*$` 段标题。
      - IR-004：响应正文同时含四段式 4 个独立段标题（结论 / 为什么 / 修法 / 验证），或 findings-first 5 段（审查结论 / 严重问题 / 一般问题 / 验证缺口 / 最终要求）。
      - IR-006：响应正文含独立的 `^版本前提\s*$` 段标题。
      - IR-008：响应正文同时含 `残留风险声明` + `已覆盖` + `未覆盖` + `残留风险` 4 个 anchor。
    - 其它 rule_id（IR-003 / IR-005 / IR-007 / 全部 SYM / ROUTE / OUT）一律标 `UNSUPPORTED`，不计入 PASS / FAIL。
    - 输出每行一条 `[PASS/FAIL/UNSUPPORTED] task-type rule-id: 描述`，结尾打印 `PASS=N FAIL=M UNSUPPORTED=K`。
    - exit code：`FAIL > 0` 非零退出，否则零（UNSUPPORTED 不计为失败）。
  - references/usage_ledger.md：
    - §7 self-grading 偏差告示节追加一段："轻量 self-grading 校验脚本：[scripts/lint_hit_rules.sh](../scripts/lint_hit_rules.sh)。对 IR-002 / IR-004 / IR-006 / IR-008 等已落模板硬字段的 IR，可外部机械验证 audit 块声明的 hit-rules 是否在响应正文里真的有锚点；UNSUPPORTED 项不视为失败。本脚本是 ledger 数据可信度的一道前置过滤，不替代 validation_scenarios 回放——后者仍是命中率的最终权威。"
- 替代或合并旧规则：本提案不替代任何 ID；usage_ledger.md §7 原有"data 应被视作有偏的草稿，真正可信靠 validation_scenarios"的口径保留，本次只追加一道前置过滤工具。

## 预期收益
- ledger 入账前可加一道轻量过滤：模型自报 hit-rules: IR-006 但响应里没有版本前提块时，能立刻发现并修正 audit 块（或推回让模型补块）。
- IR-002 / IR-006 / IR-008 三条已模板字段化的 IR 命中率从"完全靠模型自评"过渡到"模型自评 + 文本锚点对账"，self-grading 偏差显著下降。
- 给后续模板字段化的 IR（如 IR-005 若未来有"修复范围"块）提供可扩展的检查表入口（直接往 SIGNALS 表加一条）。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 脚本自验：用一段构造的 transcript（含 1 个含版本前提的响应 + 1 个不含版本前提但声明 hit IR-006 的响应）跑脚本，验证前者 PASS、后者 FAIL，UNSUPPORTED 不计失败。
- 场景回放：6 场景结构校验。本提案不改输出行为、不改路由识别条件、不改 IR 定义；6 场景通过条件不变。
- 残留风险：
  - SIGNALS 表是基于当前模板字段化锚点（前置确认 / 版本前提 / 残留风险声明 / 四段式 / findings-first）写死的；任一 anchor 字面被改名（如 "版本前提" → "运行时假设"），脚本会错判 FAIL。anchor 变更已被 rule_index.md 跨文件共享概念表的修改协议捕获，但 SIGNALS 表本身没在该索引里。**本提案补强**：在跨文件索引里把 scripts/lint_hit_rules.sh 列为"版本前提声明 / 前置确认块 / 残留风险声明"三个概念的引用位置，确保 anchor 改名时同步更新脚本。
  - IR-001 检查"含中文字符"过宽：响应正文里有任何中文都视为 PASS，无法防"全英文回答但混入一两个中文标点"的退化。可接受现状，作为该 IR 的最弱信号。
  - 当前不支持 ROUTE / OUT / SYM 的命中检查（这些靠 ref 选择，不在响应文本里留稳定锚点）；UNSUPPORTED 可能占大头。脚本对这部分给出明确"不可验证"信号而非误判。

## 状态
- promoted
