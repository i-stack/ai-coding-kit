<!-- last-verified: 2026-06 -->
# iOS Review Checklist

> This is an English mirror of the authoritative Chinese `references/review_checklists.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- When doing code review, solution review, or refactoring review, first identify which dimensions the current changes **hit** (correctness / architecture / concurrency / performance / UI / testing), then check hit dimensions against the checklist. Unhit dimensions explicitly marked "not involved" or "no evidence" in review conclusions; do not force checking to generate empty content.
- Review conclusions cover all **hit** dimensions; unhit dimensions only annotated. "Hit" criteria: the dimension has real code changes or solution involvement; unchanged files are not considered hit.
- When serious issues found, must explicitly mark "not mergeable".

## 1. Correctness Check
- [ ] Are there force unwrapping, out-of-bounds, illegal state transitions, or null data assumptions?
- [ ] Are there incorrect lifecycle dependencies?
- [ ] Are there async writeback of stale data issues?
- [ ] Are there list reuse causing state residue?
- [ ] Are there missing error handling or error swallowing?
- [ ] Have new fields / parameters / state been chain-checked per [architecture_and_network.md](architecture_and_network.md) "Parameter Pass-through & Data Source"?
- [ ] Has the current fix listed checked impact scope, unverified paths, and residual risk? (not requiring assertion of "none"; requiring explicit annotation)

## 2. Architecture Check
- [ ] Is View / ViewController overstepping to carry business logic?
- [ ] Are ViewModel / UseCase / Repository / Service responsibilities clear?
- [ ] Are dependencies protocol-oriented rather than concrete implementations?
- [ ] Are module boundaries clear? Is there cross-module smuggling?
- [ ] Is routing placed in Coordinator / Router rather than hardcoded inside pages?
- [ ] If new values depend on upstream pass-through, has it been traced back to the true owner / construction point / mapping layer? (see [architecture_and_network.md](architecture_and_network.md) "Parameter Pass-through & Data Source")

## 3. Concurrency Check
- [ ] Are all UI updates constrained by `@MainActor`?
- [ ] Are there shared mutable state not isolated?
- [ ] Are there unowned `Task {}`?
- [ ] Are there task cancellation misses, post-cancellation writeback, or race overrides?
- [ ] Are `Sendable`, `actor`, and old interface bridging usage truly safe?

## 4. Performance Check
- [ ] Are heavy computation, decoding, sorting, IO placed on main thread?
- [ ] Are there SwiftUI over-refreshing or UIKit hierarchy too deep?
- [ ] Are there obvious hotspots in list scroll path?
- [ ] Are unnecessary caches, duplicate computation, or duplicate requests introduced?
- [ ] Are performance verification data provided?

## 5. UI / UX / Accessibility Check
- [ ] Is it compatible with long text, multiple languages, extreme font sizes, and Dark Mode?
- [ ] Does layout rely on hardcoded dimensions or magic spacing?
- [ ] Is list identity stability and interaction state consistency ensured?
- [ ] Are basic accessibility semantics present?
- [ ] Is platform interaction consistency broken?

## 6. Testing & Verification Check
- [ ] Are key business logic unit tests added?
- [ ] Are integration verification paths defined?
- [ ] Do bug fixes have reproduction paths and fix proof?
- [ ] Do bug fixes provide at least one reproducible verification path and explicitly list uncovered paths and corresponding residual risks?
- [ ] Do performance optimizations have before/after comparison?
- [ ] Do refactoring migrations have phased regression verification?

## 7. Review Conclusion Levels
### Not Mergeable
Judged when any of the following conditions are met:
- Would cause Crash, data corruption, severe race, severe leak
- Obvious architecture overstepping that is hard to contain later
- Fix has no root-cause evidence; is patch-style
- Fix PR does not list checked impact scope / unverified paths / residual risk, and there are actually known affected modules not handled (lacking delivery evidence, not asserting no risk)

### Mergeable After Changes
Applicable when:
- Structure is acceptable but local implementation defects exist
- Testing, verification, boundary handling are incomplete

### Mergeable
Applicable when:
- All hit dimensions pass check; unhit dimensions annotated as not involved / no evidence
- No not-mergeable issues
- Verification covers current change scope
- Remaining issues are only low-risk optimization items

> Common anti-pattern reference see [anti_patterns.md](anti_patterns.md); cross-module collaboration / PR splitting / ownership review rules see [team_collaboration.md](team_collaboration.md).

## 8. Standard Output Skeleton
```text
Version Prerequisite
- iOS / Swift version (engineering truth, e.g., `iOS 15.0 / Swift 5.9`; or explicit assumption, e.g., `Assuming iOS ≥ 15 / Swift ≥ 5.9; correct if not`)

Review Conclusion
- Not Mergeable / Mergeable After Changes / Mergeable

Critical Issues
1. ...

General Issues
1. ...

Verification Gaps
- ...

Final Requirements
- What must be completed before merge

Residual Risk Statement
- Covered: which dimensions / change paths were reviewed
- Uncovered: paths not reviewed / dimensions lacking evidence (reconcile against §1-§6 hit dimensions)
- Residual Risk: regressions that could still occur after merge / dependencies on other team confirmations
```

> Residual Risk Statement is the landing point for GR-008 in the findings-first skeleton: three fields must exist as independent sub-sections literally; must not be merged with "Verification Gaps" or omitted. Field existence will be mechanically verified in regression scenarios.
> Version Prerequisite is the landing point for IR-006 in the findings-first skeleton: when review involves concurrency / availability API / SwiftUI behavior / network cancellation semantics, must exist as an independent paragraph literally; must not be merged with "Review Conclusion"; when review completely does not involve the above dimensions, it may be omitted, but "Verification Gaps" must explicitly state "version-related dimensions not involved".
