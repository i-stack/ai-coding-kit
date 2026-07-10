<!-- last-verified: 2026-06 -->
# Decision Records

> This is an English mirror of the authoritative Chinese `references/decision_records.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- When involving architecture selection, module splitting, concurrency model adjustment, state model rebuild, networking layer refactoring, or data flow restructuring, MUST output a decision record.
- Decision records default to a four-section summary first, then full adjudication document as needed.
- This file is only for solution adjudication and migration implementation; do NOT redefine generic answer patterns, troubleshooting discipline, or tool budgets.
- Without candidate comparison, without risk assessment, without rollback conditions — not considered a valid decision record.

> Cross-person decision sync, ownership, and PR splitting rules see [team_collaboration.md](team_collaboration.md).

## Scenarios Requiring Records
- Choosing `MVVM + Coordinator`, `Clean Architecture`, `TCA`, `VIPER`, etc.
- Splitting SPM modules or adjusting module dependency directions
- Introducing `actor`, `@MainActor`, `TaskGroup` and other concurrency boundary strategies
- Introducing Repository, caching layer, offline strategy, retry strategy
- Major page refactoring, list state governance, navigation system rebuild

## Standard Output Template
```text
Decision Title
- One-line description of the core problem to solve

Background
- Current system state
- Existing problems
- Reason for this adjustment

Decision Objective
- What this MUST solve
- What this explicitly does NOT solve

Candidate Solutions
1. Solution A
   - Approach
   - Pros
   - Cons
   - Risks
2. Solution B
   - Approach
   - Pros
   - Cons
   - Risks

Final Decision
- Which solution is chosen
- Why other solutions are not chosen

Scope & Impact
- Which modules are affected
- Which call chains are affected
- Whether tests, caching, analytics, concurrency model are affected

Implementation Steps
1. Step one
2. Step two
3. Step three

Risk Control
- Biggest risk point
- How to roll out gradually or in phases
- What are the rollback conditions

Verification
- How to prove the decision is valid
- What tests and observation metrics are needed
```

Usage constraints:
- If the current task is only giving directional advice, first output a brief conclusion, reason, fix, and verification; then supplement this template as needed.
- Only expand the full decision record when the solution truly changes boundaries, concurrency model, state ownership, or migration path.

## Decision Quality Standards
- MUST first define the problem, then compare solutions, then make the ruling.
- Empty conclusions like "adopting a certain pattern is clearer" are NOT allowed.
- MUST clearly distinguish long-term benefits from short-term costs.
- MUST clearly state technical benefits and business costs.

## Common Mistakes
- Writing "personal preference" as "architecture conclusion"
- Only giving the end state without migration path
- Only listing pros without costs
- Only describing design without verification
- Only stating current feasibility without future maintainability

## Simplification Rules
> This section is a **structured decision** version of the "scenarios requiring records" above: the above lists by business scenario (e.g., choosing MVVM+Coordinator / introducing actor), this section decides by structural change (touching public API / introducing new isolation domain / moving source of truth / cross-PR dependency); hitting any one triggers the full decision record; no requirement to hit both sets simultaneously.

- If the solution adds, removes, or moves public APIs (`public` / `package` modifiers), or changes existing public API behavioral semantics (return type, exception set, side effects).
- If the solution introduces new concurrency isolation domains (`actor` / `@MainActor` / serial queues), or changes existing isolation strategies (e.g., from class + lock to actor).
- If the solution moves or merges the real holder (source of truth) of ViewState / Entity / shared state, or changes state holding from class A to class B.
- If the solution requires other teams' code to be modified simultaneously (cross-PR dependency), or ≥ 2 Feature packages are modified within the same release.
