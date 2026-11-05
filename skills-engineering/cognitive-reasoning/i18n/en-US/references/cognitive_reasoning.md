<!-- mirror-of: ../../../references/cognitive_reasoning.md -->
<!-- last-verified: 2026-08 -->
<!-- sha256: c3c034889eb2fce2eb02ef505a0164a9c82e43aabeb67d95cee64f8a0945415f -->

# cognitive-reasoning Primary Reference

> Primary reference for `cognitive-reasoning` (Cursor .mdc generation and quick index). Full truth in the per-domain files below; on conflict, the per-domain file wins.

`cognitive-reasoning` unifies four cognitive/reasoning disciplines; rule IDs are globally unique and bidirectional-consistent (validate-skill-behavior.sh Check 2).

## Four domains & detail files

| Domain | Rule IDs | Detail file | Trigger |
|--------|----------|-------------|---------|
| Cognitive Adversary Mode (Tier 2, anti-flattery) | CAM-001~005 | [cognitive_adversary_mode.md](cognitive_adversary_mode.md) | technical decision/architecture/root-cause/review/strong conviction/explicit "don't flatter" |
| Logical reasoning (inward) | GR-010 | [logical_reasoning.md](logical_reasoning.md) | any reply with judgment |
| Epistemic integrity (outward) | GR-011~013 | [epistemic_integrity.md](epistemic_integrity.md) | factual claim / explanatory answer |
| Cognitive expansion (post-answer) | CE-001~013 | [cognitive_expansion.md](cognitive_expansion.md) | Tier 0 gate hit / `【深潜】` |

Format calibration: [examples.md](examples.md); rule index: [rule_index.md](rule_index.md).

## Mandatory entry
On trigger, read the matching detail file in full; do not substitute this index or preamble managed block for the full text.

## Key discipline notes
- CAM (toward user): restate → strongest refutation → hidden assumptions → failure/falsifiability → flattery self-check; say "uncertain" when evidence lacks; >70% confidence needs falsifiability.
- GR-010 (inward): conclusions trace to premises; fact/inference/advice/speculation layered; high-risk emits `逻辑链` block.
- GR-011~013 (outward): unverified ≠ known; reduce confidence + verify in high-risk zones; fact-class → verify not derive; high-risk fact emits `验证锚点` block.
- CE-* (post): Tier 0 only when gate hit (judgment + falsifiable blind spot); Tier 2 hit suppresses Tier 0 (mutual exclusion extends to preamble).

## Relation to engineering-discipline
This skill governs cognitive/reasoning *quality*; engineering delivery structure is `engineering-discipline` (GR-001~008). When CAM active, its fields already carry `逻辑链`/`验证锚点` calibration; not emitted as separate block (see GR-004 multi-block merge) but output as-is.
