# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-151354-bootstrap-summarize-usage-ledger
- Created At: 2026-05-08 15:13:54 +0800
- Active Version At Creation: v46

## 问题信号
- Step 1（v43）/ Step 2（v44）/ Step 3（v46）已落地 SkillOps 的所有写入路径：场景规格、rule-ID、usage ledger。但 ledger 是 append-only 纯文本池，人没法直观看出：
  - 哪条规则反复 missed
  - 哪两个工具命中差异显著
  - `task_type=other` 是否在涌入（暗示新场景）
  - 哪些 deviation 文本反复出现（暗示稳定失败模式）
- Step 4 上线 summarize 脚本，把 ledger 聚合成 markdown 报表 + JSON，并按预设阈值 surface 提案候选信号。**用户已明确选择「仅 surface 信号，不自动起草 proposal draft」**。

## 变更类型
- 新增能力（不退役、不替代任何旧规则；不动 SKILL.md / rule_index.md / 任何 scenario JSON / ledger schema）

## 变更内容
- 修改文件：
  - 新增 `scripts/summarize_usage_ledger.sh`：bash + ruby；读 `evolution/usage/usage.jsonl` 聚合统计、读 `references/rule_index.md` 把 ID 映射回摘要；输出 markdown 到 stdout（默认）或 JSON（`--json`）；支持 `--since YYYY-MM-DD` / `--tool <slug>` / `--output FILE` 过滤；阈值硬编码（missed_rule≥3 / task_type_other≥5 / deviation≥2 / 工具 hit_rate 差≥0.4，每端最低 5 条样本才比较）
  - `references/self_evolution.md` 「真实任务观测」章节追加 1 行说明 summarize 用法
- 替代或合并旧规则：无；不动既有契约

## 预期收益
- ledger 从「写得进、看不见」升级为「写得进、报得出」：人可以定期跑一次报告判断 skill 状态
- 阈值化的「提案候选信号」段是 SkillOps 半自动闭环的最后一块——把 LLM-self-grading 偏差暴露在工具间对比中（同一规则 codex 92% / claude-code 60% 这类信号最有价值）
- 报表 markdown 形态便于人读，JSON 形态保留下游脚本可消费的接口
- 不加入伞形校验：summarize 是报表工具无 pass/fail 概念，避免误把它做成阻塞门槛

## 验证
- 结构校验：
  - 空 ledger → 输出 `No entries yet (ledger empty)` exit 0
  - 合成 10 条 ledger 数据，跑默认 markdown 输出排版正确、各分桶数字与 ledger 实际计数一致
  - 阈值触发测试：构造数据触发 4 类信号（missed_rule、task_type=other、deviation、tool divergence），逐项确认 surface
  - JSON 输出可被 `JSON.parse` 解析，键名稳定（`by_tool` / `by_task_type` / `top_missed` / `top_deviations` / `proposal_signals`）
  - `--since` / `--tool` 过滤后数字相应变化
  - 清空 ledger 回到空状态，`bash scripts/validate_skill_evolution.sh` 12 步全绿不受影响（本步未改 umbrella）
- 场景回放：6 个固定场景人工自评分；本提案不动 skill 行为，只验证 summarize 不引入回归
- 残留风险：
  - deviation 仅完全字符串相等聚合（无 embedding / 编辑距离），近义偏差会被拆桶；v1 接受这个粒度，后续如果数据量上来后聚合粒度太细可升级
  - 阈值硬编码不开 CLI flag；调阈值要走提案 + 改源码，避免参数膨胀
  - 自动起草 proposal draft 不在本步；下一步独立计划再上
  - `evolution/usage/` 仍不在快照范围（与 `evolution/scenarios/` 同样限制），summarize 不受影响但 drift 风险仍在

## 状态
- promoted
