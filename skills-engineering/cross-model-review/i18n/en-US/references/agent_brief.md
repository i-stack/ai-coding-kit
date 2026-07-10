<!-- last-verified: 2026-07 -->
# cross-model-review Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Auto-discover available CLIs (codex/gemini/claude), recommend a combination of two different providers and let user choose, reviewer runs read-only outputting VERDICT, raw output and delivery logs all written under current project root directory, main agent arbitrates and writes to PLAN-REVIEW-LOG.md, MAX_ROUNDS without convergence outputs deadlock.

## When to Invoke

- **User trigger**: User says `cross-model-review` / `cross review` / "adversarial review" / "let two models review the plan" / "model debate" / "stress-test PLAN.md"
- **Relay from plan-grill**: After plan-grill locks PLAN.md, user says "let another model review"
- **Prerequisite**: PLAN.md must already exist (produced by plan-grill)

## Key Behaviors

1. Read `SKILL.md` + full text of `references/cross_model_review.md`.
2. Directly probe available CLIs (`command -v codex|gemini|claude` + `--version`; optional auxiliary script in this repository: `skills-engineering/scripts/detect-review-clis.sh`). Stop when available providers < 2.
3. Recommend a combination of two different providers and let user confirm (CMR-002).
4. Reviewer runs read-only (CMR-003): codex `-s read-only`, gemini `--approval-mode plan`, claude `--permission-mode plan`.
5. Output to disk (CMR-003/004): reviewer raw output, intermediate output, and delivery logs must be under current project root directory, recommended `.plan-reviews/<date>-<slug>/raw/`; must not use `/tmp` as reviewer output buffer.
6. Main agent arbitration (CMR-004): collect all selected reviewers each round; only all APPROVED converges; any REVISE must be arbitrated, revised, and recorded in PLAN-REVIEW-LOG.md.
7. MAX_ROUNDS (default 5) without convergence → deadlock (CMR-005), hand to user for adjudication, do not pretend approved.
8. After Resolution, optional archiving (user-triggered): save PLAN.md + PLAN-REVIEW-LOG.md to project root `.plan-reviews/<date>-<slug>/` for reference on similar problems. See references "Archiving" chapter for details.

## When Not to Invoke

- No PLAN.md (run plan-grill first)
- Trivial changes
- User explicitly says "implement directly"
- Available reviewer providers < 2
