<!-- last-verified: 2026-05 -->
# iOS Coding Conventions

> This is an English mirror of the authoritative Chinese `references/ios_conventions.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- When involving naming, declaration order, access control, force unwrapping, nesting depth, code structure, concurrency writing consistency, and unified terminology for coding habits, output review comments or code per this file's rules.
- This file only captures coding habit-level constraints; architecture boundaries, state ownership, concurrency isolation, UI layout issues belong to dedicated topic documents.
- When reviewing or producing code, if this file's clauses are violated, must explicitly point out and provide correction direction.
- When outputting solutions, code reviews, troubleshooting conclusions, architecture designs, or migration plans, must use this file's unified terminology.
- This file does not preset iOS / Swift version baselines; specific trade-offs for concurrency writing, availability API, SwiftUI behavior constraints are determined by the actual project's `IPHONEOS_DEPLOYMENT_TARGET` and `SWIFT_VERSION`. Version-sensitive recommendations see SKILL.md core iron rules.

## General Naming Rules
- When narrating in Chinese, Chinese is primary, English secondary.
- When naming Swift types, protocols, enums, file names, module names, retain English naming.
- Apple official frameworks, language keywords, protocol names, property wrapper names retain original English terms.
- Prohibit frequent switching between Chinese and English causing multiple aliases for one concept.
- Within the same round of answers, the same concept can only use one primary name.
- When English terms need to be retained, first occurrence uses "Chinese primary name + original English term" format; subsequent occurrences consistently use the same term.

## Swift Property Declaration & Position
- Use `let` when possible: properties default immutable; do not expose write capability unnecessarily.
- Only use `lazy var` when lazy construction is needed and initialization depends on runtime context (e.g., properties needing `self`); note `lazy var` is not concurrency-safe; cross-task access must explain thread ownership or change to `actor` holding.
- `var` properties must minimize external visibility: prefer `private(set)`; cross-class writable `var` must explain state ownership and write path.
- Shared mutable state must explain isolation strategy (`actor` / `@MainActor` / explicit lock).
- Property positions recommended uniformly at end of class structure (after init / public API / private helpers); avoid interleaving properties of different access levels.

## `self` Prefix
- Variables and method calls default to using `self.` prefix.
- The prefix is not for disambiguation but to make "current scope property vs local variable" immediately clear when reading; avoid later additions of same-named variables causing implicit shadowing.

## Access Control
- Default explicit access control: prefer minimum visibility (e.g., `private`, `private(set)`); avoid unnecessary exposure.
- Cross-module public members must explicitly write `public` or `package`; must not use default `internal` to代替 intentional public declarations.

## Prohibit Crash-Causing APIs
- Prohibit force unwrapping, force casting, and assertion-style crashes (e.g., `!`, `as!`, `fatalError`) unless the immutable premise and failure cost are explicitly stated.
- If crashing is unavoidable, must annotate near the code "what is the premise, what is the failure cost, why the error path cannot be taken".

## Nesting Depth & Early Exit
- Control nesting depth: prefer `guard` for precondition early exit; avoid multi-level `if` / `switch` nesting.
- Single function indentation levels generally not exceeding 3 levels; when exceeded, prefer splitting functions or extracting sub-processes rather than adding more branches.

## Code Structure Order
- Fixed code structure order: `typealias` / `enum` -> init -> public API -> private helpers.
- Protocol implementations grouped in corresponding `extension`; not mixed with main class body.
- `IBOutlet` / `IBAction` if present, grouped separately like protocol extensions.

## Swift Naming
- Variables and methods use camelCase, e.g., `messageCount`, `refreshFeed()`.
- Bool types prefixed with `is` / `has` / `can`, e.g., `isLoading`, `hasUnreadMessages`, `canSubmit`.
- Async / concurrency-related methods use clear verb phrases to express intent, e.g., `refreshFeed()`, `cancelInflightRequests()`; do not use vague verbs like `doXxx`, `handleXxx`.
- Avoid ambiguous abbreviations: `mgr`, `ctrl`, `tmp`, `val` all prohibited in new code; retain existing abbreviations without spreading to new modules.
- Prohibit generalizing temporary business state as `Snapshot` (e.g., naming "current temporary data for some view" as `XxxSnapshot` without business semantics); use business-close naming (e.g., `pinnedFollowUpIdentifier`, `savedDraft`, `pendingOrder`).
- **Exception**: Apple API's own Snapshot types (e.g., `NSDiffableDataSourceSnapshot`, `UIViewControllerContextTransitioning.snapshotView`) retain original names; snapshot testing concepts in test frameworks retain original names.

## Concurrency Writing Consistency
- Write concurrency boundaries clearly: UI update strategy unified (e.g., `@MainActor` or explicit main-thread hop); avoid mixing multiple writing styles in the same module causing unclear boundaries.
- After selecting a writing style, within the same module do not allow mixing `@MainActor` with `DispatchQueue.main.async` / `MainActor.run {}`; when switching is needed, must migrate as a whole; no local patches.
- Related concurrency design rules see [swift_concurrency.md](swift_concurrency.md).

## Architecture & Layering Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Architecture Boundary | Architecture Boundary | When narrating layer responsibilities |
| Dependency Injection | Dependency Injection, DI | First occurrence may write "Dependency Injection (DI)" |
| Route Coordinator | Coordinator | Type name retains `Coordinator`; body may write "Route Coordinator (Coordinator)" |
| Use Case | UseCase | Type name retains `UseCase` |
| Repository | Repository | Type name retains `Repository` |
| Service | Service | Type name retains `Service` |
| Feature Module | Feature | When narrating business modules, use "Feature Module"; code name retains `Feature` |
| Core Module | Core | When narrating base layer, use "Core Module"; code name retains `Core` |

## Modeling Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Transfer Model | DTO | First occurrence may write "Transfer Model (DTO)" |
| Domain Entity | Entity | First occurrence may write "Domain Entity (Entity)" |
| Page State | ViewState | First occurrence may write "Page State (ViewState)" |
| Error Model | ErrorModel | First occurrence may write "Error Model (ErrorModel)" |
| Mapping Layer | Mapper | If independent layer clearly exists, may write "Mapping Layer (Mapper)" |

## Concurrency Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Main Thread Isolation | @MainActor | When narrating rules |
| Actor Isolation | actor | Retain keyword as-is |
| Structured Concurrency | Structured Concurrency | When narrating concurrency model |
| Cancellation Semantics | Cancellation | When narrating task cancellation rules |
| Sendable Semantics | Sendable | First occurrence may write "Sendable Semantics (Sendable)" |

## UI & State Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Page State Machine | State Machine | When narrating complex page state flow |
| Empty State | Empty State | When narrating success-but-no-data scenario |
| Error State | Error State | When narrating failure rendering scenario |
| Loading State | Loading State | When narrating loading process |
| List Identity | Identity | When narrating list stable identification issues |

## Networking & Data Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Request Endpoint | Endpoint | Type name retains `Endpoint` |
| Request Builder | RequestBuilder | Type name retains `RequestBuilder` |
| API Client | APIClient | Type name retains `APIClient` |
| Idempotency | Idempotency | When narrating write operation safety |
| Cursor-based Pagination | Cursor-based Pagination | When narrating cursor-type pagination |
| Page-based Pagination | Page-based Pagination | When narrating page-number pagination |
| Token Refresh | Token Refresh | When narrating Token update chain |

## Engineering Collaboration Terminology
| Unified Term | Original English | Usage Rule |
|------|------|------|
| Code Review | Review | Body uniformly writes "Code Review"; first occurrence may write "Code Review (Review)" |
| Pull Request | PR | Body uniformly writes "PR" |
| Module Owner | Owner / Ownership | Body uniformly writes "Module Ownership" or "ownership"; this skill uniformly writes "module ownership" |
| Rollout | Rollout | When narrating phased release |
| Rollback Condition | Rollback Condition | When narrating release failure exit conditions |

## Prohibited Mixing Rules
- Do not collectively refer to `DTO`, `Entity`, `ViewState`, `ErrorModel` as `Model`.
- Do not mix "Controller", "VC", "ViewController" in the same paragraph.
- Do not mix "Code Review", "Review", "PR Review" in the same paragraph.
- Do not mix "ownership", "owner", "owner attribution" in the same paragraph.
- Do not conflate "page state", "business state", "component state" into just "state".

## Common Anti-Patterns
- Declaring all properties as `var` for convenience; not declaring `private(set)` or `let`.
- Using `!` to suppress compile warnings without analyzing failure premises.
- `guard` swallowed by nested `if`; early exit logic hidden in deeper indentation.
- Protocol implementations scattered in class body; reader cannot immediately see which are protocol contracts.
- Bool names without prefix (`loading`, `error`); reader cannot tell if it's a state flag or a value.
- Same module simultaneously using `@MainActor`, `DispatchQueue.main.async`, `MainActor.run {}`; UI update boundaries out of control.
