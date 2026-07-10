<!-- last-verified: 2026-07 -->
# cross-model-review Out of Scope

> This is an English mirror of the authoritative Chinese `OUT-OF-SCOPE.md`.
> In case of discrepancies, the Chinese source takes precedence.

This skill is responsible for **adversarial cross-model review of locked plans**, not for plan locking grilling, problem review, code review, or plan execution.

## What Is Not Handled

- **Plan locking**: Grilling the user to lock PLAN.md is the responsibility of `plan-grill` (PG-001~004). cross-model-review only reviews already-locked PLAN.md.
- **Problem review**: The logical validity of the problem itself and true requirements decomposition are handled by `problem-analysis` (PA-001~003), before plan-grill.
- **Review of written code**: Reviewing implemented code (not plans) is handled by `ios-engineer/references/review_checklists.md`. This skill only reviews PLAN.md.
- **Plan execution**: cross-model-review only reviews, does not implement. Implementation is handled by subsequent conversation or ios-engineer skill. No code is written between the two acts.
- **Single-model review**: This skill must be cross-provider. Same-provider review (e.g., Claude reviewing Claude's plan) loses adversarial value and is not performed.

## Trigger Gate

Only triggers when PLAN.md already exists. If no PLAN.md, load plan-grill first.
