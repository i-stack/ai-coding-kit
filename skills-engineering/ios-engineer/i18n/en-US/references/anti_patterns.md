<!-- last-verified: 2026-05 -->
# iOS Anti-Patterns Library

> This is an English mirror of the authoritative Chinese `references/anti_patterns.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Architecture Anti-Patterns
- Concurrency Anti-Patterns
- UI & State Anti-Patterns
- Networking & Data Anti-Patterns
- Performance Anti-Patterns
- Troubleshooting Anti-Patterns

## Usage Rules
- First determine whether each anti-pattern's "identification criteria" are met; do not label if criteria are not satisfied.
- When matched, output in four sections: "Symptoms → Identification Criteria → Risk → Fix"; the fix must point to verifiable code changes.
- This file is the **anti-pattern library** (identification criteria / risks / fixes). **Review checklists and mergeability judgments** belong to [review_checklists.md](review_checklists.md); use them together — during review, first check against review_checklists.md dimensions, then cross-reference the corresponding anti-pattern entry in this file.

## 1. Architecture Anti-Patterns
### Massive ViewController / Massive ViewModel
Symptoms:
- A controller or ViewModel simultaneously handles rendering, routing, networking, caching, analytics, permissions, and state assembly.

Identification Criteria: A single type handles ≥ 3 categories of responsibilities (e.g., rendering + networking + routing + analytics); or a single class exceeds 600 lines; or has > 20 member variables.

Risks:
- Untestable
- Hard to reuse
- Change one thing, break everything

Fix:
- Extract UseCase, Repository, Coordinator, DataSource, Service.

### Pseudo-Modularization
Symptoms:
- Multiple directories or Packages exist, but dependency directions are chaotic; any module can directly access any implementation.

Identification Criteria: Cross-module direct access to internal / private implementations; or circular dependencies between SPM packages; or module public API ratio > 50%.

Risks:
- Module boundaries are ineffective
- Cannot evolve independently

Fix:
- Consolidate public APIs, correct dependency directions, prohibit cross-module access to internal implementations.

### Universal Manager
Symptoms:
- A single `Manager` handles networking, caching, state sync, and business decisions simultaneously.

Identification Criteria: A single type handles ≥ 3 different responsibilities (networking + caching + business + state sync); or contains ≥ 2 shared states requiring lock protection; or is held as a singleton by ≥ 10 callers.

Risks:
- Single-point bloat
- Uncontrolled responsibilities

Fix:
- Split responsibilities, maintain abstract interfaces, layer by communication, storage, state, and business rules.

## 2. Concurrency Anti-Patterns
### Scattered `Task {}`
Symptoms:
- Tasks are started directly in Views, Cells, callbacks, and utility classes without ownership or cancellation relationships.

Identification Criteria: `Task {}` appears in UIView / Cell / utility classes; or the Task lacks a corresponding cancel trigger chain; or the Task modifies shared state with no owning object (the holder cannot answer "who cancels").

Risks:
- Cancellation fails
- State writeback misalignment
- Lifecycle leaks

Fix:
- Consolidate into structured concurrency with parent-child task relationships.

### `DispatchQueue.main.async` Masking Timing Issues
Symptoms:
- Any UI or state issue gets wrapped in a main-thread async dispatch.

Identification Criteria: New `main.async` commits/PRs only say "fix crash / blank screen" without explaining why the original path wasn't on the main thread; or multiple nested layers of `main.async`; or evidence that async-captured objects were deallocated on a non-main thread.

Risks:
- Problem is deferred, not fixed
- Creates new race condition windows

Fix:
- Clearly define isolation domains, state sources, and writeback timing.

### Abusing `@unchecked Sendable`
Symptoms:
- To eliminate compiler warnings, reference types are marked `@unchecked Sendable` directly.

Identification Criteria: `@unchecked Sendable` is added without an "internal synchronization guarantee" comment; or the class contains mutable `var` properties without lock / actor protection; or the class is concurrently written by multiple tasks.

Risks:
- Real data races disguised as "handled"

Fix:
- Switch to value semantics, actor isolation, or add strict synchronization guarantees with documented rationale.

## 3. UI & State Anti-Patterns
### Scattered State Sources
Symptoms:
- The same page state is independently maintained in View, ViewModel, Service, and cache layers.

Identification Criteria: The same semantic state (e.g., "logged in", "loading", "selected") is independently maintained in ≥ 2 objects; or the UI layer needs manual "sync" of multiple state sources.

Risks:
- State inconsistency
- List misalignment
- Form data corruption

Fix:
- Define a single source of truth with unified state flow and write paths.

### Hardcoded Dimensions for Layout Fixes
Symptoms:
- Pages are fixed using fixed widths/heights, extra spacing, or magic margins.

Identification Criteria: Hardcoded constraint constants ≥ 50 or font sizes ≥ 13 as magic values; or dimensions that should be determined by `intrinsicContentSize` are hardcoded; or layout fix commits only change numbers without changing the hierarchy.

Risks:
- Breaks under localization, extreme font sizes, and rotation

Fix:
- Return to constraint relationships, content-driven sizing, and layout semantics.

### Unstable List Identity
Symptoms:
- `id` is unstable, or index is used as long-term identity.

Identification Criteria: List item id uses `indexPath` / array index / mutable fields (e.g., `unreadCount` / `status` / `updatedAt`); or identity changes when the item updates.

Risks:
- Scroll position loss
- Animation glitches
- Reuse state corruption

Fix:
- Use stable business identifiers as identity.

## 4. Networking & Data Anti-Patterns
### String-Concatenated Requests
Symptoms:
- URLs, Headers, Query parameters, and Bodies are hand-written everywhere.

Identification Criteria: URL / Query / Header uses `+` or string interpolation in ≥ 3 places; or the same endpoint's URL construction logic appears in ≥ 2 files.

Risks:
- Inconsistency
- Untestable
- Hard to audit

Fix:
- Centralize Endpoint and Request construction.

### Error Passthrough to UI
Symptoms:
- Raw `Error.localizedDescription` is displayed directly to users.

Identification Criteria: UI code directly displays `error.localizedDescription` / `error.debugDescription`; or user-visible messages contain HTTP status codes / NSError domains.

Risks:
- Semantic errors
- Poor user experience
- Uncontrolled error boundaries

Fix:
- Establish error layering and UI-facing error mapping.

### Blind Retry
Symptoms:
- Automatic retry on any failure without distinguishing idempotency or business semantics.

Identification Criteria: Write operations (POST / PUT / DELETE) have automatic retry; or retry lacks max attempts or backoff; or business errors (4xx business fail) are included in retry scope.

Risks:
- Duplicate orders
- Duplicate submissions
- Server avalanche

Fix:
- Define finite, traceable retry strategies only for retry-allowed requests.

## 5. Performance Anti-Patterns
### Heavy Work on Main Thread
Symptoms:
- Main thread performs image decoding, rich text parsing, complex sorting, or synchronous I/O.

Identification Criteria: Time Profiler shows main thread single-call duration > 16ms (frame drop) or > 100ms (stall); or `cellForItem` / `scrollViewDidScroll` / `layoutSubviews` performs decode / JSON parse / sort or other O(n)+ operations.

Risks:
- Frame drops
- Slow first screen
- Gesture blocking

Fix:
- Offload non-UI work; control the timing of switching back.

### Sacrificing Correctness for Performance
Symptoms:
- Caching stale state, skipping refreshes, or swallowing exceptions to be "faster".

Identification Criteria: Using cache without defining invalidation conditions; or `catch` blocks swallow exceptions without logging; or refresh code is commented out as "skipping for performance"; or "avoiding duplicate requests" leads to dirty reads.

Risks:
- Data errors
- UI inconsistency

Fix:
- Ensure correctness first, then optimize based on metrics.

## 6. Troubleshooting Anti-Patterns
### Symptom Equals Root Cause
Symptoms:
- The error point, last crash stack frame, or page anomaly location is treated directly as the root cause.

Identification Criteria: Fix PR / commit descriptions stay at "fixed xxx crash" / "defended against xxx nil" without explaining "why xxx happened"; or the fix point is the last crash frame without call chain backtracking.

Risks:
- Fixing the wrong location
- Problem recurs

Fix:
- Backtrack through the complete chain to data, state, concurrency, and lifecycle sources.

### Patch-Style Fixes
Symptoms:
- Adding `if`, delays, overrides, or fallback branches to suppress the problem.

Identification Criteria: Fix code only adds `if` / `guard` / null checks / `try-catch` fallbacks without removing or changing the error source; or the same input path can still trigger the same error after the fix.

Risks:
- Hidden problems accumulate
- Harder to investigate next time

Fix:
- Make structural fixes and provide verification evidence.
