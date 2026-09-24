<!-- last-verified: 2026-09 -->
# Skill: Problem Analysis

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: problem-analysis
description: >-
  Problem pre-analysis — logic testing, first principles decomposition, respond only after sufficient understanding (PA-001/002/003).
  Default-load on judgment, solution discussion, implementation requests, or architecture trade-offs; skip pure mechanical execution (formatting, direct translation, recitation without judgment).
  Fact-class questions are verified, not derived from first principles.
locale: zh-CN
supported_locales: [zh-CN]
experimental_locales: [en-US]
---

# Problem Analysis

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/problem_analysis.md](references/problem_analysis.md) and execute according to its terms.

- Do not substitute the full text with preamble or summaries.
- Rule ID source of truth: [references/rule_index.md](references/rule_index.md).

## Three Core Rules

- [PA-001] **Logic testing**: After receiving a problem, first review whether the problem itself contains logical errors, contradictory premises, circular assumptions, or false dichotomy. If found, must reveal first; must not answer directly on flawed premises.
- [PA-002] **First principles**: For reasoning/trade-off questions, decompose from base requirements — what actually needs to be solved? Is the currently proposed path optimal? Fact-class questions (API, numbers, interface behavior, events) are verified, not derived from first principles (same boundary as GR-013). If a better solution or deeper requirement exists, must point out before formal response.
- [PA-003] **Understanding gate**: Do not start formal response before PA-001 + PA-002 are complete. Three states: problem clear and path reasonable → silent (no analysis block); substantial logical error, strong assumption, or better path → output `Problem Analysis` block then answer; base requirement does not match surface request → confirm real intent first, do not advance the solution before confirmation.

Details in [references/problem_analysis.md](references/problem_analysis.md).

## `Problem Analysis` Block (mechanical format)

Output only in explicit mode. Field names are fixed; do not rename to aliases such as "Logic issue / Better path":

```
Problem Analysis
Logic test: <logical flaws found, or "none">
Real requirement: <base goal after first principles decomposition>
Path evaluation: <whether current solution is optimal; if better solution exists, one sentence>
```

Block is immediately followed by the formal response. This block addresses input (the problem itself) and is not merged with `Logic Chain` / `Verification Anchor` / four-section output.

## When to Load

- **Default**: Any technical question containing judgment, solution discussion, implementation request, or architecture trade-off. Does not depend on the user saying "first principles / deeper need / problem deviation".
- **Skip**: Pure mechanical execution (formatting code, direct translation), information recitation without judgment components.

## Division of Labor with Adjacent Skills

| Skill | Division |
|-------|------|
| **problem-analysis (this skill)** | Analyze **the problem itself**'s validity and real requirements (L0, before formal response) |
| `engineering-discipline` (GR-002) | Pre-confirmation when problem **description is unclear**; this skill does not replace that block |
| `cognitive-reasoning` (GR-013) | Decide whether this question is fact (verify) or reasoning (PA-002 allowed) |
| `cognitive-reasoning` (GR-010) | Constrain AI **own response**'s argumentation quality |
| `cognitive-reasoning` (CAM-001~005) | Challenge **user conclusions**; when both hit, finish problem review first, then emit CAM fields |
| `plan-grill` (PG-000) | After this skill, grill the **implementation** decision tree; do not start grilling before problem review completes |
| `cognitive-reasoning` (CE-*, Tier 0/3) | **Post-response** cognitive expansion |
