<!-- last-verified: 2026-07 -->
# Cognitive Expansion Examples (before / after)

> This is an English mirror of the authoritative Chinese `references/examples.md`.
> In case of discrepancies, the Chinese source takes precedence.

> This file is the **format calibration anchor** for `cognitive-expansion`, provided for LLM output alignment.
> Source-of-truth rules are in [rule_index.md](rule_index.md); this document does not introduce new rule IDs, only uses `CE-NNN` back-references to the contract.
> Prose norms without examples are most likely to degrade — the following samples are the criteria for "what qualifies / what counts as not written".

## Example 1: Tier 0 Cognitive Footnote After a Normal Response (Satisfies CE-001 ~ CE-005, CE-010)

**User asks**: "Should I use Redux or Context to manage state in this mid-sized React app?"

**Main answer (excerpt)**: Recommend layering by state type — use React Query for server-side cache, Context for global UI state, and only use Redux for domain state that truly needs time-travel/predictable dispatch; mid-sized apps usually don't need Redux.

**Appended Cognitive Footnote (gate met: contains trade-offs + can produce falsifiable blind spot)**:

> Cognitive Footnote
> - Reframe (CE-002): State management selection is fundamentally a "state lifecycle and ownership" problem, not "which library to use".
> - Blind Spot (CE-003): If over the next 3 months you frequently write selectors/utils to work around Context's re-rendering, the assumption "mid-sized app with Context is enough" was wrong — Context's fine-grained update cost is underestimated.
> - Adjacent Domain (CE-004): In distributed systems, "state ownership" likewise determines consistency boundaries (Conway's Law: team boundaries map to state boundaries), same mechanism as frontend state layering.
> - Takeaway (CE-005): Next time before selecting, first ask "Who will modify this state, and at what frequency?" before deciding the ownership layer.

## Example 2: User Writes 【深潜】 for Tier 3 (Satisfies CE-006 ~ CE-009, plus CE-001~005)

**User asks**: "【深潜】 Why does our team's code review always become a formality?"

**Main answer (excerpt)**: Review formalism often stems from incentive misalignment and Goodhart's Law — when "number of reviews passed" becomes the metric, reviewers tend to quickly LGTM.

**Appended (Tier 0 + Tier 3)**:

> Cognitive Footnote
> - Reframe (CE-002): Review failure is a universal phenomenon of "quality signals being replaced by metrics", not limited to the code domain.
> - Blind Spot (CE-003): If after introducing "mandatory comment word count" review quality actually decreases (formulaic comments appear), the assumption "longer comments = more thoughtful" was wrong — length weakly correlates with thoughtfulness.
> - Adjacent Domain (CE-004): In the scientific method, "pre-registering hypotheses" exists precisely to prevent post-hoc treating noise as signal, same mechanism as Goodhart.
> - Takeaway (CE-005): Use "how many real issues did the review find" rather than "time to pass" as the health metric.
>
> Deep Dive
> - Mental Model (CE-007): Goodhart's Law (when a measure becomes a target, it ceases to be a good measure) — used to explain why LGTM culture self-dilutes.
> - Cross-domain Analogy (CE-008): Education system "teaching to the test" leads to literacy being replaced by scores, same mechanism as reviews becoming formalities to "pass" (metric hijacking the goal), not word-shuffling the main text.
> - Verification Action (CE-009): Within 7 days, change the review template from "LGTM / Request changes" to "The 1 most critical risk + 1 verifiable improvement this time", then observe discussion quality after two weeks.

## Degeneration Specimens (Writing that equals not writing, should trigger CE-003 / CE-004 / CE-005 / CE-010 to skip or rewrite)

- ❌ Blind spot writes "be careful about edge cases, there might be issues" — no falsifiable condition (violates CE-003, should skip entire section).
- ❌ Adjacent domain writes "just like organizing a room requires categorization first, state management also requires categorization first" — same tech stack word-shuffling the main text (violates CE-004).
- ❌ Takeaway writes "keep learning, think more" — chicken soup, not actionable (violates CE-005).
- ❌ Blind spot restates what the main answer already said "mid-sized apps usually don't need Redux" — no dimension change (if logical-reasoning already issued a logic chain in the same round, violates CE-013).
