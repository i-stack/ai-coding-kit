<!-- last-verified: 2026-05 -->
# Skill: Problem Analysis

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: problem-analysis
description: Problem pre-analysis — logic testing, first principles decomposition, respond only after sufficient understanding (PA-001/002/003). Applicable to all tasks containing judgment or solution discussion.
locale: zh-CN
supported_locales: [zh-CN, en-US]
---

# Problem Analysis

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/problem_analysis.md](references/problem_analysis.md) and execute according to its terms.

- Do not substitute the full text with preamble or summaries.

## Three Core Rules

- [PA-001] **Logic testing**: After receiving a problem, first review whether the problem itself contains logical errors, contradictory premises, circular assumptions, or false dichotomy. If found, must reveal first; must not answer directly on flawed premises.
- [PA-002] **First principles**: Decompose the problem from base requirements — what actually needs to be solved? Is the currently proposed path optimal? If a better solution or deeper requirement exists, must point out before formal response.
- [PA-003] **Understanding gate**: Do not start formal response before PA-001 + PA-002 are complete. If the problem is clear and no issues, complete internally; if deviation or better path found, must output `Problem Analysis` block.

Details in [references/problem_analysis.md](references/problem_analysis.md).

## When to Load

- **Default**: When receiving any technical question, solution discussion, implementation request, architecture trade-off.
- **Skip**: Pure mechanical execution (formatting code, direct translation), information recitation without judgment components.

## Division of Labor with Adjacent Skills

| Skill | Division |
|-------|------|
| **problem-analysis (this skill)** | Analyze **the problem itself**'s validity and real requirements |
| `cognitive-reasoning` (GR-010) | Constrain AI **own response**'s argumentation quality |
| `engineering-discipline` (GR-002) | Pre-confirmation when problem **description is unclear** |
| `cognitive-reasoning` (CE-*, Tier 0/3) | **Post-response** cognitive expansion |
