<!-- last-verified: 2026-05 -->
# Migration Strategy & Risk Control

> This is an English mirror of the authoritative Chinese `references/migration_strategy.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Applicable Scenarios
- Usage Rules
- Refactoring Principles
- Giant File Splitting Strategy
- Migration Strategies
- Risk Identification
- Phased Migration
- Compatibility Layer Strategy
- Rollout & Rollback
- Verification Strategy
- Pre-release Checklist
- Review Output Standards
- Common Anti-Patterns

## Applicable Scenarios
For the following tasks:
- Legacy project governance, giant file splitting, architecture cleanup
- Callback hell migration to `async/await`
- GCD to structured concurrency, serial queue to `actor`
- UIKit and SwiftUI mixed migration
- Networking layer, caching layer, authentication layer refactoring
- Pull Request review, technical solution review, refactoring roadmap design

## Usage Rules
- When involving architecture migration, module splitting, concurrency model migration, networking layer refactoring, or UIKit to SwiftUI migration, this file must be used.
- Migration is not a single code replacement but a continuous risk control process.
- Must not proceed with high-risk migration without rollback conditions, compatibility layer strategy, and verification paths.
- Refactoring and migration must simultaneously handle "how to change" and "how to control risk"; must not answer only one side.
- Related playbooks see [execution_playbooks.md](execution_playbooks.md); release and CI gates see [build_release_and_ci.md](build_release_and_ci.md).

## Refactoring Principles
- First stabilize behavior, then adjust structure; prohibit changing requirements without boundaries while refactoring.
- Use verifiable small-step refactoring; prohibit one-shot "big bang".
- Refactoring goals must be clear: reduce coupling, improve testability, eliminate duplication, converge state, clarify boundaries.

## Giant File Splitting Strategy
### ViewController / ViewModel Too Large
- First identify what is rendering, what is business orchestration, what is data access, what is routing.
- Extract list data sources, form validation, network orchestration, route jumping, analytics logic.
- Split through protocol facets and dependency injection, not simply moving code to `Extensions`.

### Service / Manager Out of Control
- If one object is simultaneously responsible for networking, caching, analytics, permissions, state synchronization, responsibilities must be split.
- First extract stable abstractions, then migrate callers, finally delete old implementation.

## Migration Strategies
### Callback to async/await
- Start wrapping an async interface from edge dependencies, then gradually converge the call chain upward.
- When using `withCheckedContinuation` / `withCheckedThrowingContinuation`, must guarantee only one resume.
- During migration, prohibit mixing multiple cancellation semantics causing inconsistent behavior.

### GCD to Structured Concurrency
- Translate "queue" problems into "isolation domain" and "task hierarchy" problems.
- When serial queues protect shared state, evaluate whether it should become an `actor`.
- `DispatchSemaphore`, `group.wait()` and other blocking approaches treated as high-risk.

### UIKit and SwiftUI Mixed Migration
- First decide which is the host and which is the incrementally introduced party.
- Avoid simultaneously migrating UI, state management, navigation, and networking layer; split into multiple phases.
- Extract reusable components into independent modules; prohibit scattered dual-side implementations.

## Risk Identification
- Before starting, must identify impact scope: pages, modules, shared components, analytics, caches, tests, release paths.
- Must identify the most problem-prone chains: launch, login, list, payment, submission, deep-link navigation.
- Must clarify new risks after migration, not just describe old problems.

## Phased Migration
All high-risk migrations must be split into phases:
1. Build abstractions
2. Connect compatibility layer
3. Migrate callers
4. Delete old implementation
5. Closure verification

Requirements:
- Each phase must have independently verifiable deliverables.
- Must not compress "build abstractions, migrate callers, delete old implementation" into a single commit.

## Compatibility Layer Strategy
- Compatibility layer must have clear lifecycle: why it exists, who it serves, when it will be deleted.
- Compatibility layer must limit spread scope; must not become a new long-term dependency.
- When introducing dual-write, dual-read, dual-routing, dual-rendering, must define consistency check methods.

## Rollout & Rollback
- High-risk migrations must explicitly define rollout scope.
- Must define rollback trigger conditions: Crash, key metric anomalies, business failure rate increase, significant performance degradation.
- Rollback paths must be executable; must not just write "rollback if there are issues".
- Feature flags, route flags, configuration flags must have clear responsibilities.

## Verification Strategy
- Each phase must define: verification goals, verification scope, verification method, uncovered risks.
- Must cover new/old path consistency verification.
- Must cover exception paths and degradation paths.
- If migration involves concurrency and state model, must specifically verify cancellation, writeback, isolation, and regression.

## Pre-release Checklist
- Has impact scope and high-risk chains been identified
- Has compatibility layer and deletion conditions been defined
- Are rollout and rollback means available
- Have key tests and observation metrics been added
- Have failure signals and responsible persons been clarified

## Migration Review Additional Check Items
When reviewing migration-related PRs, in addition to the 6 dimensions from [review_checklists.md](review_checklists.md), add the following migration-specific checks:
- Is it split by phases (build abstractions / connect compatibility layer / migrate callers / delete old implementation / closure verification) rather than single large change?
- Is there a compatibility layer with defined lifecycle (when to delete, preconditions for deletion)?
- Is rollout scope and rollback trigger conditions clearly defined (Crash / metric anomalies / business failure rate)?
- Has new/old path behavioral consistency been verified?
- If involving concurrency or state model migration, has cancellation, writeback, and isolation been specifically verified?

Review output format: comply with [review_checklists.md](review_checklists.md) §8 findings-first standard output skeleton; migration-related additional check items fall into corresponding sections of that skeleton by severity.

## Common Anti-Patterns
- Equating refactoring with "splitting files" rather than "rebuilding boundaries".
- Large-scale concurrency model migration without regression verification.
- Wrapping old problems in new framework; just moving complexity to a different location.
- Code review only raising style opinions, not correctness, risk, or verification.
- One-shot large migration without phasing.
- Cutting to main path directly without compatibility layer.
- Introducing compatibility layer and never deleting it indefinitely.
- No rollout; can only go live all at once.
- Proceeding with refactoring without rollback path.
- Not defining metrics and failure signals before release.

## Verification Checklist
- [ ] Are refactoring scope, goals, and invariant behaviors defined?
- [ ] Is it progressing in phases with regression verification means retained?
- [ ] Are abstractions built first, then implementation and callers migrated?
- [ ] Are impact scope, high-risk chains, and compatibility layer lifecycle identified?
- [ ] Are rollout and executable rollback paths available?
- [ ] After concurrency migration, are cancellation, thread isolation, and state consistency verified?
- [ ] Do review comments cover correctness, architecture, performance, and testing?
