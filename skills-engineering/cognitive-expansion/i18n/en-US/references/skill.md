<!-- last-verified: 2026-07 -->
# Skill: Cognitive Expansion

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: cognitive-expansion
description: >-
  Post-response cognitive expansion (reframe/blind spot/adjacent domain/takeaway),
  breaking knowledge filter bubbles; complementary to ios-engineer Cognitive Adversary Mode.
  Globally applicable, not limited to iOS engineering.
locale: zh-CN
supported_locales: [zh-CN, en-US]
---

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/cognitive_expansion.md](references/cognitive_expansion.md) and execute according to its terms.

- Do not substitute the full text with preamble, Cursor rule summaries, or other secondary summaries.
- Tier 2 (Cognitive Adversary) is carried by [ios-engineer references/cognitive_adversary_mode.md](../ios-engineer/references/cognitive_adversary_mode.md); this skill manages Tier 0 / Tier 3 expansion.
- Sync dependency: This skill references `../ios-engineer/references/cognitive_adversary_mode.md` via relative path; when syncing to each platform, ensure `ios-engineer` skill is also synced to the same-level skills directory (e.g., `~/.claude/skills/ios-engineer`), otherwise that link breaks. **Conditional**: Tier 2 link is only available when ios-engineer is synced to the same-level skills directory; in non-iOS environments (ios-engineer not synced), this skill only provides Tier 0 / Tier 3; Tier 2 requires the user to explicitly load ios-engineer. Do not interrupt Tier 0/3 due to link unavailability.

## When to Load

- **Gate**: Tier 0 cognitive footnote **does not trigger by default**; only appended when the response contains real judgment / trade-offs / attribution / design choices, **AND** can produce at least 1 falsifiable blind spot; otherwise silent (see detailed spec "Trigger Gate").
- **Deepen**: User writes `【深潜】` / `【拓展】` (Tier 3).
- **Skip**: User explicitly says "just give me the answer / no extensions"; or gate not met.

## Rule Index (owned rule IDs)

This skill's contract is carried by the following `CE-NNN` rules, with the source-of-truth registry in [references/rule_index.md](references/rule_index.md). Format calibration examples (before/after and degeneration specimens) in [references/examples.md](references/examples.md). Behavior gate `scripts/validate-skill-behavior.sh` Check 2 validates bidirectional consistency of ID sets between the two files (IDs declared in SKILL.md are all defined; active rows in rule_index.md are all declared in SKILL.md).

- [CE-001] Tier 0 trigger gate: dual conditions (contains judgment component AND can produce ≥1 falsifiable blind spot) must both be met to append cognitive footnote, otherwise silent.
- [CE-002] Reframe: elevate the question to a more general judgment/learning question; pure execution tasks write "reframe skipped".
- [CE-003] Blind spot (falsifiable hard criterion): 1 hidden assumption/missed dimension/pitfall, must contain (assumption X) + (observable trigger Y) + (if Y then X is wrong negation condition); if can't write it, skip entire section.
- [CE-004] Adjacent domain (mechanism-related): 1 adjacent field comparison, must be mechanism-related to current question, no same-tech-stack word-shuffling repetition of main text.
- [CE-005] Takeaway: 1 reusable self-check question or if-then rule, no chicken soup.
- [CE-006] Tier 0/Tier 2 mutual exclusion: when Cognitive Adversary (Tier 2) is triggered, output full calibration structure, no separate Tier 0.
- [CE-007] Deep Dive · Mental Model: model name + 1 sentence on how it applies to this problem.
- [CE-008] Deep Dive · Cross-domain Analogy: non-same-tech-stack, mechanism-aligned analogy; must name the mapped mechanism, no cliché/word-shuffle analogies (guardrails see references/cognitive_expansion.md §Tier 3).
- [CE-009] Deep Dive · Verification Action: 1 specific action doable within 7 days.
- [CE-010] Sycophancy self-check: after writing, pass three questions (adjacent domain not word-shuffle / takeaway not chicken soup / blind spot falsifiable).
- [CE-011] Skip conditions: do not write Tier 0 if user says "just give me the answer/no extensions" or gate not met.
- [CE-012] Adjacent domain comparison pool: pick 1 from the pool and must be mechanism-related.
- [CE-013] Deduplication with L2/L0: when logical-reasoning "logic chain (falsifiable/gaps)" or problem-analysis "problem analysis" has been issued in the same round, blind spot must change dimension, no restatement.
