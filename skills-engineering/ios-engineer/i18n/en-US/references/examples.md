<!-- last-verified: 2026-06 -->
# Output Templates & Standard Answers

> This is an English mirror of the authoritative Chinese `references/examples.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Architecture Design Answer
- Bug Investigation Answer
- Code Review Answer
- Swift Concurrency Answer
- Performance Analysis Answer
- Refactoring & Migration Roadmap Answer
- Strict Output Requirements

## Usage Rules
- When outputting solutions, review conclusions, troubleshooting conclusions, migration roadmaps, or performance analysis, directly apply this file's templates.
- Output structure follows SKILL.md core iron rules (four-section + single main path + minimal fix); this file only provides specific field templates per scenario type, does not redefine triggers or candidate strategies.
- If test strategy, decision records, or migration risk control are simultaneously triggered, first give the four-section summary, then append the corresponding detailed sections.
- This file only defines output skeletons; does not redefine root-cause analysis discipline, tool budgets, or stop-loss rules.
- For template output involving any changes (troubleshooting fix / architecture changes / concurrency migration / performance optimization / refactoring implementation), after the "Verification" section must append an independent "Residual Risk Statement" block with fixed three fields: Covered / Uncovered / Residual Risk (fulfilling GR-008). Three fields must exist as independent paragraphs literally; writing them scattered into "Verification" or merging into one paragraph is not allowed — field existence must be mechanically verifiable.
- For output involving concurrency / availability API / SwiftUI behavior / network cancellation semantics, before the "Conclusion" section must append an independent "Version Prerequisite" block, one of two choices: write the engineering truth (e.g., `iOS 15.0 / Swift 5.9`), or an explicit assumption (e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`). This block must exist as an independent paragraph literally; merging with "Conclusion" or "Why" or scattering into prose is not allowed (fulfilling IR-006). Field existence must be mechanically verifiable.

## 1. Architecture Design Answer
Applicable to: module design, page refactoring, networking layer design, state governance.

Output structure:

```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Conclusion
- Recommend what structure
- How to define boundaries and dependency direction

Why
- What is the current core problem
- Why this is the minimal and evolvable solution

Fix
- Which layer to change first
- Which dependencies or state ownership to adjust

Verification
- How to prove boundaries and behavior have not regressed
- Which risks are not yet covered

Residual Risk Statement
- Covered: paths / scenarios / callers already validated by this change
- Uncovered: paths / scenarios / callers explicitly not verified
- Residual Risk: assumptions / boundaries / dependencies that could still cause problems even if above passed
```

## 2. Bug Investigation Answer
Applicable to: Crash, state confusion, layout anomalies, concurrency issues, intermittent issues.

Output structure:

```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Conclusion
- What is the most likely root cause
- Which layer the error falls at

Why
- What evidence supports this judgment
- Why it triggers at this timing

Fix
- What is the minimal structural fix
- Why it's not a patch-style fix

Verification
- How to reproduce and regress
- How to prove no side effects introduced

Residual Risk Statement
- Covered: paths already reproduced / regression-verified by this fix
- Uncovered: paths / similar scenarios / related callers not verified
- Residual Risk: how failure would manifest if root cause hypothesis is wrong / what unknown factors could still trigger it
```

## 3. Code Review Answer
Applicable scenarios and output structure (findings-first skeleton + hit dimension verification) see [review_checklists.md](review_checklists.md).
This file does not redefine the code review output skeleton; review output format, mergeable judgment, and per-dimension check items are all solely handled by review_checklists.md.

## 4. Swift Concurrency Answer
Applicable to: Actor design, task cancellation, callback migration, Sendable review.

Output structure:

```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Conclusion
- How concurrency boundaries should be defined

Why
- What is the current risk point
- Which isolation or cancellation semantics went wrong

Fix Plan
- How to adjust actor / `@MainActor` / Task hierarchy
- How to bridge old interfaces

Verification
- Compile-time concurrency checks
- Device behavior verification
- Cancellation chain verification

Residual Risk Statement
- Covered: call points / thread boundaries already validated by this concurrency change
- Uncovered: untested exception paths / cancellation timing / concurrency level scenarios
- Residual Risk: potential races in Sendable assumptions / actor reentrance / old interface bridging
```

## 5. Performance Analysis Answer
Applicable to: slow launch, scroll stutter, memory growth, heavy page refresh.

Output structure:

```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Conclusion
- What is the main performance bottleneck
- Which critical path it falls on

Why
- What data and hotspots support this judgment

Fix
- What is the minimal effective optimization action
- Which actions should not be done now

Verification
- Pre-optimization data
- Post-optimization data
- Whether there are side effects

Residual Risk Statement
- Covered: metrics / devices / scenarios already tested by this optimization
- Uncovered: device tiers / data scales / interaction paths not tested
- Residual Risk: under what conditions the optimization assumption would fail / whether it could drag down other paths
```

## 6. Refactoring & Migration Roadmap Answer
Applicable to: large legacy module splitting, UIKit to SwiftUI migration, callback to async/await migration.

Output structure:

```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Conclusion
- Goal and scope of this migration or refactoring

Why
- Why the current structure must be adjusted
- What is the biggest risk point

Fix
- How phases are cut
- How compatibility layer, call migration, and old-code deletion order are arranged

Verification
- What signals to look at per phase
- What are the rollback conditions

Residual Risk Statement
- Covered: planned compatibility layers / existing rollback paths / assessed phases
- Uncovered: sub-modules without risk assessment / unscheduled phases
- Residual Risk: inter-phase coupling failure modes / release window risks / observation blind spots
```

## 7. Strict Output Requirements
- When answering architecture questions, do not just name patterns; must explain boundaries, dependency direction, and state ownership.
- When answering bug questions, do not just give guesses; must provide evidence.
- When answering performance questions, do not just list optimization points; must provide metrics.
- When answering review questions, do not just discuss style; must discuss risks.
- When answering migration questions, do not just describe end state; must describe phases.
- Do not unnecessarily expand historical background, textbook explanations, or large candidate solution sections.
