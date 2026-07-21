# auto-code-review Agent Invocation Guide

## One-Line Description

User-explicitly-triggered cross-model code review; read-only by default; main agent may fix only when `--fix` is explicitly specified.

## When to Invoke

- Invoke: `/auto-review`, `use auto-code-review`, `start cross-model code review`.
- Invoke with fix authorization: `/auto-review --fix`, `review and fix`.
- Do NOT invoke: normal code generation/modification completed, pure Q&A, vague "take a look at the code".

## Key Behaviors

1. Read `SKILL.md` and `references/auto_code_review.md` in full.
2. Confirm explicit trigger exists in the current session; distinguish `review-only` vs `review-and-fix`.
3. Load `env/review.json`, `.auto-review-config.json`, `AUTO_REVIEW_*`; configuration does NOT substitute user authorization.
4. Confirm review scope: precise changes from the current request; otherwise ask the user to choose staged or worktree.
5. History recall is handled by the global `historical-recall` skill, so invoke the reviewer directly in read-only mode (no inline recall).
6. `review-only` only triages, reports, and archives — no code modifications.
7. `review-and-fix` allows the main agent to fix and re-review, up to 3 rounds.
8. After archiving, best-effort execute sync + merge.

## When NOT to Invoke

- Normal code generation or modification completed.
- User has not explicitly requested the auto-code-review workflow.
- `AUTO_REVIEW_ENABLED=false`.

## Configuration Options

Priority: `env/review.json` → `.auto-review-config.json` → `AUTO_REVIEW_*`.

| Environment Variable | Default | Meaning |
|---|---|---|
| `AUTO_REVIEW_ENABLED` | `true` | Capability switch; does NOT mean current request is authorized |
| `AUTO_REVIEW_REVIEWER` | auto-select | Single reviewer |
| `AUTO_REVIEW_REVIEWERS` | auto-select | Reviewer list |
| `AUTO_REVIEW_MAX_ROUNDS` | `3` | Maximum rounds for `review-and-fix` |
| `AUTO_REVIEW_ALLOW_SELF_REVIEW` | `false` | Whether single-model fallback is allowed |

Reference template: `env/review.json.example`.

Archive contains `QUESTION.md`, `RESPONSE.md`, `REVIEW-LOG.md`, `diff.patch`, and `raw/`.

## Permission Boundaries

- Reviewer is ALWAYS read-only.
- `/auto-review` does NOT authorize the main agent to write files.
- `/auto-review --fix` authorizes the main agent to fix issues within the current review scope.
- `AUTO_REVIEW_ENABLED=true` only means the capability is available; it is NOT persistent authorization.

Plan review still uses `cross-model-review`.
