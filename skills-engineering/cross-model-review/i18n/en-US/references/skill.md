<!-- last-verified: 2026-07 -->
# Skill: Cross Model Review

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: cross-model-review
description: Adversarial cross-model review of locked PLAN.md — auto-discover available CLIs (codex/gemini/claude), recommend a combination of two different providers and let user choose, reviewer runs read-only outputting VERDICT:APPROVED|REVISE, main agent arbitrates and records reasoning in PLAN-REVIEW-LOG.md, MAX_ROUNDS without convergence outputs deadlock. Based on chaseai-yt/grill-me-codex (MIT) Act 2 approach.
locale: zh-CN
supported_locales: [zh-CN, en-US]
---

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/cross_model_review.md](references/cross_model_review.md) and execute according to its terms.

- Do not substitute the full text with preamble, Cursor rule summaries, or other secondary summaries.
- This skill is Act 2 of `plan-grill`; after plan-grill locks PLAN.md, this skill takes over.

## Five Core Rules

- [CMR-001] **Auto-discover reviewers**: Directly probe availability, versions, non-interactive and read-only mode support for three CLIs: codex/gemini/claude (using `command -v <cli>` + `<cli> --version`; optional auxiliary script in this repository: `skills-engineering/scripts/detect-review-clis.sh`). When available providers < 2, stop and prompt to install; do not fabricate cross-model.
- [CMR-002] **Recommended combination + user selection**: From available CLIs, recommend a combination of two different providers (e.g., codex + gemini) and let user confirm. Do not silently choose for the user.
- [CMR-003] **Reviewer read-only**: Each reviewer must run in read-only mode — codex uses `-s read-only`, gemini uses `--approval-mode plan`, claude uses `--permission-mode plan`. Reviewer does not write code, only outputs `VERDICT: APPROVED` or `VERDICT: REVISE` + specific modification suggestions.
- [CMR-004] **Main agent arbitration**: The main agent (Claude/Codex, depending on host) is the final arbitrator. Each round must collect verdicts from all selected reviewers; reviewer raw output, intermediate output, and delivery logs must be saved under the current project root directory (recommended `.plan-reviews/<date>-<slug>/raw/`); must not use `/tmp` as reviewer output buffer. Only all `APPROVED` can converge; any `REVISE` must be arbitrated and proceed to revision/next round. Adopt criticisms with evidence, reject criticisms that don't hold with reasoning written, recorded in `PLAN-REVIEW-LOG.md`.
- [CMR-005] **MAX_ROUNDS + deadlock**: When MAX_ROUNDS (default 5) still not converged, output deadlock — list each unresolved point + main agent's counter-position, hand to user for adjudication. Do not pretend approved.

Details in [references/cross_model_review.md](references/cross_model_review.md). Full running example for login rate limiting scenario in `examples/regression-login-rate-limit.md`.

## When to Load

- **Default trigger**: User says `cross-model-review` / `cross review` / "adversarial review" / "let two models review the plan" / "model debate" / "stress-test PLAN.md" / "review PLAN.md" / "let Gemini/Codex/Claude review the plan".
- **Relay from plan-grill**: After plan-grill locks PLAN.md, user says "let another model review" then load this skill.
- **Skip**: No PLAN.md (run plan-grill first); trivial changes; user explicitly says "implement directly".

## Division of Labor with Adjacent Skills

| Skill | Division |
|-------|------|
| `plan-grill` (PG-001~004) | Grilling to lock PLAN.md (Act 1) |
| **cross-model-review (this skill)** | Adversarial cross-model review of PLAN.md (Act 2) |
| `problem-analysis` (PA-001~003) | Problem review, before plan-grill |
| `epistemic-integrity` (GR-011~013) | Epistemic grounding discipline during main agent arbitration |
