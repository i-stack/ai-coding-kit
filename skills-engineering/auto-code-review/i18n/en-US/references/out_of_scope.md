# auto-code-review Out-of-Scope Declaration

This skill does **NOT** handle the following scenarios:

## 1. Plan Review

- Reviewing PLAN.md or implementation plans → use the `cross-model-review` skill.
- This skill only reviews **code implementations**, not plan documents.

## 2. Non-Code Changes

- Pure documentation updates (.md files)
- Minor configuration tweaks (single-line changes)
- Typo fixes, formatting adjustments
- These scenarios are NOT handled by this skill, and review is NOT started automatically.

## 3. Conversations Without Code Changes

- Pure Q&A, explanations, suggestion-type responses
- No actual file modifications produced
- These scenarios do NOT trigger review.

## 4. Not Explicitly Triggered

- Normal code generation, modification completion, or test passing does NOT trigger this skill.
- Only explicit requests such as `/auto-review` or `use auto-code-review` start the workflow.
- `AUTO_REVIEW_ENABLED=true` only indicates capability availability; it does NOT constitute user authorization.

## 5. Cross-Model Review Substitution

- This skill does NOT replace the `cross-model-review` PLAN.md review process.
- The two are complementary: cross-model-review reviews plans, auto-code-review reviews implementations.
- Complete workflow: plan-grill → cross-model-review → implement → auto-code-review.

## 6. Human Review Substitution

- This skill does NOT replace human code review.
- Review results are for agent and user reference only; final decisions are made by the user.
- Deadlocks MUST be escalated to the user for adjudication; no automatic merging.

## 7. Unauthorized Fixes

- `/auto-review` is read-only by default and does NOT authorize the main agent to modify code.
- Only `/auto-review --fix` or explicit "review and fix" enters the fix cycle.

## 8. Non-CLI Reviewer Scenarios

- This skill relies on CLI tools (codex/gemini/claude) for cross-model review.
- Direct API calls to models are NOT supported (unless wrapped through CLI).
- GUI tools or web-based reviewer interfaces are NOT supported.
