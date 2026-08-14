<!-- mirror-of: ../../../references/examples.md -->
<!-- last-verified: 2026-08 -->
<!-- sha256: a3febe43a5757eee128dbc3b5773bb9b1bdf7dc57e8482062cf1ee1cbebde9e9 -->

# Cognitive Expansion Examples (before / after)

> Format-calibration anchor for `cognitive-reasoning`. Rule truth in `rule_index.md`; this doc does not introduce new rule IDs, only references `CE-NNN`.

## Example 1: Tier 0 tail note after a normal answer (CE-001~005, CE-010)
User: "Redux or Context for state in a mid-size React app?"
Main answer (excerpt): layer by state type — server cache via React Query, global UI state via Context, only domain state needing time-travel/predictable dispatch uses Redux; mid-size apps usually don't need Redux.
Tail note (gate hit: tradeoff + falsifiable blind spot):
- Reframe (CE-002): state-management choice is fundamentally "lifecycle & ownership of state", not "which library".
- Blind spot (CE-003): if in 3 months you frequently write selectors/utils to bypass Context re-renders, the assumption "Context suffices for mid-size apps" was wrong — Context fine-grained-update cost was underestimated.
- Neighbor (CE-004): in distributed systems "state ownership" also determines consistency boundaries (Conway: team boundaries map to state boundaries) — same mechanism as frontend state layering.
- Takeaway (CE-005): before next choice, ask "who will mutate this state, and how often?" then decide the ownership layer.

## Example 2: user writes 【深潜】 Tier 3 (CE-006~009, plus CE-001~005)
User: "【深潜】why does our team's code review always become a formality?"
Main answer (excerpt): formalization comes from incentive misalignment + Goodhart — once "reviews passed" is the metric, reviewers trend to quick LGTM.
Tier 0 + Tier 3:
- Reframe / Blind spot / Neighbor / Takeaway (as above, plus)
- Mental model (CE-007): Goodhart's Law (when a measure becomes a target, it ceases to be a good measure).
- Cross-domain analogy (CE-008): education "teaching to the test" replaces literacy with scores — mechanism同源 with review-as-formality (metric usurps goal), not a synonym restatement.
- Verification action (CE-009): within 7 days change the review template from "LGTM / Request changes" to "top 1 risk + 1 verifiable improvement", observe quality over 2 weeks.

## Degenerate specimens (writing = not writing; trigger CE-003/004/005/010 to omit or rewrite)
- ❌ Blind spot "watch out for edge cases, might have problems" — no falsifiability (violates CE-003, omit entire note).
- ❌ Neighbor "like tidying a room by sorting first, state management also sorts first" — synonym restatement of main (violates CE-004).
- ❌ Takeaway "keep learning, think more" — broth, not actionable (violates CE-005).
- ❌ Blind spot restates main answer's "mid-size apps usually don't need Redux" — no new dimension (violates CE-013 if logical-reasoning block already emitted same turn).
