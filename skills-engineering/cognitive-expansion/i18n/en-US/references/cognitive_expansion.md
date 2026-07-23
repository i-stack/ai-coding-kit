<!-- last-verified: 2026-06 -->
# Cognitive Expansion

> This is an English mirror of the authoritative Chinese `references/cognitive_expansion.md`.
> In case of discrepancies, the Chinese source takes precedence.

> **Source of truth**: This file is the sole detailed specification. `cognitive-expansion/SKILL.md` is the entry point; full copies for each platform are synced by `scripts/sync-skills.sh` to `~/.codex/skills/`, `~/.claude/skills/`, `~/.cursor/skills/`; within Cursor projects, `sync-agent-preamble.sh` generates `.cursor/rules/cognitive-expansion.mdc` from this file.

## Division of Labor with Cognitive Adversary Mode

| Mode | Goal | Typical Trigger |
|------|------|-----------------|
| [Cognitive Adversary Mode](../../ios-engineer/references/cognitive_adversary_mode.md) | Calibration: approach truth, challenge false certainty | Technical decisions, architecture, root-cause conclusions, review judgments, strong conviction |
| **Cognitive Expansion (this file)** | Expansion: break filter bubbles, portable capabilities | Appended when Tier 0 gate hits; deepened with `【深潜】` |

Both can coexist: decision-type goes through Cognitive Adversary (Tier 2) first; other responses only append Tier 0 footnotes when the gate is hit, otherwise stay silent.

> **Link conditionality**: The link to Cognitive Adversary Mode `../../ios-engineer/references/cognitive_adversary_mode.md` in the table above is only reachable when ios-engineer skill has been synced to the same-level skills directory. In non-iOS environments (ios-engineer not synced), this skill only provides Tier 0 / Tier 3; Tier 2 requires the user to explicitly load ios-engineer. Link unavailability does not block Tier 0/3.

## Three-Tier Division

| Tier | When | What |
|------|------|------|
| **Tier 0 (Gate)** | Appended after response when gate conditions below are met | Fixed section "Cognitive Footnote", 3–5 lines |
| **Tier 2** | Technical decisions / architecture / root-cause conclusions / review final judgments / user strong conviction | Full Cognitive Adversary Steps 0–6 (see ios-engineer `cognitive_adversary_mode.md`) |
| **Tier 3** | User writes `【深潜】` or `【拓展】` | Tier 0 + Mental Model + Cross-domain Analogy + 7-day verifiable action |

When Tier 2 is triggered: use the full Cognitive Adversary structure; **do not separately output** the Tier 0 footnote, and the preamble's lightweight cognitive-calibration section is likewise carried by the CAM structure and not output on its own (see CE-006 and the global cognitive calibration section). The three calibration layers are deduplicated to avoid repetition.

## Trigger Gate (Whether Tier 0 Is Appended)

Tier 0 is **not written by default**. It is only appended when both conditions below are **simultaneously** met; otherwise stay silent, leave no trace:

1. **Contains judgment**: The response contains real judgment / trade-offs / attribution / design choices (not pure execution, pure syntax, or pure fact retrieval).
2. **Can produce a falsifiable blind spot**: Can write at least 1 specific falsifiable blind spot ("If X happens, the assumption was wrong"). **If you can't produce a qualifying blind spot, skip the entire section** — this is a hard gate; no padding for format's sake.

The gate uses "blind spot" rather than "reframing / adjacent domain" because the latter two most easily degrade into word-shuffling repetition; if you can't write a blind spot, there's no cognitive increment worth expanding on, and silence is the correct output.

> Design intent: reduce insurance costs from "every time" to "when worth it". Better to miss one medium-value footnote than to dilute the signal with low-value footnotes and train the user to skip them.

## Tier 0: Cognitive Footnote (Appended After Gate Is Met)

Fixed heading **`Cognitive Footnote`**, each item 1 line, 4 items total:

1. **Reframe**: Elevate the current question to a more general judgment/learning question; for pure execution tasks (fixing typos, running commands, single-point syntax) write "Execution task, reframe skipped".
2. **Blind Spot**: 1 specific hidden assumption, missed dimension, or common pitfall; must be testable ("If X happens, the assumption was wrong"); no vague "be careful about boundaries".
3. **Adjacent Domain**: 1 comparison from an **adjacent field** (see comparison pool below); must be **mechanism-related** to the current question; no word-shuffling repetition of the main text within the same tech stack.
4. **Takeaway**: 1 reusable self-check question or if-then rule for the user to apply independently next time.

Constraints: Do not substitute the footnote for the main answer; do not delay execution requests; no preaching; no repeating content already in the main text.

## Tier 3: Deep Dive (Appended on Explicit Trigger)

After Tier 0, add:

- **Mental Model**: (Model name + 1 sentence on how it applies to this problem)
- **Cross-domain Analogy**: Non-same-tech-stack, mechanism-aligned analogy; must satisfy the following guardrails (CE-008):

  - **Mechanism Alignment**: The analogy source and target must be isomorphic in **underlying mechanism** (e.g., metric hijacking the goal, incentive misalignment), not just surface-level thematic similarity.
  - **Name the Mapped Mechanism**: Explicitly write "A's X mechanism ↔ B's Y mechanism"; otherwise treat as unaligned and don't write.
  - **No Cliché Analogies**: Traffic rules / chess / doctor visits — overused metaphors — unless you can provide a unique and fitting mechanism mapping from that domain.
  - **No Word-shuffle Analogies**: Paraphrasing the main text within the same tech stack without introducing a new mechanism perspective (simultaneously violates CE-004 adjacent domain constraint).

  - ✅ good: Education system "teaching to the test → literacy replaced by scores" and review "going through the motions to pass" share the same mechanism (metric hijacking the goal), introducing a new education governance perspective, not word-shuffling (consistent with examples.md Example 2).
  - ❌ bad: "Writing code is like building a house — a weak foundation will collapse" — cliché and only word-shuffling, no named mapped mechanism (should not write).
- **Verification Action**: (1 specific action doable within 7 days)

## Adjacent Domain Comparison Pool (Pick 1, Must Be Mechanism-Related)

- Concurrency / UI state → Distributed consistency, idempotency, stale reads
- Performance → Queuing theory, tail latency, SRE error budgets
- Architecture → Conway's Law, DDD bounded contexts
- Testing → Property-based testing, fault injection
- Troubleshooting → Scientific method, Bayesian updating, pre-mortem
- Product / Collaboration → Incentive misalignment, Goodhart's Law
- Security → Threat modeling, least privilege, defense in depth

## Skip Conditions

Do not write Tier 0 if any of the following: User explicitly says "just give me the answer / no extensions"; or the two gate conditions are not simultaneously met (default case).

## Compact Trigger Phrases

- `【深潜】` / `【拓展】` → Tier 3
- `【认知对手模式】` / `【不要迎合】` / `【red team】` → Tier 2 (not this file)

## Sycophancy Self-Check (Quick pass after writing footnote)

- [ ] Is the adjacent domain comparison just word-shuffling the main text?
- [ ] Is the "takeaway" an actionable question/rule, not chicken soup?
- [ ] Is the blind spot specific enough to be falsifiable, not "might have issues"?

## Appendix: Process Safeguards (Optional Habits, Not Gated)

> The following are optional habits beyond a single prompt, **not part of the mandatory contract, not counted in any `validate-skill-behavior.sh` Check**, provided only for users who want to continuously train cognitive habits.

- **Prediction Log**: Record confidence level + 2 falsifiable conditions + date for important conclusions
- **Dual Session**: New Chat, paste only the conclusion, dedicated red team, no emotional carryover from original conversation
- **Weekly Deep Dive**: Ask "What assumptions have I been repeating this week?"
