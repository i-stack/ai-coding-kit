# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260509-104944-ir-002-clarification-block-as-template-trigger
- Created At: 2026-05-09 10:49:44 +0800
- Active Version At Creation: v62

## 问题信号
- IR-002 当前是建议式约束："对描述不清、上下文不足或存在歧义的问题，先确认关键事实，不自行猜测"。但缺一个字面化锚点：
  - 模型实际行为常退化为"在散文里说一句'需要更多信息'然后继续给出半猜半证的方案"，而不是真的停下来追问；
  - root_cause_enforcement.md L49 已建议"提出 1 个最关键确认问题"，但表述偏抽象，没有维度示例；其它 ref 没有同等约束；
  - "前置求证"目前是模型可选行为，不是模板硬字段，无法机械校验；
  - 当用户给出模糊 prompt 时，模型倾向把"补齐信息"压力推回给用户而不是主动列出问题清单。
- 横向对比：IR-006 / IR-008 已分别落到模板硬字段（"版本前提"块 / "残留风险声明"三字段），均能机械校验。IR-002 缺等价机制。

## 变更类型
- 修正表达（IR-002 升级为模板字段触发；不新增 / 退役任何 ID；不改 ROUTE / OUT 集合）

## 变更内容
- 修改文件：
  - SKILL.md：IR-002 文案在尾段追加："判定信息不足时（典型触发：模糊措辞 / 未给机型与系统 / 未给复现条件 / 未说已尝试方案 / 未说受影响范围），必须以独立的"前置确认"块字面输出 ≥1 个具体问题，方可继续给出方案。仅在散文中提"需要更多信息"或"建议补充"视为违反本铁律。前置确认问题维度示例见 [root_cause_enforcement.md](references/root_cause_enforcement.md) §2 取证策略；架构 / 性能类按对应 ref 主读补完。能从工程或上下文读出的事实优先读，不要让用户重复输入。"
  - references/root_cause_enforcement.md：把 L48-49 的"取证策略"两条扩写为一个小节"前置确认问题维度"，列举排障类常见追问维度（机型 / iOS 系统版本 / 真机 vs 模拟器 / 复现频率与路径 / 已尝试方案 / 受影响范围与时间窗）；保留原"先提出 1 个最关键确认问题"的最小化纪律。
  - references/rule_index.md：
    - 铁律表 IR-002 行摘要列改为："描述不清 / 上下文不足 / 歧义时先以独立"前置确认"块字面输出 ≥1 个具体问题，不允许仅在散文里说'需要更多信息'"。
    - "## 跨文件共享概念索引" 表追加一行："前置确认块（IR-002 在信息不足时的字面化触发） | owner: SKILL.md IR-002 | 引用位置: root_cause_enforcement.md §2 取证策略"前置确认问题维度"小节 | 修改协议: 改 owner 字面（如触发条件枚举）必须同步 root_cause_enforcement.md 维度示例；新增追问维度示例由对应 ROUTE 主读 ref 承担，不写进 owner，避免 SKILL.md 维度膨胀；段标题"前置确认"是机械校验 anchor，重命名需批量同步全部引用位置。"
- 替代或合并旧规则：本提案不替代任何 ID；只把 IR-002 的执行口径从"先确认关键事实"收紧为"以独立前置确认块字面存在 ≥1 个具体问题"，旧描述被新描述完全覆盖。root_cause_enforcement.md L49 的"提出 1 个最关键确认问题"被扩写但保留原意。

## 预期收益
- IR-002 落到独立块后，可机械校验（grep "前置确认" 段标题 + 至少 1 个问题项），与 IR-006 / IR-008 同等可观测性。
- 减少"散文里说一句需要更多信息然后继续半猜半证"的退化路径。
- 排障类追问维度沉淀到 ref，模型在 ROUTE-001 任务下首步就有可复用问题清单，prompt 信息密度的优化压力部分从用户侧转移回模型主动行为。
- 与现有 IR 输出约束体系对齐（IR-002 / IR-006 / IR-008 全部模板字段化）。

## 验证
- 结构校验：scripts/validate_skill_evolution.sh + scripts/validate_rule_ids.sh + scripts/validate_scenario_specs.sh。
- 场景回放：6 场景结构校验。本提案影响"信息不足时"的触发，但场景输入都已足够明确（concurrency / layout / migration / parameter-pass-through / mcp-control / review 都有完整描述），不会触发前置确认块；6 场景的通过条件不变。
- 残留风险：
  - 仅在 root_cause_enforcement.md 写明排障类问题维度，架构 / 性能 / 重构类的追问维度没有就地落 ref；后续若发现这些 ROUTE 下的追问质量持续偏低，再开提案给对应 ref 各加"前置确认问题维度"小节。
  - "前置确认"段标题字面是机械校验 anchor，未来重命名（如改成"信息缺口"）需要批量同步 SKILL.md + root_cause_enforcement.md + rule_index.md 三处。
  - 前置确认块的"必要性"由模型自判（信息是否真的不足），存在 self-grading 偏差。模板字段化只能保证"判定信息不足时必须落块"，无法保证"该判定信息不足时一定判定到"。后续可在 usage_ledger 里加 deviation 信号观察。

## 状态
- promoted
