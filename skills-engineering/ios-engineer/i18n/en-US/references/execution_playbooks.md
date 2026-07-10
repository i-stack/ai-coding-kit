<!-- last-verified: 2026-05 -->
# Execution Playbooks

> This is an English mirror of the authoritative Chinese `references/execution_playbooks.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- When encountering complex tasks, MUST first select the corresponding playbook, then enter analysis and implementation.
- Playbooks define execution order, not background knowledge.
- Do NOT skip the "evidence gathering, boundaries, verification" three steps.
- Default: expand only the currently selected playbook; do NOT apply multiple playbooks in parallel.
- When outputting, prioritize keeping "current step, next step, final verification goal" visible; do NOT recite the entire playbook to the user.
- For any playbook involving concurrency models, availability APIs, SwiftUI behavior, or migration suggestions, MUST confirm `IPHONEOS_DEPLOYMENT_TARGET` and `SWIFT_VERSION` before entering step 1; when version is unknown, do NOT give specific API choices or concurrency mode advice.

> Troubleshooting playbooks also follow [root_cause_enforcement.md](root_cause_enforcement.md) root cause discipline; concurrency / refactoring / migration playbooks also follow [migration_strategy.md](migration_strategy.md) risk gates.

## Table of Contents
- Taking Over Legacy Pages
- Systematic Investigation of Recurrent Intermittent Crashes
- Performance Specialization
- Concurrency Architecture Migration
- Large-Scale Refactoring

## Taking Over Legacy Pages
Scenarios:
- Oversized ViewController / ViewModel
- Scattered state
- UIKit / SwiftUI mixed legacy pages

Steps:
1. Define page boundaries: what it's responsible for, what it's not.
2. Identify state sources: local state, remote state, cached state, navigation state.
3. Flag out-of-boundary code: networking, routing, caching, analytics, permissions, formatting.
4. Set minimal refactoring goals: first split state, then dependencies, then structure.
5. Define migration phases: big-bang refactoring is NOT allowed.
6. Add tests and regression paths.

Deliverables:
- Page boundaries
- Phase order
- Regression scope

## Systematic Investigation of Recurrent Intermittent Crashes
Scenarios:
- Hard-to-reproduce crashes
- Intermittent production anomalies
- Random state corruption

Steps:
1. Define symptoms: crash point, frequency, device, OS version, trigger conditions.
2. Build evidence chain: logs, call stacks, state flow, lifecycle, thread/Actor.
3. Distinguish crash point from root cause.
4. Backtrack from input source → data transformation → state management → concurrency boundary → lifecycle → UI rendering.
5. Make structural fixes; do NOT use delays, retries, or null-check patches.
6. Provide fix verification loop and side effect assessment.

Deliverables:
- Root cause
- Pre/post fix evidence
- Reproduction and regression paths

## Performance Specialization
Scenarios:
- Slow launch
- List stutter
- Heavy page refresh
- Abnormal memory growth

Steps:
1. Define metrics: launch time, FPS, main thread duration, peak memory, CPU.
2. Lock down paths: cold start, warm start, first screen, scrolling, page switching, background to foreground.
3. Gather evidence with tools: Time Profiler, Core Animation, Memory Graph, MetricKit.
4. Find the heaviest hotspot; do NOT tackle multiple root causes simultaneously.
5. Define optimization actions: delete, offload, async, cache, slim down.
6. Compare pre/post optimization data; verify correctness and UX haven't regressed.

Deliverables:
- Baseline
- Hotspots
- Before/after comparison

## Concurrency Architecture Migration
Scenarios:
- Callback to async/await migration
- GCD to structured concurrency migration
- Serial queue to actor migration

Steps:
1. List current concurrency model: who creates tasks, who writes state, who switches to main thread.
2. List shared mutable state and cross-domain data passing.
3. Design isolation domains first, then select `@MainActor`, `actor`, `TaskGroup`, `async let`.
4. When bridging legacy interfaces, ensure resume is called exactly once.
5. Build cancellation chains to prevent stale result writeback.
6. Confirm migration success via compile checks, device behavior, and cancellation verification.

Deliverables:
- Isolation model
- Migration order
- Cancellation and writeback verification

## Large-Scale Refactoring
Scenarios:
- Module splitting
- Navigation rebuild
- State model rebuild
- Networking layer restructure

Steps:
1. Define refactoring goals and explicit non-goals.
2. Write decision records comparing candidate solutions.
3. Phase division: build abstractions, migrate callers, delete old implementations, add tests.
4. Identify high-risk modules and rollback points.
5. Perform behavioral consistency verification per phase.
6. Clean up legacy compatibility layers last.

Deliverables:
- Decision record
- Phase plan
- Per-phase verification method
