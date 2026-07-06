---
name: plan-grill
description: 需求对齐/盘问锁定计划——一次一个问题盘问决策树，每个问题给推荐答案，能查代码就查代码，确认前不执行。产出 PLAN.md 供后续 cross-model-review 接力。基于 Matt Pocock 的 grill-me（MIT）。
---

# Plan Grill

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/plan_grill.md](references/plan_grill.md) 并按其中条款执行。

- 不得以 preamble、Cursor 规则摘要或其它二次摘要代替该文件全文。
- 本 skill 是 `cross-model-review` 的 Act 1；若需要跨模型对抗审查，盘问锁定后接力 `cross-model-review`。

## 四条核心规则

- [PG-001] **逐一提问**：一次只问一个问题，等用户回答后再继续。禁止一次抛出多个问题。
- [PG-002] **给推荐答案**：每个问题须给出推荐答案 + 一句理由，让用户可以快速确认或反驳，而非从零思考。
- [PG-003] **遍历设计树**：沿决策树分支逐一解决依赖；能通过探索代码库回答的问题，直接查代码，不问用户。
- [PG-004] **锁定产出**：决策树解析完且与用户达成共识后，产出 `PLAN.md`（Goal / Constraints & assumptions / Approach / Key decisions & tradeoffs / Validation plan / Risks / Out of scope）。**确认前不执行计划。**

细则见 [references/plan_grill.md](references/plan_grill.md)。

## 何时加载

- **默认触发**：用户说 `【盘问】` / `/plan-grill` / `/grill-me` / "grill me" / "锁定计划" / "盘问我的方案" / "盘我" / "拷问方案" / "先锁计划" / "先别写代码" / "stress-test the plan" / "requirements interview"。
- **建议触发**（不自动）：高风险任务（鉴权、schema、并发、迁移、支付）前，可主动建议用户触发，但需用户确认；不得与用户明确"直接做"的工作流冲突。
- **跳过**：trivial 改动（typo、格式化、单点语法）、纯执行任务、用户明确"直接做"。

## 与相邻 skill 的分工

| Skill | 分工 |
|-------|------|
| `problem-analysis`（PA-001/002/003） | 分析**问题本身**的合理性与真实需求 |
| **plan-grill（本 skill）** | 问题清晰后，盘问**实现方案**的决策树并锁定计划 |
| `cross-model-review` | plan-grill 锁定后，跨模型对抗审查 PLAN.md |
| `engineering-discipline`（GR-002） | 问题**描述不清**时前置确认 |
