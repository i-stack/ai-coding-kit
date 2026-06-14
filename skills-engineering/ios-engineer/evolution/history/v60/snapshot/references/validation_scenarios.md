# Skill 验证场景

## 使用规则
- 用本文件验证 `ios-engineer` skill 是否真正做到：少带上下文、先抓根因、避免大改、补齐链路、控制工具调用。
- 每次验证只测 1 个场景，不把多个场景混在一轮。
- 验证结论只回答四件事：是否命中、哪里偏了、为什么偏、规则怎么补。
- 建议使用固定场景标识：`layout`、`parameter-pass-through`、`concurrency`、`review`、`migration`、`mcp-control`。
- 结构化定义沉淀在 [evolution/scenarios/](../evolution/scenarios/) 下的 6 份 JSON 规格（`expected_hits` / `failure_signals` / `output_contract` / `primary_refs`），本文件作为人读伴随。新增或调整场景时**先改 JSON，后同步本文**；伞形校验 [scripts/validate_scenario_specs.sh](../scripts/validate_scenario_specs.sh) 会断言两侧 slug 一致、字段齐全。

### JSON 与本文同步流程
按以下顺序执行，跳步会被对应脚本捕获：

1. 改 `evolution/scenarios/<slug>.json` 的 `expected_hits[].rule_id` / `failure_signals[].rule_id` / `output_contract` / `primary_refs`。
2. 跑 [scripts/validate_scenario_specs.sh](../scripts/validate_scenario_specs.sh) — 断言 6 份 JSON 与本文 slug 双向一致、字段齐全。漏跑会让 slug 漂移在 grader 阶段才暴露。
3. 同步本文对应场景描述（"用户输入示例 / 通过标准 / 失败信号"）。
4. 跑 [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh) — 断言 JSON 内 `rule_id` 是 [rule_index.md](rule_index.md) 中 `status=active` 的 ID。漏跑会让 retired/deprecated/不存在的 ID 进入场景规格。

## 验证目标
- 输出是否优先给出最可能根因，而不是铺开多个大分支。
- 输出是否保持短结构，而不是被模板和背景说明拖长。
- 修复是否遵守最小改动原则，而不是上来重构模块。
- 新增字段或参数时，是否补齐完整数据链路，而不是只修消费端。
- 工具调用是否受控，是否避免重复搜索、重复读取和重复尝试。

## 场景 1：布局异常
用户输入示例：
```text
消息气泡高度偶发错误，长文本会截断，先别重构，帮我找根因。
```

通过标准：
- 先落到布局、复用、自适应高度链路。
- 不直接建议重写整个消息视图。
- 输出保持“根因 / 为什么 / 修法 / 验证”。

失败信号：
- 一上来给大量候选原因。
- 没有先看复用、约束链路、异步回填。
- 直接建议整体替换布局方案。

## 场景 2：参数透传链路
用户输入示例：
```text
修一下 A 类这个方法。新增字段 currentModel，但它现在在 A 里拿不到，B 里也没有。
```

通过标准：
- 识别这是完整数据链路问题。
- 回溯真实来源、构造点、映射层和中间持有者。
- 不只在 A 或 B 局部补变量。

失败信号：
- 只在消费端加属性。
- 给默认值或传空值让当前文件先过。
- 没有说明真实 source of truth。

## 场景 3：并发状态错乱
用户输入示例：
```text
搜索页快速输入时结果会串线，帮我修，不要大改。
```

通过标准：
- 先落到任务取消、过期结果回写、状态归属。
- 优先最小修复，例如取消旧任务或丢弃过期结果。
- 说明验证方式。

失败信号：
- 把问题泛化成“换一套架构”。
- 只加 `DispatchQueue.main.async` 或延迟。
- 不提取消链路。

## 场景 4：代码审查
用户输入示例：
```text
review 这个改动，重点看有没有隐藏回归。
```

通过标准：
- 先报正确性、竞态、生命周期、架构越界、测试缺口。
- Findings 明显先于风格意见。
- 结论简短，不做长篇教学。

失败信号：
- 先讲命名、格式、风格。
- 没有按严重度排序。
- 没提验证缺口。

## 场景 5：复杂迁移
用户输入示例：
```text
准备把这个老的聊天页从 callback 迁到 async/await，给一个落地方案。
```

通过标准：
- 先给四段式摘要。
- 再按需要追加阶段计划、兼容层、回滚条件。
- 不把迁移说成一次性替换。

失败信号：
- 没有阶段划分。
- 没有兼容层和回滚。
- 只讲终态，不讲迁移路径。

## 场景 6：MCP / 工具调用控制
用户输入示例：
```text
这个线上偶发问题帮我查一下，日志很多，你自己看。
```

通过标准：
- 先缩成现象、已知事实、关键缺口。
- 工具调用围绕 1 个主方向推进。
- 两次无新增证据后主动切方向或收敛。

失败信号：
- 一次性打开大量文件或大量搜索。
- 没有预算意识。
- 同一方向重复尝试。

## 记录模板
```text
验证场景
- 场景名称

是否通过
- 通过 / 不通过 / 部分通过

命中点
- 哪些规则起作用

偏差点
- 哪些行为仍然失控或偏题

改进建议
- 应该补哪条规则
- 应该删哪条重复规则
```

结构化记录建议字段：

```text
scenario
- 固定场景标识

result
- pass / partial / fail

hits
- 命中的规则或行为

deviations
- 偏差点

improvements
- 改进建议
```

可选字段（场景规格 JSON 中的 `expected_hits[]` / `failure_signals[]`）：

- `rule_id`：填 SKILL.md 中已存在的 active ID（如 `IR-005`），用于跨场景统计命中频率与 missed_rules 列表对账；ID 来源见 [rule_index.md](rule_index.md)，校验由 [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh) 把守。
