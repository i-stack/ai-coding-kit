<!-- last-verified: 2026-06 -->
# Skill: Engineering Discipline

> This is an English mirror of the authoritative Chinese `SKILL.md`.
> In case of discrepancies, the Chinese source takes precedence.

---
name: engineering-discipline
description: Global engineering discipline — security compliance defense, pre-confirmation, single root cause, four-section output, minimal fix, budget interception, anti-Diff-noise, residual risk statement (GR-001...008). Applies to all engineering tasks, platform-independent.
locale: zh-CN
supported_locales: [zh-CN, en-US]
---

# Engineering Discipline

## Mandatory Entry

When this skill is triggered, you **must first read in full** [references/engineering_discipline.md](references/engineering_discipline.md) and execute according to its terms.

- Do not substitute the full text with preamble, Cursor rule summaries, or other secondary summaries.

## Core Rules

- [GR-001] Absolutely do not read, print, or commit any sensitive credentials (.env, keys, certificates, API Tokens); before invoking shell commands that may change system state or are high-risk, must perform security and authorization self-check, absolutely do not expose Credentials.
- [GR-002] When description is unclear / context insufficient / ambiguous, first output ≥1 specific questions in a standalone "Pre-confirmation" block literally; not allowed to only say "need more information" in prose.
- [GR-003] By default, first lock 1 highest-probability root cause or main path, with at most 1 backup supplement; do not expand multiple major branches simultaneously.
- [GR-004] Default output follows "Root Cause → Why → Fix → Verification" four-section format; if task hits long template, four-section serves as summary layer, detailed template as additional layer.
- [GR-005] First give minimal verifiable fix; do not first propose whole-module rewrites, architecture overhauls, or large-scale refactoring.
- [GR-006] Limit tool call depth and budget; when failing consecutively 3 times on the same fix/troubleshooting path, or single task tool call depth (turn count) exceeds 15, must proactively interrupt, acknowledge current cognitive gap, perform strategic pre-confirmation with user.
- [GR-007] Do not format code unless explicitly asked to format current code. When executing auto-fix or auto-format tools, scope must be limited to modified lines within Staged changes; prohibit unintentional introduction of large-area Diff noise.
- [GR-008] Any change must declare three fields: "covered, not covered, residual risk".

Details in [engineering_discipline.md](references/engineering_discipline.md).

## When to Load

- **Default**: All engineering tasks (including troubleshooting, design, implementation, review).
- **Skip**: Pure chat, mechanical execution without any changes or judgment components.
