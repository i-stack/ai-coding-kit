<!-- last-verified: 2026-06 -->
# engineering-discipline Agent Invocation Guide

> This is an English mirror of the authoritative Chinese `AGENT-BRIEF.md`.
> In case of discrepancies, the Chinese source takes precedence.

## One-line Description

Global engineering discipline — security compliance defense, pre-confirmation, single root cause, four-section output, minimal fix, budget interception, anti-Diff noise, residual risk statement (GR-001…008). Applies to all engineering tasks, platform-independent.

## When to Invoke

**Load by default**: All engineering tasks (including troubleshooting, design, implementation, review).

## Key Behaviors

1. **[GR-001]** Never read/print/commit sensitive credentials; security self-check before high-risk shell commands.
2. **[GR-002]** When description is unclear, first output standalone "Pre-confirmation" block.
3. **[GR-003]** Lock 1 highest-probability root cause, at most 1 backup.
4. **[GR-004]** Output in "Root Cause → Why → Fix → Verification" four-section format.
5. **[GR-005]** First give minimal verifiable fix.
6. **[GR-006]** Proactively interrupt confirmation after 3 consecutive failures or turn count exceeds 15.
7. **[GR-007]** Do not format code (unless explicitly requested); auto-fix limited to Staged changes.
8. **[GR-008]** Any change declares "covered/not covered/residual risk".

## When Not to Invoke

- Pure chat
- Mechanical execution without any changes or judgment components
