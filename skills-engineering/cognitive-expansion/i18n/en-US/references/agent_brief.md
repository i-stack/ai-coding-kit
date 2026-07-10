<!-- last-verified: 2026-07 -->
# cognitive-expansion Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Post-response cognitive expansion (reframe/blind spot/adjacent domain/takeaway), breaking knowledge filter bubbles; complementary to ios-engineer Cognitive Adversary Mode. Globally applicable, not limited to iOS engineering.

## When to Invoke

- **Gate-triggered** (Tier 0): When the response contains real judgment/trade-offs/attribution/design choices and can produce ≥1 falsifiable blind spot, append a cognitive footnote.
- **User-initiated** (Tier 3): Load deep-dive mode when user inputs `【深潜】` / `【拓展】`.
- **Skip**: User explicitly says "just give me the answer/no extensions"; pure factual recitation; gate not met.

## Key Behaviors

1. Read `SKILL.md` + full text of `references/cognitive_expansion.md`.
2. Output per Tier 0: Reframe (reframe the question), Blind Spot (points the model is uncertain/unknown about), Adjacent Domain (adjacent field comparison), Takeaway (actionable follow-up).
3. Do not over-extend or pile on — each item must be falsifiable and actionable.
4. Clear division of labor with `ios-engineer` Cognitive Adversary Mode: Tier 2 handles anti-sycophancy/challenge, this skill handles expansion.

## When Not to Invoke

- Pure information queries without judgment
- User skips cognitive expansion
- Tier 0 trigger conditions not met
