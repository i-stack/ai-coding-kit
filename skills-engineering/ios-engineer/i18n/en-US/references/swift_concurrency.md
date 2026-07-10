<!-- last-verified: 2026-05 -->
# Swift Concurrency Architecture

> This is an English mirror of the authoritative Chinese `references/swift_concurrency.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For designing, implementing, and reviewing:
- `async/await`, `Task`, `TaskGroup`
- `@MainActor`, `actor`, `Sendable`
- Legacy callback API migration
- Task cancellation, state sync, concurrency bug investigation

## General Principles
- Understand concurrency issues as "isolation, ownership, cancellation, ordering" problems, not "thread switching tricks".
- MUST use structured concurrency.
- UI state and UI updates MUST be constrained by `@MainActor`.
- MUST review shared mutable state across concurrency domains.

## Mandatory Rules
### Actor & Isolation
- Shared mutable state MUST be placed in an `actor` or converted to immutable value semantics.
- Not every object should be marked `@MainActor`; only put truly UI-related state in the main isolation domain.
- If a type is frequently passed across domains, first evaluate whether the boundary design is wrong.

### Sendable
- Data passed across tasks or actors MUST be evaluated for `Sendable`.
- When `struct` / `enum` can solve the problem, do NOT force reference types.
- `@unchecked Sendable` is only a last resort with strict internal synchronization guarantees; rationale MUST be documented.

### Task Lifecycle
- Every task must answer: who creates, who holds, who cancels, when does it end.
- Use parent-child task relationships to propagate cancellation.
- Scattered ownerless `Task {}` are NOT allowed.

## Common Design Rules
### ViewModel
- UI-facing ViewModels are marked `@MainActor`.
- Async loading flows need clear rules for "start loading, cancel old task, receive result, discard stale results".
- Do NOT mix multiple concurrency models in a ViewModel causing inconsistent state sources.
- For search, streaming output, pagination, and rapid switching scenarios, first check for "old task results overwriting new state" before considering other concurrency hypotheses.

### Parallel Tasks
- Use `async let` for independent subtasks.
- Use `TaskGroup` for dynamic count or aggregation tasks.
- For network aggregation, image prefetching, batch loading — clearly define cancellation and error propagation strategies.

### Legacy API Bridging
- When using `withCheckedContinuation` / `withCheckedThrowingContinuation`, MUST ensure resume is called exactly once.
- Bridging layer only does protocol adaptation; do NOT inject business logic.
- During migration, prevent both callback and async channels from modifying state simultaneously.

## High-Risk Signals
The following concurrency-specific signals (not covered in anti_patterns.md §2, belonging to concurrency isolation/contention/stale-writeback):
- Modifying UI-related state outside the main isolation domain
- Multiple tasks competing to write the same mutable data
- Writing back to UI after task cancellation

For broader concurrency anti-patterns (scattered `Task {}`, `DispatchQueue.main.async` masking timing, abusing `@unchecked Sendable`), see [anti_patterns.md](anti_patterns.md) §2 "Concurrency Anti-Patterns".

## Review Checklist
- [ ] Are UI updates and UI state publishing clearly protected by `@MainActor`?
- [ ] Does shared mutable state have a clear isolation strategy?
- [ ] Do types passed across domains satisfy `Sendable` semantics?
- [ ] Do tasks have clear creation, ownership, cancellation, and completion boundaries?
- [ ] Are concurrency issues being patched with GCD, delayed callbacks, or ownerless `Task`?
