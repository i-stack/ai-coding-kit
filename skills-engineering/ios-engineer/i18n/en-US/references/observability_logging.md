<!-- last-verified: 2026-06 -->
# Observability & Logging

> This is an English mirror of the authoritative Chinese `references/observability_logging.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Observation Targets
- Log Layering
- Required Fields
- Performance Observation
- Troubleshooting Evidence
- Analytics Discipline
- Privacy & Security
- Common Anti-Patterns

## Usage Rules
- When existing logs, metrics, or evidence chains are insufficient to locate root cause or verify fixes, first supplement **minimum necessary** observability (not deploy a full observation system); if evidence already supports the minimal fix, do NOT force new logs or analytics.
- Problems without logs, metrics, or evidence chains cannot be claimed as "located".
- Logs and analytics MUST serve troubleshooting, verification, and regression; do NOT become noise accumulation.

## Observation Targets
Observability MUST answer:
- What happened
- At what timing
- Triggered by whom
- On which thread / Actor / Task
- What state and pages were affected
- Whether it is reproducible

## Log Layering
Fixed four layers:
- Input logs: user actions, external events, API responses
- State logs: state transitions, key property changes, task creation and cancellation
- Lifecycle logs: page enter/exit, object init/deinit, task start/end
- Error logs: failure branches, exception paths, retries, degradation, assertion info

Requirements:
- Logs MUST be traceable along the same business chain.
- Same-chain logs MUST carry a unified identifier.
- Critical failure paths MUST NOT only log a single "it failed" useless entry.

## Required Fields
Critical logs MUST include at least:
- Event name
- Module name / page name
- Request ID / task ID
- Current thread or Actor context
- Key input parameter summary
- Key state changes
- Result or error classification
- Timestamp

## Performance Observation
- Launch, first screen, page transitions, list scrolling, image loading, network requests MUST be quantifiable.
- Performance data MUST distinguish cold start, warm start, weak network, low-end device.
- Critical paths need `OSLog`, Points of Interest, or MetricKit for observation.

Common metrics that MUST be observed:
- Launch duration
- First screen interactive time
- List scroll frame rate
- Main thread hotspots
- Peak memory
- Request duration and failure rate

### Performance Evidence Tools (single source of truth; other files reference here)
- **Instruments**: Apple's official performance analysis suite; the following tools are its template instances.
- **Time Profiler**: locate CPU and main thread hotspots; aggregates sampling by call stack; ideal for "which function takes longest on main thread".
- **Core Animation**: observe frame rate, off-screen rendering, blending layers, and rasterization pressure; ideal for "what type of rendering cost causes scroll stutter".
- **Allocations**: track heap object allocation and deallocation; ideal for "why is memory growing".
- **Leaks**: auto-detects memory leaks; ideal for "which object is the leak point".
- **Memory Graph** (Xcode Debug Navigator): visualizes object reference graph; ideal for "where is the retain cycle".
- **Points of Interest + OSlog**: mark signal points in code, visible on Instruments timeline; ideal for marking critical path timing (e.g., "first screen start" → "first screen complete").
- **MetricKit**: collects crash, stutter, energy data from production, delivered next day; ideal for observing real user performance trends; not for local real-time debugging.

## Troubleshooting Evidence
- During bug investigation, logs MUST cover input, state, lifecycle, thread/Actor, and error branches.
- Concurrency issues MUST record task creation, cancellation, writeback, and discard timing.
- List issues MUST record refresh, pagination, reuse, writeback, and identity changes.
- Crash issues MUST correlate call stack, key state, and last valid operation chain.

## Analytics Discipline
- Analytics are for behavior analysis, not a substitute for troubleshooting logs.
- Analytics names, parameters, and timing MUST be stable; do NOT arbitrarily rewrite.
- Same business action is tracked only once as the main event; do NOT bombard with duplicates.
- Analytics fields MUST have clear business semantics; do NOT pile up unexplained parameters.

## Privacy & Security
- Do NOT log tokens, passwords, ID numbers, full phone numbers, or complete payment information.
- When troubleshooting requires logging, only record desensitized summaries.
- Observation of user privacy data MUST comply with product and compliance requirements.

## Common Anti-Patterns
- Only printing `error` in `catch`
- Logs without chain identifiers; cannot be correlated
- Concurrency issues without recording task creation, cancellation, writeback
- Performance optimization without baseline data
- Confused analytics and logging responsibilities
- Printing sensitive data for troubleshooting
