<!-- last-verified: 2026-06 -->
# Testing Strategy

> This is an English mirror of the authoritative Chinese `references/testing_strategy.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Test Strategy Output Template
- Test Tier Requirements
- Scenario Requirements
- Common Mistakes
- Final Delivery Requirements

## Usage Rules
- When submitting implementation solutions, refactoring solutions, or fix solutions, must simultaneously provide test strategy.
- Test strategy must clearly state "what to test, how to test, coverage extent, and remaining risks".
- Implementations without verification paths are not considered deliverable solutions.
- Default to short template only; only expand to full template when hitting high-risk migration, complex concurrency, performance specialization, release risk, or user explicitly requests expansion.
- This file handles **test planning** (tier classification / coverage strategy / stub design). **Test execution and failure repair** (running tests / analyzing failures / platform verification troubleshooting) belongs to [test_execution_and_repair.md](test_execution_and_repair.md).
- This file only defines verification scope and verification methods; does not redefine root-cause analysis, tool budgets, or general answer skeletons.

## Short Template Mode
Default to short template first; expand to full template when necessary.
Short template only constrains the test strategy itself; if it accompanies implementation solution, fix solution, or refactoring delivery, must still append independent "Residual Risk Statement" block at delivery end, with three fields using GR-008 "Covered / Uncovered / Residual Risk" literally; must not use this section's "Uncovered Risks" as substitute.

```text
Test Coverage
- Which paths are covered

Verification Method
- How to verify

Uncovered Risks
- What risks remain
```

## Test Strategy Output Template
```text
Test Goals
- What to verify this time

Test Scope
- Which modules are covered
- Which modules are not covered

Test Tiers
- Unit tests
- Integration tests
- UI / interaction verification
- Concurrency verification
- Performance verification

Key Cases
1. Happy path
2. Boundary path
3. Error path
4. Regression path

Verification Method
- Automated tests
- Device manual testing
- Logs / breakpoints / Instruments

Residual Risks
- What is not currently covered
- Why these risks are temporarily accepted
```

Usage constraints:
- Only expand full template when tasks span modules, phases, platforms, or verification paths are significantly complex.
- If it is a routine fix or local implementation, short template is sufficient; do not mechanically expand the full checklist.

## Test Tier Requirements
### Unit Tests
Applicable to:
- ViewModel
- UseCase
- Repository
- State transitions
- Error mapping
- Data format transformation

Requirements:
- Cover happy path, boundary path, error path.
- Use replaceable dependencies for time, network, cache, feature flags.

### Integration Tests
Applicable to:
- Inter-module collaboration
- Networking layer and decoding chain
- Cache read/write
- Navigation and state synchronization

Requirements:
- Verify critical call chain closed-loop.
- Verify dependency injection, error propagation, and fallback behavior.

### UI / Interaction Verification
Applicable to:
- Lists, forms, navigation, dialogs, empty state, loading state
- Dark Mode, Dynamic Type, orientation, accessibility
- Components with high visual stability requirements, design system components, complex state combinations

Requirements:
- Verify visual state, interaction state, and writeback state consistency.
- Verify reuse scenarios and identity stability.
- UI visible state changes prefer automatable verification paths; snapshot testing suits stable components and visual regression; do not use as substitute for interaction chain verification.

### Concurrency Verification
Applicable to:
- `actor` isolation
- Task cancellation
- Multi-request contention
- Stale result writeback
- callback to async/await migration

Requirements:
- Must verify no writeback after cancellation.
- Must verify state does not cross-contaminate under concurrency.
- Must verify main thread update boundaries.

### Performance Verification
Applicable to:
- Launch optimization
- List scroll optimization
- Memory governance
- Page refresh optimization

Requirements:
- Must have before/after comparison.
- Must provide metric source.
- Must explain whether correctness and experience are affected.

## Scenario Requirements
### Bug Fix
- Must provide reproduction path.
- Must explain how it failed before fix and how it passes after fix.
- Must cover similar regression paths.

### Architecture Refactoring
- Must verify new/old behavior consistency.
- Must verify migration phase compatibility.
- Must clarify which tests are done in phase 1 and which in phase 2.
- When module splitting, public API, or cross-module communication changes, must cover at least one cross-boundary integration case and explain uncovered callers.

### Concurrency Fix
- Must verify task cancellation, race override, thread isolation.
- Must explain whether device stress testing or Instruments is needed.

### Performance Optimization
- Must provide baseline, target, and result.
- Must not just write "performance improved".

## Common Mistakes
- Only writing "tested" without explaining how.
- Only testing happy path; not testing boundary and error paths.
- Only running simulator; not verifying key device scenarios.
- Only saying tests will be added; not providing specific approach.
- Performance optimization without quantified metrics.

## Final Delivery Requirements
- Every delivery must include test scope.
- Every delivery must provide at least one reproducible verification path.

> "Covered / Uncovered / Residual Risk" declarations are uniformly required by SKILL.md core iron rules; this file does not repeat.
