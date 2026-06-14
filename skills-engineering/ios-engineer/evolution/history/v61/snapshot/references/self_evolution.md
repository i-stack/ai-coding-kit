# Skill 自进化治理

## 目录
- 使用规则
- 触发信号
- 自进化闭环
- 候选版约束
- 自动验证门禁
- 晋升与回滚
- 规则 ID 治理
- 真实任务观测
- 明确禁止的模式
- 提案模板

## 使用规则
- 只有在真实任务中发现当前 skill 存在规则缺失、规则冲突、规则重复、规则失效或输出失真时，才使用本文件。
- 本文件定义的是 skill 的受控自进化流程，不是业务问题的答法模板。
- 默认生成候选改动并验证，不直接把未验证的规则改动当作新的生效版本。
- 任何新增或修改规则，必须说明它是在新增能力、修正表达、合并重复，还是退役旧规则；若不能说明替代关系，默认不新增。
- 版本状态保存在 `evolution/active_version.json`；提案、验证记录、授权记录、历史快照分别存放在 `evolution/proposals/`、`evolution/validations/`、`evolution/approvals/` 和 `evolution/history/`。

## 触发信号
以下信号满足任一条，就可以进入自进化流程：
- 同类问题连续出现，而现有规则没有覆盖。
- 现有规则可以覆盖，但表达不清，导致执行结果持续偏移。
- 多份文档对同一件事重复下定义，导致上下文膨胀或优先级冲突。
- 某条规则已经长期稳定命中，但仍在多个文档重复出现。
- 某条规则在真实任务里持续带来误导、过度展开或错误约束。

## 自进化闭环
固定按以下顺序推进：

1. 记录信号
- 问题现象是什么。
- 现有哪条规则没有命中，或命中了但方向不对。
- 这是缺能力、缺表述，还是重复定义。

2. 先判定变更类型
- 新增能力：当前 skill 确实缺少某类稳定规则。
- 修正表达：规则本身方向正确，但措辞或触发条件不清。
- 合并重复：多份文档重复定义同一约束。
- 退役规则：旧规则已经过时、误导或被新规则覆盖。

3. 只生成候选版
- 先改出候选版，而不是宣称“skill 已自动学会”。
- 先使用 [scripts/create_skill_proposal.sh](../scripts/create_skill_proposal.sh) 生成提案骨架，再补全提案内容。
- 候选改动必须同时写清：
  - 改什么
  - 为什么改
  - 替代或合并哪条旧规则
  - 预期解决哪类失真

4. 运行验证
- 至少执行结构校验、引用校验和场景校验。
- 若候选改动影响输出结构、排障纪律或迁移门禁，必须补跑相关验证场景。
- 使用 [scripts/validate_skill_proposal.sh](../scripts/validate_skill_proposal.sh) 为提案写入验证记录，并把提案状态推进到 `validated` 或 `rejected`。
- 若已经回放具体场景，使用 [scripts/record_validation_scenario.sh](../scripts/record_validation_scenario.sh) 把 `通过 / 部分通过 / 不通过`、命中点、偏差点和改进建议写入同一份验证记录；当所有场景均完成且结果满足条件时，提案可自动进入 `ready_to_promote`。场景规格沉淀在 [evolution/scenarios/](../evolution/scenarios/)，写入的 `scenario` 字段必须落在那 6 个固定 slug 内，否则后续 grader 无法对账。
- 若提案已进入 `ready_to_promote`，使用 [scripts/check_skill_promotion_readiness.sh](../scripts/check_skill_promotion_readiness.sh) 查看提示，再使用 [scripts/approve_skill_promotion.sh](../scripts/approve_skill_promotion.sh) 记录授权并把提案推进到 `approved`。

5. 通过后再晋升
- 只有候选版通过验证，才作为新的 active 版本继续使用。
- 验证不通过时，只允许继续修正候选版，不得直接覆盖 active 版。
- `ready_to_promote` 可以自动判定，但不自动晋升。
- `approved` 必须通过显式授权产生，不自动推进。
- 晋升时使用 [scripts/promote_skill_evolution.sh](../scripts/promote_skill_evolution.sh) 归档当前稳定快照、更新 active 版本，并把提案状态推进到 `promoted`；该脚本要求提案状态已经是 `approved`。
- 需要快速演示整条链路时，使用 [scripts/demo_skill_evolution_flow.sh](../scripts/demo_skill_evolution_flow.sh)；脚本默认在结尾自动回滚到 `v1`。

## 候选版约束
- 每次提案优先做最小改动，不同时重写主 skill 和大量 reference。
- 每次提案尽量只处理一个核心问题；若同时发现多个问题，先拆成多个候选改动。
- 若新增一条规则，必须同时回答：它替代哪条旧规则，或为什么不能复用旧规则。
- 涉及跨文件共享概念（链路 / 分层 / 输出格式 / 分流表 / 术语条目等多文件引用的概念）的提案，生成候选版前必须先在 SKILL.md + references/ 全量 grep 该概念，列出所有出现位置，并在提案"变更内容"中覆盖所有位置（或显式标注为后续提案范围）；不得只改单一位置就认为修正完成。常见跨文件共享概念举例：网络链路 / 错误分层 / 状态分层 / 建模分层 / 日志分层 / 四段式输出（owner: SKILL.md 核心铁律）/ findings-first 骨架（owner: review_checklists.md 第 8 节）/ 任务分流 / 术语定义。
- 提案中使用"见 X 文件某节"这类跨文件引用时，必须先打开 X 文件该节确认实际包含被引用的内容；不得引用"未来意图承担但当前缺失"的内容。若引用的内容在目标文件尚不存在，要么同时在本提案中补齐目标文件内容，要么在提案"变更内容"中显式标注"需配合另一提案补齐目标文件 X 的某节"，不得单独提交。
- 若两次连续提案都只是在加规则而没有合并、收紧或退役旧规则，第三次必须先做瘦身检查。

## 自动验证门禁
候选版至少通过以下检查：
- `SKILL.md` frontmatter 合法。
- `agents/openai.yaml` 结构合法。
- `SKILL.md` 中引用的 `references/` 文件存在。
- 主 skill 仍保持分层，不把根因纪律、输出模板、工具预算重新混写。
- 命中的验证场景没有回归。

建议执行：
- 运行 [scripts/validate_skill_evolution.sh](../scripts/validate_skill_evolution.sh) 做基础校验。
- 运行 [scripts/update_skill_proposal_status.sh](../scripts/update_skill_proposal_status.sh) 维护提案状态；允许的状态只有 `draft`、`validated`、`ready_to_promote`、`approved`、`promoted`、`rejected`。
- 按 [validation_scenarios.md](validation_scenarios.md) 选择受影响的场景做前向验证。
- 运行 [scripts/record_validation_scenario.sh](../scripts/record_validation_scenario.sh) 追加结构化场景验证结论。
- 运行 [scripts/check_skill_promotion_readiness.sh](../scripts/check_skill_promotion_readiness.sh) 查看是否已满足授权前置条件和推荐提示。
- 运行 [scripts/approve_skill_promotion.sh](../scripts/approve_skill_promotion.sh) 记录显式授权。
- 需要回退时，使用 [scripts/rollback_skill_evolution.sh](../scripts/rollback_skill_evolution.sh) 恢复已归档版本。

## 晋升与回滚
- 晋升原则：只有通过验证、处于 `ready_to_promote`、并已记录显式授权的候选版，才能在收到显式命令后成为新的 active 版。
- 回滚原则：如果新规则导致输出更长、命中率下降、工具调用失控或与既有铁律冲突，应回退到上一个稳定版本。
- 若当前任务只是在探索规则是否需要调整，可以先保留候选改动，不强制立即晋升。

## 规则 ID 治理
- SKILL.md 中所有结构化规则都带 `[ID]` 前缀（铁律 IR-NNN / 症状导航 SYM-NNN / 任务分流 ROUTE-NNN / 输出模板 OUT-NNN）；ID 真值索引沉淀在 [rule_index.md](rule_index.md)。
- 新增 ID **先改 [rule_index.md](rule_index.md)，再同步 SKILL.md**；两侧由 [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh) 双向断言一致。
- ID 一旦发布不复用：退役时把 [rule_index.md](rule_index.md) 中的 status 改为 `retired` 或 `deprecated` 并填替代 ID（无替代填 `retired-no-replacement`），同时**从 SKILL.md 中删除 inline 引用**——校验脚本会拒绝退役 ID 仍出现在 SKILL.md 的情况。
- 编号可有空洞，无强制连续约束；新增条目优先使用前缀内最大编号 +1。
- ID 不携带语义后缀（不写 `ROUTE-LAYOUT-001` 这种），语义靠 [rule_index.md](rule_index.md) 的「摘要」列传达，避免重命名/拆分时出现 ID 含义漂移。
- [evolution/scenarios/*.json](../evolution/scenarios/) 的 `expected_hits[].rule_id` / `failure_signals[].rule_id` 字段可填 SKILL.md 中已存在的 active ID，用于跨场景统计命中频率；填 retired/deprecated ID 或不存在的 ID 时校验脚本会失败。

## 真实任务观测
- 真实任务命中数据沉淀在 [evolution/usage/usage.jsonl](../evolution/usage/usage.jsonl)，schema、写入协议、三端 audit 块格式与 Codex / Claude Code / Cursor 各自的 system-prompt 片段统一沉淀在 [usage_ledger.md](usage_ledger.md)。
- 写入路径有两条：单条用 [scripts/append_usage_entry.sh](../scripts/append_usage_entry.sh)；批量从 audit 块灌入用 [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh)。两条路径都会原子拒绝非法条目，不污染 ledger。
- ledger 的合法性由 [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh) 把守，集成在伞形校验的 `[8/12]` 步：rule_id 必须在 [rule_index.md](rule_index.md) active 集合内，`task_type` 必须在 6 个固定场景 slug + `other` 之内，`missed_rules == expected_rules - hit_rules`。
- ledger 是后续 summarize / 提案聚类（Step 4）的数据源。三端 audit 块由 LLM 自评，存在 self-grading 偏差——data 应被视作**有偏的草稿**，真正可信的命中率仍要靠 [validation_scenarios.md](validation_scenarios.md) + [evolution/scenarios/*.json](../evolution/scenarios/) 的回归场景集独立回放确认。
- 不要只记败例：平稳成功的任务也要追加，否则采样偏差会让命中率统计失真。
- 定期跑 [scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) 看汇总报表与提案候选信号（高频 missed_rules / `task_type=other` 累积 / 重复 deviation / 工具间 hit_rate 差异）；脚本只读不写仓库，默认输出 markdown 到 stdout，`--json` 输出机器可读，`--since` / `--tool` 缩窄数据集。阈值硬编码在脚本顶部（missed≥3 / other≥5 / dev≥2 / 工具差≥40%）。

## 明确禁止的模式
- 因一次偶发失误就新增永久规则。
- 新增规则时不说明替代关系。
- 用新增规则掩盖已有规则表达不清的问题。
- 没跑验证就宣布 skill 已学会。
- 连续扩容规则而不做瘦身、合并或退役。
- 改动跨文件共享概念时，只改一处就提交候选版，不 grep 其他引用位置。
- 使用跨文件引用（"见 X 文件"、"详见 Y"、"按 Z 执行"）时，未验证目标文件实际包含被引用内容就提交候选版（dead reference）。

## 提案模板
需要做自进化时，优先按以下模板组织变更：

```text
问题信号
- 真实任务里出现了什么偏差

变更类型
- 新增能力 / 修正表达 / 合并重复 / 退役规则

变更内容
- 修改哪些文件
- 替代或合并哪条旧规则

预期收益
- 会减少什么失真
- 会减少什么上下文浪费

验证
- 跑了哪些结构检查
- 回放了哪些验证场景
- 还有哪些残留风险
```
