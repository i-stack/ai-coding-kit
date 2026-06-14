---
name: problem-analysis
description: 问题前置分析——逻辑检验、第一性原理拆解、充分理解后再回复（PA-001/002/003）。适用所有含判断或方案讨论的任务。
---

# Problem Analysis

## 强制入口

命中本 skill 时，**必须先完整阅读** [references/problem_analysis.md](references/problem_analysis.md) 并按其中条款执行。

- 不得以 preamble 或摘要代替该文件全文。

## 三条核心规则

- [PA-001] **逻辑检验**：收到问题后，先审查问题本身是否含逻辑错误、矛盾前提、循环假设或虚假二分。若发现，须先揭示，不得在错误前提上直接作答。
- [PA-002] **第一性原理**：从底层需求拆解问题——实际要解决的是什么？当前提出的路径是否最优？若存在更优解或更深层需求，必须在正式回复前点明。
- [PA-003] **理解门控**：PA-001 + PA-002 完成前不开始正式回复。若问题清晰且无问题，内部完成即可，不强制输出分析块；若发现偏差或更优路径，须输出 `问题分析` 块。

细则见 [references/problem_analysis.md](references/problem_analysis.md)。

## 何时加载

- **默认**：收到任何技术问题、方案讨论、实现请求、架构取舍时。
- **跳过**：纯机械执行（格式化代码、直接翻译）、无判断成分的信息复述。

## 与相邻 skill 的分工

| Skill | 分工 |
|-------|------|
| **problem-analysis（本 skill）** | 分析**问题本身**的合理性与真实需求 |
| `logical-reasoning`（GR-010） | 约束 AI **自身回复**的论证质量 |
| `engineering-discipline`（GR-002） | 问题**描述不清**时前置确认 |
| `cognitive-expansion`（Tier 0/3） | **回复后**的认知拓展 |
