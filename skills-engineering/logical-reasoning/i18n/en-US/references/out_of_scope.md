<!-- last-verified: 2026-05 -->
# logical-reasoning Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill constrains the argumentation quality of AI's **own responses** (inward); not responsible for testing user question logic or conclusion truthfulness.

## What Is Not Handled

- **User question logic testing**: Handled by `problem-analysis` (PA-001).
- **Conclusion grounding with external world**: Handled by `epistemic-integrity` (GR-011/012).
- **Cognitive Adversary Mode**: Handled by `ios-engineer/references/cognitive_adversary_mode.md` (challenging user conclusions).
- **Engineering output structure**: Handled by `engineering-discipline` (GR-004 four-section).

## Boundary Explanation

GR-010 is an inward constraint:
- **Logic chain traceable**: Every reasoning step can trace back to upstream premises
- **Four-layer distinction**: Facts / Inferences / Recommendations / Speculations
- **Strength matching**: Conclusion strength does not exceed evidence strength
- **Non-contradictory**: No internal self-contradiction within the same response

Orthogonal to GR-011/012 — a response can be internally logically consistent yet not match the external world, or can be directionally correct yet have messy argumentation structure. When both are triggered, they execute in parallel.
