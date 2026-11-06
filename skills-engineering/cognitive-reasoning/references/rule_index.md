<!-- last-verified: 2026-11 -->
<!-- owner: cognitive-reasoning -->
<!-- sha256: 25bf9f93e6e2a5224d41def8fac522d021f8e1777c2c78738a5c21efb89c32a4 -->

# 规则索引（cognitive-reasoning）

> 本文件为 `cognitive-reasoning` skill 拥有规则 ID 的**唯一定义真值**。
> 机械校验（scripts/validate-skill-behavior.sh Check 2）要求：SKILL.md 声明 ID ↔ 本文件 active 行**双向一致**，且定义锚点格式为 `## ID` / `[ID]` / `| ID |` 之一。
> 规则 ID 全球唯一；本条文件内 ID 与任何其它 skill 不重复。

## 认知对手模式（CAM，Tier 2，平台无关真值 owner）

- [CAM-001] 反迎合激活：适用场景命中时必须启用认知对手模式，不得跳过 Step。
- [CAM-002] 机械步骤：严格按 Step 0 → Step 6 执行，不得跳步。
- [CAM-003] 输出 schema：固定字段（复述/最强反驳/隐藏假设/失效条件/可证伪条件/立场翻转/迎合自检/置信度/结论）。
- [CAM-004] 禁止行为：禁止先肯定后弱反驳结构、禁止无依据置信。
- [CAM-005] 置信天花板：>70% 但给不出可证伪条件即违规。

真值细则见 [cognitive_adversary_mode.md](cognitive_adversary_mode.md)。

## 论证纪律（GR-010）

- [GR-010] 可追溯逻辑链 / 事实推断分层 / 置信匹配 / 逻辑链块（细则见 [logical_reasoning.md](logical_reasoning.md)）。

## 真值接地（GR-011 ~ GR-013）

- [GR-011] 反幻觉接地：未验证内容不得当已知陈述。
- [GR-012] 验证方法论：现实为裁判、验证非知道答案、优先可证伪。
- [GR-013] 求真方法边界：事实/推理分流、校准替代去情绪。

细则见 [epistemic_integrity.md](epistemic_integrity.md)。

## 认知拓展（CE-001 ~ CE-013，Tier 0/3）

- [CE-001] Tier 0 触发门控：有判断成分 + 能产出可证伪盲区，二者同时命中才追加；否则静默。
- [CE-002] 重框：提升为更一般的判断/学习问题；执行任务写「重框略」。
- [CE-003] 盲区：1 条具体隐藏假设/误区，须可检验；写不出够格盲区则整段不写（硬门）。
- [CE-004] 邻域：1 条相邻领域机制相关对照，禁止同技术栈换词重复主文。
- [CE-005] 带走：1 条可复用自检问句/if-then 规则，禁止鸡汤。
- [CE-006] Tier0-Tier2 互斥：Tier 2 命中时用认知对手完整结构，不另输出 Tier 0 尾注；该互斥同时扩展到 preamble 轻量校准段（D1）。
- [CE-007] 心智模型：深潜时给模型名 + 1 句如何用于本问题。
- [CE-008] 跨域类比护栏：机制对齐、点名被映射机制、禁陈词/换词类比。
- [CE-009] 验证动作：深潜给 7 天内可做的 1 个具体动作。
- [CE-010] 迎合自检：写完过三问（邻域非换词 / 带走非鸡汤 / 盲区可证伪）。
- [CE-011] 跳过条件：用户「只要答案/不要延伸」或门控未命中即不写 Tier 0。
- [CE-012] 邻域对照池：从对照池任选 1 条且须与机制相关。
- [CE-013] 去重：Tier 0 尾注不得与同轮 cognitive-reasoning 逻辑链（GR-010）重复维度。

细则见 [cognitive_expansion.md](cognitive_expansion.md)；形态校准见 [examples.md](examples.md)。

## 跨 skill 元数据字段说明

`engineering-discipline`、`problem-analysis`、`doc-hygiene`、`learning-loop` 等 skill 的 `references/rule_index.md` 用表格登记 `owner / scope / phase / precedence / conflicts_with / merges_into / field_owner` 七列，并注明"字段语义见本文件"。以下为这七列的权威定义：

| 字段 | 含义 |
|------|------|
| `owner` | 拥有该规则条文真值的 skill 名，与其 SKILL.md frontmatter 一致。 |
| `scope` | 规则适用范围；当前所有登记规则均为 `global`（不限平台/语言）。 |
| `phase` | 规则在构造回复过程中所处阶段：`timing`（触发/时序门控）、`structure`（输出结构/格式）、`evidence`（证据与推理约束）、`safety`（安全与授权边界）。 |
| `precedence` | 与 `conflicts_with` 指向的规则比较优先级的数值，数值越大越优先；`.agents/composition.md`「冲突裁决」把"安全 > 真相 > 问题 > 结构"的文字顺序落到可比较数字时使用。仅当 `conflicts_with` 非空、确有同处内容的冲突要求时才参与裁决；数值目前按各 skill 内部相对顺序设定，未建立跨 skill 统一刻度，新增规则沿用同 `phase` 内邻近规则的数量级即可，不要求与其它 skill 同名 `phase` 的数值直接可比。 |
| `conflicts_with` | 本规则与哪些其它规则 ID 可能就同一处内容给出冲突要求；当前所有登记规则均为 `[]`（尚无已登记的冲突对）。 |
| `merges_into` | 本规则的输出字段最终并入哪个机械块（如 `逻辑链`/`验证锚点`/四段式）；当前为保留列，所有登记规则均为 `[]`——多块合并的具体对应关系仍以 `engineering-discipline` GR-004「多块合并」的散文表述为准，尚未逐条登记到本列。 |
| `field_owner` | 当某机械块的具体字段（如"已覆盖"/"真实需求"）由某条规则独占命名权时，以 `{字段名: owner-skill}` 登记；无独占字段的规则登记为 `{}`。 |
