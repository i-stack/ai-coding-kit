<!-- mirror-of: ../../../references/rule_index.md -->
<!-- last-verified: 2026-11 -->
<!-- sha256: 25bf9f93e6e2a5224d41def8fac522d021f8e1777c2c78738a5c21efb89c32a4 -->

# Rule Index (cognitive-reasoning)

Unique rule IDs owned by this skill. Mechanical check (validate-skill-behavior.sh Check 2) requires SKILL.md declared IDs ↔ this file active lines bidirectional consistency.

## CAM (Tier 2)
- [CAM-001] anti-flattery activation
- [CAM-002] mechanical steps
- [CAM-003] output schema
- [CAM-004] forbidden behaviors
- [CAM-005] confidence ceiling

## GR-010
- [GR-010] traceable logic chain / fact-inference layering / calibrated strength / logic-chain block

## GR-011~013
- [GR-011] anti-hallucination grounding
- [GR-012] verification methodology
- [GR-013] truth-seeking method boundary

## CE-001~013
- [CE-001] Tier 0 gate
- [CE-002] reframe
- [CE-003] blind spot (falsifiable, hard gate)
- [CE-004] neighbor (mechanism-related, no synonym)
- [CE-005] takeaway (actionable)
- [CE-006] Tier0-Tier2 mutual exclusion extends to preamble lightweight calibration section
- [CE-007] mental model
- [CE-008] cross-domain analogy guardrails
- [CE-009] 7-day verification action
- [CE-010] flattery self-check
- [CE-011] skip conditions
- [CE-012] neighboring-domain pool
- [CE-013] dedup vs cognitive-reasoning logical chain (GR-010)

## Cross-skill metadata field semantics

`engineering-discipline`, `problem-analysis`, `doc-hygiene` and `learning-loop` each table `owner / scope / phase / precedence / conflicts_with / merges_into / field_owner` in their `references/rule_index.md` and point here for field semantics. Authoritative definitions:

| Field | Meaning |
|-------|---------|
| `owner` | The skill that owns this rule's authoritative text; matches that skill's SKILL.md frontmatter. |
| `scope` | Applicability; every currently registered rule is `global` (platform/language-agnostic). |
| `phase` | Stage in reply construction: `timing` (trigger/sequencing gate), `structure` (output shape/format), `evidence` (evidence and inference constraints), `safety` (safety/authorization boundary). |
| `precedence` | A number used to rank this rule against whatever `conflicts_with` names, higher wins; used by `.agents/composition.md`'s conflict resolution to turn "safety > truth > problem > structure" into comparable numbers. Only consulted when `conflicts_with` is non-empty and a real same-spot conflict exists; values are currently set relative to neighboring rules within the same skill and `phase`, with no cross-skill unified scale yet — new rules should match the order of magnitude of nearby rules in the same `phase`, not assume direct comparability with another skill's same-named `phase`. |
| `conflicts_with` | Other rule IDs this rule may conflict with over the same piece of content; every currently registered rule is `[]` (no registered conflict pairs yet). |
| `merges_into` | Which mechanical block (e.g. `逻辑链`/`验证锚点`/four-part answer) this rule's output field ultimately merges into; currently a reserved column, every registered rule is `[]` — the actual merge mapping still lives as prose in `engineering-discipline` GR-004's "multi-block merge" section and has not been itemized into this column. |
| `field_owner` | When a rule exclusively names a specific field of a mechanical block (e.g. "covered" / "real requirement"), register it as `{field: owner-skill}`; rules with no exclusive field register `{}`. |
