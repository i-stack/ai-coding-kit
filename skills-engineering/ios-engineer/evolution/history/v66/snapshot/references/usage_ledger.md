<!-- last-verified: 2026-05 -->
# Usage Ledger（真实任务命中观测）

## 用途
- 把每次真实 iOS 工程任务结束后的「期望命中 / 实际命中 / 偏差 / 结果」结构化追加到 [evolution/usage/usage.jsonl](../evolution/usage/usage.jsonl)。
- 是 Step 4 summarize / 提案聚类的数据源；本文件只定义 schema 与写入协议，**不实现统计**。
- 维护人/工具：写入靠 [scripts/append_usage_entry.sh](../scripts/append_usage_entry.sh)；批量从 audit 块灌入靠 [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh)；合法性由 [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh) 把守。

## 1. JSONL Schema（一行一条）

```json
{
  "time": "2026-05-08T14:30:00+0800",
  "tool": "claude-code",
  "session_id": null,
  "prompt_summary": "搜索页快速输入结果串线",
  "task_type": "concurrency",
  "expected_rules": ["IR-005", "ROUTE-007", "SYM-003"],
  "hit_rules": ["IR-005", "ROUTE-007"],
  "missed_rules": ["SYM-003"],
  "deviations": ["未明确取消旧请求链路"],
  "outcome": "partial",
  "evolution_signal": "修正表达"
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `time` | string | 是 | ISO8601 含时区，如 `2026-05-08T14:30:00+0800` |
| `tool` | string | 是 | 枚举：`codex` / `claude-code` / `cursor` / `manual` / `other` |
| `session_id` | string \| null | 是 | 三端可填会话 ID 便于回溯；不需要时填 `null` |
| `prompt_summary` | string | 是 | **摘要**，5-200 字符；禁贴原始 prompt、源码片段、可识别项目名 |
| `task_type` | string | 是 | 枚举：`layout` / `parameter-pass-through` / `concurrency` / `review` / `migration` / `mcp-control` / `other` |
| `expected_rules` | string[] | 是 | 元素必须是 [rule_index.md](rule_index.md) 中 `status=active` 的 ID（如 `IR-005`） |
| `hit_rules` | string[] | 是 | 同上；可为空数组 |
| `missed_rules` | string[] | 是 | **必须等于** `expected_rules - hit_rules` 的集合差；append 脚本自动计算填入 |
| `deviations` | string[] | 是 | 自由文本数组，可为空数组 |
| `outcome` | string | 是 | 枚举：`pass` / `partial` / `fail` |
| `evolution_signal` | string | 是 | 枚举：`none` / `修正表达` / `新增能力` / `合并重复` / `退役规则`（与 [self_evolution.md](self_evolution.md) 的 4 种变更类型一致） |

## 2. 写入协议（人/脚本通用）

- **每个真实任务完成后追加一条**——无论成败。**平稳成功的任务也要记录**：只记败例会让 ledger 严重偏向负样本，命中率统计直接失真。
- 同一会话有多个独立任务时，分多条记录（每条对应一个 task_type 判断）。
- `prompt_summary` 必须脱敏：
  - 不贴原始用户输入
  - 不贴源码片段或 stack trace
  - 不贴包含可识别项目名的文件路径（除非项目本身公开）
  - 5 字符下限保证至少有内容；200 字符上限保证不滥用
- `expected_rules` 来源建议：先去 [rule_index.md](rule_index.md) 找匹配 `task_type` 的 ROUTE-XXX，再加上跨任务铁律（IR-002 求证 / IR-005 最小修复 / IR-008 残留风险声明等）。
- `hit_rules` 必须诚实——如果不确定，**留空**而不是猜测填入。猜测会污染 Step 4 的命中率。

## 3. CLI 写入

```bash
bash scripts/append_usage_entry.sh \
  --tool claude-code \
  --task-type concurrency \
  --prompt-summary "搜索页快速输入结果串线" \
  --expected-rules "IR-005,ROUTE-007,SYM-003" \
  --hit-rules "IR-005,ROUTE-007" \
  --deviations "未明确取消旧请求链路" \
  --outcome partial \
  --evolution-signal "修正表达"
```

- 字段不合规直接非零退出，不污染 ledger
- `time` 自动取系统时间
- `missed_rules` 自动从 `expected - hit` 计算，**不要手传**
- 可选：`--session-id <id>` / 省略 `--deviations`（默认空数组）/ 省略 `--evolution-signal`（默认 `none`）
- 持锁原子写入，并发安全

## 4. 三端 Audit 块格式（统一）

任意工具（Codex CLI / Claude Code / Cursor）在合适时机输出如下文本块；之后由人工用 [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh) 批量灌入 ledger：

```
<usage-audit>
tool: codex
task-type: concurrency
prompt-summary: 搜索页快速输入结果串线
expected-rules: IR-005, ROUTE-007, SYM-003
hit-rules: IR-005, ROUTE-007
deviations: 未明确取消旧请求链路
outcome: partial
evolution-signal: 修正表达
</usage-audit>
```

- 标签和字段名固定（kebab-case，与 JSONL 字段下划线版本对应）
- 数组字段用逗号分隔
- 空数组：写空字符串（如 `deviations:`）
- `session-id` 可省，等价于 null
- 多个块之间用空行分隔，extract 脚本一次解析所有

## 5. 三端 system-prompt 片段（可粘贴）

三端 system-prompt 各自加入下面对应段落。**核心约束统一**：仅在任务命中 ios-engineer 主题且 `task_type` 落在 6 个固定 slug + `other` 时才输出 audit 块；不要伪造 `hit-rules`，不确定就留空。

### 5.1 Codex CLI

加到 `~/.codex/AGENTS.md` 或项目级 `AGENTS.md`：

```
## ios-engineer skill audit
当任务涉及 iOS / Swift / SwiftUI / UIKit / Xcode 工程，且 task_type 能落在
{layout, parameter-pass-through, concurrency, review, migration, mcp-control, other}
之内时，在最终回答之后追加一个 <usage-audit> 块（格式见 ios-engineer skill
references/usage_ledger.md 第 4 节）：
- tool: codex
- task-type: 上述 7 选 1
- prompt-summary: 5-200 字符脱敏摘要
- expected-rules / hit-rules: 用 IR-XXX / SYM-XXX / ROUTE-XXX / OUT-XXX 形式，
  来源是 ios-engineer/references/rule_index.md 的 active 集合
- deviations: 偏离了什么；没有就留空
- outcome: pass / partial / fail
- evolution-signal: none / 修正表达 / 新增能力 / 合并重复 / 退役规则
不要伪造命中；不确定就在 hit-rules 里留空。
```

### 5.2 Claude Code

加到项目级 `CLAUDE.md` 或全局 `~/.claude/CLAUDE.md`：

```
## ios-engineer skill audit
完成任何 iOS / Swift / SwiftUI / UIKit / Xcode 工程任务后，在回答末尾追加一个
<usage-audit> 块。格式严格遵守 ios-engineer/references/usage_ledger.md 第 4 节。
- tool: claude-code
- task-type 只能落在 {layout, parameter-pass-through, concurrency, review,
  migration, mcp-control, other}
- expected-rules / hit-rules 用 ios-engineer/references/rule_index.md 中
  status=active 的 ID
- 不确定 hit-rules 时留空，不要凭印象猜测
- prompt-summary 脱敏，5-200 字符
非 iOS 工程任务（写文档、看代码、答 API 问题）不必输出 audit 块。
```

### 5.3 Cursor

加到 `.cursorrules`：

```
## ios-engineer skill audit
对 iOS / Swift / SwiftUI / UIKit / Xcode 工程任务，回答之后追加 <usage-audit> 块，
格式见 ios-engineer/references/usage_ledger.md 第 4 节。
- tool: cursor
- task-type ∈ {layout, parameter-pass-through, concurrency, review, migration,
  mcp-control, other}
- expected-rules / hit-rules 用 IR-XXX / SYM-XXX / ROUTE-XXX / OUT-XXX
- 不确定就留空，不猜
- prompt-summary 5-200 字符脱敏
```

## 6. 批量灌入

```bash
bash scripts/extract_usage_audit.sh path/to/transcript.txt
```

- 抽取文件中所有 `<usage-audit>...</usage-audit>` 块
- 解析 KV，逐块调 `append_usage_entry.sh`
- **任一块字段不全或字段非法 → 整批拒绝**，已写入条目不回滚（v1 受限），所以 extract 设计为 dry 校验全部通过后再统一写
- 不做交互式确认；extract 是「audit 块作者的复制器」，不是审计员

## 7. 关于 self-grading 偏差的告示

**重要**：模型自己输出 audit 块本质上是 LLM 给自己评分。这会导致：

- `hit_rules` 系统性高估（模型倾向于声称自己做到了）
- `deviations` 系统性低估（模型不容易察觉自己的偏离）
- 同一个模型在「执行任务」与「审计任务」两个角色里有共同盲点

**所以本 ledger 的数据是「有偏的草稿」**，不是 ground truth。真正可信的命中率要靠 [validation_scenarios.md](validation_scenarios.md) + [evolution/scenarios/*.json](../evolution/scenarios/) 的回归场景集独立回放确认。

Step 4 的 summarize 脚本会按 `tool` 字段分桶，让不同工具间的 self-grading 偏差互相暴露——这是 ledger 现阶段最有用的次级诊断。

**轻量 self-grading 校验**：[scripts/lint_hit_rules.sh](../scripts/lint_hit_rules.sh) 对 audit 块声明的 `hit-rules` 与响应正文做模板字段对账，覆盖 IR-001 / IR-002 / IR-004 / IR-006 / IR-008——这些 IR 都有稳定文本锚点（前置确认 / 版本前提 / 残留风险声明 / 四段式 / findings-first 骨架）。脚本输出每条 PASS / FAIL / UNSUPPORTED，FAIL > 0 非零退出；UNSUPPORTED 不计失败。本脚本是 ledger 入账前的一道前置过滤，不替代 validation_scenarios 回放——后者仍是命中率的最终权威。

## 8. 提案候选信号阈值

[scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) L69-L72 硬编码 4 个阈值常量，超过即在 summarize 输出中作为提案候选信号浮出。本节是这 4 个常量的文档化镜像：

| 常量 | 值 | 候选提案信号 | 含义 |
|------|----|-------------|------|
| `MISSED_RULE_THRESHOLD` | 3 | 新增能力 | 同一 `rule_id` 在 `missed_rules` 中累计 ≥ 3 次 → 现有规则可能表达不到位或缺触发条件 |
| `TASK_TYPE_OTHER_THRESHOLD` | 5 | 新增能力（新 task_type） | `task_type=other` 累计 ≥ 5 条 → 现有 6 个 slug 覆盖不全，可能需新增场景 |
| `DEVIATION_THRESHOLD` | 2 | 修正表达 | 同一 deviation 字符串重复 ≥ 2 次 → 稳定失败模式，对应规则需收紧表达 |
| `TOOL_DIVERGENCE_THRESHOLD` | 0.4 | self-grading 偏差对比 | 同一 `rule_id` 在不同 `tool` 间 hit_rate 差异 ≥ 40%（且每端 expected ≥ 5） → 工具/模型对规则理解分裂，需独立回放确认 |

**漂移防护**：阈值与 [scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) 的 `*_THRESHOLD` 常量一一对应。改本文必须同时改脚本，否则 summarize 输出（`thresholds` 字段会带脚本真值）与文档解释会漂移。后续提案可考虑把"脚本常量 ↔ 本表数字"双向校验补到 [scripts/validate_skill_evolution.sh](../scripts/validate_skill_evolution.sh)。

## 9. 维护

- 新增 `task_type` 枚举值：先扩 [validation_scenarios.md](validation_scenarios.md) 与 [evolution/scenarios/](../evolution/scenarios/)，再同步 [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh) 与本文件。
- 新增 `tool` 枚举值（如 Aider / Continue 等）：直接改本文件 + `validate_usage_ledger.sh` + `append_usage_entry.sh` 的白名单。
- ledger 体积超大（> 10k 行）时再考虑分片或压缩归档；Step 3 不预留分片机制。
