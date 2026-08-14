<!-- last-verified: 2026-05 -->
# Skill: Logical Reasoning

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: logical-reasoning
description: Global argumentation discipline — traceable logic chain, layered, causal discipline, logic chain output block (GR-010). Applies to all engineering tasks, platform-independent.
locale: zh-CN
supported_locales: [zh-CN, en-US]
---

# Logical Reasoning

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/logical_reasoning.md](references/logical_reasoning.md) and execute according to its terms.

- Do not substitute the full text with preamble, Cursor rule summaries, or other secondary summaries.
- Sync dependency: This skill references `../cognitive-calibration/references/cognitive_adversary_mode.md` (platform-agnostic owner of CAM) via relative path in "Division of Labor with Cognitive Adversary Mode"; `ios-engineer` references the same truth via `depends_on: [cognitive-calibration]` and maintains a mirror. When syncing to each platform, ensure `cognitive-calibration` skill is also synced to the same-level skills directory, otherwise that link breaks. **Conditional**: That link is only reachable when cognitive-calibration is synced to the same-level skills directory; in environments where it is not synced, this skill's GR-010 constraint itself remains complete, only the "division of labor with Cognitive Adversary Mode" jump link fails, not affecting core argumentation discipline.

## GR-010 Core Rule

- [GR-010] Responses must have a traceable logic chain; must distinguish "facts / inferences / recommendations / speculations"; must not write unverified inferences as established conclusions; prohibited: unjustified causal jumps, circular reasoning, self-contradiction within the same response; non-obvious judgments must mark at least one "because...therefore..." step; when evidence is insufficient, mark uncertainty, must not use fluent wording to disguise certainty. High-risk judgments must include an independent "Logic Chain" block with fields: facts/evidence, inference, conclusion strength, falsifiable/gaps. Details in [logical_reasoning.md](references/logical_reasoning.md).

## When to Load

- **Default**: All tasks containing judgment components.
- **Must output logic chain block**: Technical decisions, architecture trade-offs, root cause attribution, performance attribution, review final judgments, user strong conviction or explicitly requests challenging viewpoints.
- **Skip**: Pure mechanical execution, tasks without any judgment components.

## Division of Labor with Cognitive Adversary Mode

| Role | Goal | Typical Trigger |
|------|------|-----------------|
| [Cognitive Adversary Mode](../cognitive-calibration/references/cognitive_adversary_mode.md) (cognitive-calibration) | Calibration: challenge user conclusion's logic and assumptions | Technical decisions, strong conviction, explicit red team |
| **This skill (GR-010)** | Constraint: AI's own argumentation quality | All responses containing judgment components |
