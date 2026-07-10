<!-- last-verified: 2026-06 -->
# Root Cause Fix Iron Rule

> This is an English mirror of the authoritative Chinese `references/root_cause_enforcement.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For the following tasks:
- Root-cause investigation and fix assessment for troubleshooting / bugs / intermittent issues / Crashes
- Judging during code review or solution review whether changes only suppress symptoms, or miss evidence and impact scope
- Confirming before changes go live that impact scope, unverified paths, and residual risk explicit declarations have been checked

This file only defines troubleshooting discipline, evidence standards, and pseudo-fix prohibitions. General output templates belong to SKILL.md core iron rules; tool budgets belong to [mcp_control.md](mcp_control.md); this file does not redefine them.

## Table of Contents
- Core Principles
- Standard Troubleshooting Flow
- Explicitly Prohibited "Pseudo-fixes"
- Evidence Requirements
- Side Effects Must Be Assessed After Fix
- Verification Requirements

All troubleshooting, fix, and refactoring suggestions must comply with this file.

## Core Principles
- No evidence, no conclusion.
- No boundaries, no fix start.
- No root cause, no patch commit.
- No verification, no completion declaration.
- When fixing, must explicitly list: checked impact scope (which related modules / states / concurrency paths were examined), unverified paths (which may be related but not reproduced or tested), residual risk (what would happen if an unverified path has problems). Do not promise "no new risks at all".
- Default to pursuing 1 highest-probability root cause first; do not expand multiple large branches simultaneously consuming context and tokens.

## Standard Troubleshooting Flow
### 1. Define Problem Boundary
Before starting, must clarify:
- What is the phenomenon
- What are the trigger conditions
- How large is the impact scope
- Is it stably reproducible
- Device, system version, network environment, and concurrency environment

### 2. Build Evidence Chain
Must gather evidence from at least the following dimensions:
- Call chain
- State flow
- Lifecycle
- Thread / Actor / Task context
- Memory reference relationships
- Logs, breakpoints, call stacks, Instruments

Evidence strategy:
- Prefer filling evidence that best distinguishes primary hypothesis from secondary hypotheses; do not lay out all possibilities at once.
- If current evidence is insufficient to distinguish multiple directions, first ask 1 most critical confirmation question rather than expanding lengthy guesses in parallel.

Pre-confirmation question dimensions (GR-002 landing point; when information is insufficient, list ≥1 items as independent "Pre-confirmation" block literally):
- Device model: iPhone / iPad model (affects hardware performance tier / screen size / memory tier / Pro Motion).
- System version: iOS / iPadOS major version (affects available API, concurrency model, SwiftUI behavior baseline).
- Runtime environment: device vs simulator / Debug vs Release / whether TestFlight.
- Reproduction conditions: always reproducible / intermittent / specific path trigger; minimal reproduction steps; first occurrence version / time.
- Attempted solutions: fixes the user has already verified / ruled out (avoid repeating ineffective paths).
- Affected scope: single user / partial users / all users; production vs dev; whether there are user reports or monitoring data.

Follow "necessary for distinguishing primary hypothesis" principle; only ask minimum necessary items; do not throw all six at the user.

### 3. Trace Back Along Full Chain
Fixed trace-back along the following chain:

```text
Input source -> Data transformation -> State management -> Concurrency boundary -> Lifecycle -> UI rendering -> User-visible phenomenon
```

Prohibit only patching at the error point or View layer.

### 4. Implement Structural Fix
Fix falls at:
- Architecture boundary
- State model
- Data flow
- Concurrency isolation
- Lifecycle management

### 5. Verify and Document
After fix, must complete:
- Reproducible verification path
- Pre/post fix comparison evidence
- Necessary tests

## Explicitly Prohibited "Pseudo-fixes"
All of the following are judged as masking the problem (iOS troubleshooting-specific; not listed separately in anti_patterns.md):
- Repeatedly calling `reloadData`, `setNeedsLayout`, `layoutIfNeeded`
- Adding temporary boolean flags to suppress symptoms

If degradation strategy is truly needed, must first explain the real root cause and why only degradation is possible at this stage.

Broader troubleshooting anti-patterns (phenomenon equals root cause, patch-style fix: adding guard if, delay, fallback branch, retry by luck, DispatchQueue.main.async masking timing) refer to [anti_patterns.md](anti_patterns.md) §6 "Troubleshooting Anti-patterns".

## Evidence Requirements
### Minimum Log Coverage
| Category | Description |
|------|------|
| Input | Parameters, external events, server responses |
| State | State transitions, key property changes |
| Context | Thread, Actor, Task, queue |
| Lifecycle | `init`, `deinit`, page lifecycle |
| UI Trigger | Refresh source, binding update, reuse timing |
| Exception Path | `guard`, `catch`, failure branches |

### Conclusion Requirements
- Phenomenon does not equal root cause.
- Crash point does not equal root cause; the last error stack frame is often just a victim.
- Root cause must explain "why it happens" and "why at this timing".

> Concurrency-related evidence chain (task creation / cancellation / stale writeback) modeling see [swift_concurrency.md](swift_concurrency.md); log layering, mandatory fields, chain identifiers see [observability_logging.md](observability_logging.md).

## Side Effects Must Be Assessed After Fix
- Does it change state flow and business semantics
- Does it introduce new races or thread-switching issues
- Does it affect performance, scrolling, launch, or power consumption
- Does it affect object deallocation, task cancellation, and reuse chains
- Does it impact other pages or shared components
- Does fixing the current issue introduce new bugs or regressions

## Verification Requirements
Use one or more of the following in combination:
- Unit tests
- Integration tests
- Device reproduction
- Log breakpoints
- Memory Graph
- Instruments
- Concurrency checking tools
