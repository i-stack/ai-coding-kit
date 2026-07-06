<!-- last-verified: 2026-07 -->
# 计划盘问（Plan Grill）

> **真值来源**：本文件为唯一详规正文。`plan-grill/SKILL.md` 为入口；各端完整副本由 `scripts/sync-skills.sh` 同步到 `~/.codex/skills/`、`~/.claude/skills/`、`~/.cursor/skills/`、`~/.gemini/skills/`；Cursor 项目内另由 `sync-agent-preamble.sh` 生成 `.cursor/rules/plan-grill.mdc`。

## 定位

plan-grill 解决 AI 辅助编码的第 1 类失败模式：**你和 AI 对"构建什么"未达成共识**。通过一次一个问题的盘问，把模糊需求逼成可执行的锁定计划。

本 skill 基于 Matt Pocock 的 `grill-me`（MIT 许可），适配本项目结构化 skill 框架。

## 与 problem-analysis 的衔接

| 阶段 | skill | 做什么 |
|------|-------|--------|
| 1. 问题审查 | `problem-analysis` | 检查问题本身是否含逻辑错误、矛盾前提；拆解真实需求 |
| 2. 方案盘问 | **plan-grill** | 问题清晰后，盘问实现方案的决策树，逐一锁定 |
| 3. 跨模型审查（可选） | `cross-model-review` | 锁定后，已选 reviewer 对抗审查 PLAN.md |

problem-analysis 未完成时，plan-grill 不开始——否则会在错误前提上盘问。

## 盘问规则（PG-001 ~ PG-004 详规）

### PG-001 逐一提问

- **一次一个问题**。问完即停，等用户回答。
- 禁止用「另外还有…」「顺便问下…」追加第二问。
- 若问题有依赖，先问被依赖的那个；依赖未明时不下钻。
- 一次抛多个问题会让用户 bewildered（Matt Pocock 原话），违反本规则。

### PG-002 给推荐答案

每个问题须包含：

1. **问题本身**（一句话，具体到决策点）
2. **推荐答案**（一句话，给方向而非含糊「看情况」）
3. **理由**（一句，为什么推荐这个）

格式：

```
Q: <问题>
推荐: <答案>
理由: <一句>
```

让用户可以「确认 / 反驳 / 跳过」，而非从零思考。推荐答案不是替用户决定，是降低决策成本。

### PG-003 遍历设计树

- 把方案拆成决策树，按依赖顺序逐一解决。
- **能查代码就查代码**：如果一个问题可以通过探索代码库回答（如「这个函数返回什么类型」「现有 schema 有没有 X 字段」「这个配置项的默认值」），直接查，不问用户。
- 用户回答后，沿其分支下钻下一层；不横向跳跃。
- 决策树完全解析（无未决分支）后才进入产出。

### PG-004 锁定产出

决策树解析完且与用户达成共识后，写入 `PLAN.md`：

```markdown
# Plan: <一句话标题>

## Goal
<要解决什么，一句话>

## Constraints & assumptions
- <约束 1：必须满足的硬条件>
- <假设 1：未验证但当前假定为真>

## Approach
<怎么做，2-5 句>

## Key decisions & tradeoffs
- <决策 1>：选 A 而非 B，因为…
- <决策 2>：…

## Validation plan
- <如何证明方案有效：测试/验收路径>

## Risks / non-blocking open questions
- <风险 1：non-blocking，可保留>
- <或显式 "None">

## Out of scope
- <明确不做的事>
```

写入后告知用户：「PLAN.md 已锁定。如需跨模型对抗审查，接力 `cross-model-review`。」

## 何时停止盘问

满足以下全部条件才停：

1. 决策树无未决分支（每个叶子节点都有明确选择）
2. 用户对每个决策确认或接受推荐
3. PLAN.md 七段（Goal / Constraints & assumptions / Approach / Key decisions / Validation plan / Risks / Out of scope）都能填实
4. **blocking open questions 必须为空**：未决的阻塞性问题必须在盘问阶段解决，不得遗留。
5. **non-blocking risks 可保留**：已知但不阻塞实施的风险，写入 Risks 段即可，不必在盘问阶段消除。

任一不满足，继续问下一个未决点。

## 跳过条件

- trivial 改动（typo、格式化、单点语法、直接翻译）
- 用户明确「直接做」「不要盘问」
- 纯执行任务（已知明确指令，只需执行）

## 盘问质量自检

盘问结束前过一遍：

- [ ] 是否每个问题都给了推荐答案 + 理由？
- [ ] 是否有本可查代码却问了用户的问题？（应改为查代码）
- [ ] 决策树是否还有未决叶子？
- [ ] PLAN.md 七段是否都填实，无占位符？
- [ ] blocking open questions 是否已清空？non-blocking risks 是否已记录？

## 与 cross-model-review 的接力

plan-grill 产出的 `PLAN.md` 是 `cross-model-review` 的输入。若用户在盘问后说「让另一个模型审查」「cross review」「对抗审查」，则：

1. plan-grill 完成（PLAN.md 已写）
2. 加载 `cross-model-review` skill
3. cross-model-review 读取 PLAN.md，自动发现可用 CLI（codex/gemini/claude），推荐组合并让用户选择，调用已选 reviewer 对抗审查

详见 `cross-model-review/references/cross_model_review.md`。

## 致谢

本 skill 基于 Matt Pocock 的 `grill-me`（MIT 许可，https://github.com/mattpocock/skills）；盘问规则源自其 `grilling` 实现。适配本项目结构化 skill 框架。
