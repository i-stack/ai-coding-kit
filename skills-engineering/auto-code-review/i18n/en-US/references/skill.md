---
name: auto-code-review
description: Cross-model code review workflow triggered only by explicit user request. Activated when the user says `/auto-review`, `use auto-code-review`, `start cross-model code review`, or explicitly requests "review and fix". Normal code generation, modifications, or vague "take a look at the code" do NOT trigger this skill. Default is read-only review; only when the user explicitly requests `--fix` or "review and fix" is the main agent allowed to modify code.
locale: auto
supported_locales: [zh-CN, en-US]
---

# Auto Code Review

## Mandatory Entry Point

When this skill is triggered, you MUST read [references/auto_code_review.md](../../../references/auto_code_review.md) in full and execute according to its rules.

- Do NOT substitute the full specification with preambles, Cursor rule summaries, or other secondary summaries.
- Do NOT probe reviewer CLIs, invoke reviewers, or create review archives without explicit authorization in the current request.
- Runtime prerequisites (not distributed with the skill sync package; must be provided by the host environment): `env/review.json` (template: `env/review.json.example`), in-project `.auto-review-config.json`, and `AUTO_REVIEW_*` environment variables. See `AGENT-BRIEF.md` and `docs/auto-code-review.md` for configuration loading priority and field semantics.

## Eight Core Rules

- [ACR-001] **Explicit Authorization Gate**: The skill is entered ONLY when the user explicitly triggers it; completion of code changes is NOT a trigger. Configuration can only control capability availability — it cannot represent authorization for the current request.
- [ACR-002] **Traceable Scope**: Prefer reviewing changes precisely recorded in the current request. When the boundary cannot be proven, ask the user to choose staged or worktree. Do NOT present `git diff HEAD` as "this round's changes".
- [ACR-003] **Reviewer Read-Only**: The reviewer ALWAYS runs in read-only mode, outputting review comments without modifying files.
- [ACR-004] **Layered Write Permissions**: Default is `review-only`; the main agent only triages and reports. Only when the user explicitly specifies `--fix` or "review and fix" may the main agent apply fixes and re-review.
- [ACR-005] **MAX_ROUNDS=3**: `review-only` runs exactly one round; `review-and-fix` runs at most 3 rounds. On non-convergence, output deadlock — do NOT fake a pass.
- [ACR-006] **Post-Authorization Closed Loop**: After explicit trigger, execute review → archive → sync → merge. History recall is now handled by the global `historical-recall` skill, so this skill no longer recalls inline. Archives are written to `.plan-reviews/` and belong only to the authorized review session.
- [ACR-007] **Configurable Reviewer**: Reviewer, rounds, and single-model fallback are all configurable. `AUTO_REVIEW_ENABLED=false` is the capability-level disable switch; `true` does NOT constitute user authorization.
- [ACR-008] **Single-Model Fallback Requires Explicit Permission**: Same-model self-review is NOT performed by default. Fallback occurs only when explicitly allowed by configuration, and logs must note reduced credibility.

## Modes

- `/auto-review`: Read-only review; no workspace modifications.
- `/auto-review --fix`: Review, main agent fixes adopted issues, then re-review.
- Normal implementation requests: do NOT trigger this skill.

## Relationship with Adjacent Skills

| Skill | Role |
|---|---|
| `plan-grill` | Interrogate and lock down PLAN.md (Act 1) |
| `cross-model-review` | Explicit review of PLAN.md (Act 2) |
| **auto-code-review** | User-explicitly-triggered code implementation review (Act 3) |
| `engineering-discipline` | Constrain main agent engineering changes |
| `epistemic-integrity` | Constrain review conclusion evidence and confidence |

## Workflow

```text
Implementation complete → User explicitly triggers → Select scope/mode → Reviewer read-only review
                                                         ├─ review-only: report and archive
                                                         └─ review-and-fix: fix → re-review → archive
```
