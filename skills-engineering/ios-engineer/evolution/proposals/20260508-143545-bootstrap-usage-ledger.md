# Skill Evolution Proposal

## Metadata
- Proposal ID: 20260508-143545-bootstrap-usage-ledger
- Created At: 2026-05-08 14:35:45 +0800
- Active Version At Creation: v44

## 问题信号
- Step 1（v43）落地了 evolution/scenarios/ 6 份 JSON 规格，Step 2（v44）给 SKILL.md 装上 41 个 rule-ID。但当前没有任何机制把「真实任务里命中/未命中了哪些规则」写进可统计的池子，导致：
  - 后续 summarize / 提案聚类（Step 4）没有数据源；
  - 跨工具（Codex / Claude Code / Cursor）的命中差异无法对比；
  - missed_rules 信号无法跨提案累加，无法触发「同类失败 ≥ N 次自动起草提案」这种半自动进化路径。
- 用户已明确希望本步只做「写入路径 + 三端写入规范」，不做统计。

## 变更类型
- 新增能力（不退役、不替代任何旧规则；不动 SKILL.md / rule_index.md / 任何 scenario JSON / 既有 13 个脚本契约）

## 变更内容
- 修改文件：
  - 新增目录 `evolution/usage/`（包含空 `usage.jsonl` 与 `.gitkeep`）
  - 新增 `references/usage_ledger.md`：JSONL schema、写入协议、三端 audit 块格式、Codex/Claude Code/Cursor 各自的 system-prompt 片段、self-grading 偏差告示
  - 新增 `scripts/append_usage_entry.sh`：长 flag CLI，严格字段校验、自动计算 missed_rules、原子写入（mkdir 互斥锁）
  - 新增 `scripts/validate_usage_ledger.sh`：逐行 JSON 合法性 / 必填字段 / 枚举白名单 / ID 落在 rule_index active 集合 / missed_rules 与 expected-hit 集合差一致 / task_type 落在 6 + other
  - 新增 `scripts/extract_usage_audit.sh`：从任意文本中正则抽 `<usage-audit>...</usage-audit>` 块、解析 KV、调 append CLI；任一块非法则整批拒绝（防部分污染）
  - `scripts/validate_skill_evolution.sh` 插入 `[8/12] Validate usage ledger`，原 [8-11] 顺延为 [9-12]
  - `references/self_evolution.md` 新增「真实任务观测」章节，链接 usage_ledger.md
- 替代或合并旧规则：无

## 预期收益
- 让 Step 4（summarize / 提案聚类）拥有数据源；本步不实现统计，但 schema 与协议落地后，统计层可以独立增量
- 三端 audit 块统一格式：未来 Codex / Claude Code / Cursor 都能产出同形态文本，由 extract 脚本批量灌入，避免每端做一套写入路径
- 严格 schema + 反向校验（missed_rules 集合差、rule_id 必须 active、task_type 限定 6 + other）从一开始就把 ledger 维持在可统计的形态，避免「先写后清洗」的常见陷阱

## 验证
- 结构校验：
  - `bash scripts/validate_usage_ledger.sh` 空 ledger 视为合法
  - 用 append 写一条合法条目后重跑应通过
  - `bash scripts/validate_skill_evolution.sh` 12 步全绿
  - 反向 1：手动追加一行 missed_rules 不等于 expected-hit 的 jsonl，应失败
  - 反向 2：手动追加一行 expected_rules 含 `IR-999` 的 jsonl，应失败
  - 反向 3：手动追加一行 task_type=`random-stuff` 的 jsonl，应失败
  - 抽取测试：写一个含 1 合法 + 1 非法 audit 块的 transcript，extract 整批拒绝、ledger 不被部分污染
- 场景回放：6 个固定场景人工自评分；本提案不动 skill 行为，只验证 ledger 体系不引入回归
- 残留风险：
  - 三端 audit 块由 LLM 自评：fox-guarding-henhouse 风险——会高估 hit_rules / 低估 deviations。usage_ledger.md 已显式告示，真正可信的命中率仍要靠 Step 1 回归场景集独立回放确认
  - extract 脚本不做交互式确认，等同 audit 块作者的复制器（不是审计员）
  - `evolution/usage/` 不在快照范围（与 `evolution/scenarios/` 同样限制），ledger drift 不会被 [10/12] 快照一致性捕获
  - manual append 高摩擦 → 早期数据采样可能稀疏；先跑 1-2 周看真实形态再决定是否做 Stop hook / 自动化

## 状态
- promoted
