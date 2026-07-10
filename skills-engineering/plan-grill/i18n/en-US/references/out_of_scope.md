<!-- last-verified: 2026-07 -->
# plan-grill Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **implementation solution grilling and locking after requirements clarity gate**, not for problem logic review, code review, or cross-model adversarial.

## What Is Not Handled

- **Problem itself review**: Whether the problem contains logical errors, contradictory premises, real requirements decomposition is handled by `problem-analysis` (PA-001/002/003). plan-grill starts after problem-analysis completes.
- **Adversarial cross-model review**: After PLAN.md is locked, adversarial review by selected reviewers is `cross-model-review`'s responsibility. plan-grill only produces PLAN.md, does not invoke reviewers.
- **Review of written code**: Reviewing implemented code is handled by `ios-engineer/references/review_checklists.md` or `cross-model-review` (reviews plans not code).
- **Executing the plan**: plan-grill only locks the plan, does not execute. Execution is handled by subsequent conversation or ios-engineer skill.

## Trigger Gate

After problem-analysis completes, automatically execute PG-000 gate. Only enter grilling when blocking decisions exist that cannot be found and would substantially alter outcomes; explicit grill trigger phrases force entry.
