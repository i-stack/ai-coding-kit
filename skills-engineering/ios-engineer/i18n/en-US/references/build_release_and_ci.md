<!-- last-verified: 2026-06 -->
# Build, Release & CI Governance

> This is an English mirror of the authoritative Chinese `references/build_release_and_ci.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Build Configuration Baseline
- Dependency Governance
- CI Gates
- Release & Rollout
- Failure Signals & Rollback
- Common Anti-Patterns

## Usage Rules
- When involving build failures, Scheme/Configuration confusion, SPM dependency issues, signing configuration, CI pipelines, release gates, rollout, or rollback, this file must be used.
- Do not treat "works locally" as a deliverable standard; must also answer "can CI build stably, can release be controllably rolled back, can risks be observed".
- Do not proceed with release or high-risk changes without gate conditions, failure signals, and rollback paths.

## Build Configuration Baseline
### Scheme & Build Configuration
- Clearly distinguish `Debug`, `Release`, and `Staging` when necessary; do not let configuration semantics drift.
- Scheme only carries startup and debug entry points; does not carry business-differentiation logic.
- Environment differences carried through configuration injection, build settings, or runtime configuration; not through scattered `#if` concatenation.

### Target & Module Boundaries
- Shared logic preferably extracted to SPM modules or stable Targets; do not copy-paste across multiple Targets.
- Target dependency direction must be unidirectional; avoid App Target reverse-referencing implementation details.
- Third-party dependency introduction location must be fixed; avoid the same dependency existing in multiple package management systems simultaneously.
- When public API or module boundaries change, CI must at minimum cover compilation of affected Targets; if boundaries carry core business flows, also cover corresponding core tests or integration tests.

### Build Problem Diagnostic Order
Identify failure layer by error signature:

| Layer | Typical Error Signal | Identification Characteristics |
| --- | --- | --- |
| Dependency Resolution | `Package.resolved missing` / `version constraint unsolvable` / `pod install` reports Podfile.lock conflict | Error occurs before build starts; message contains `version` / `resolved` / `dependency` |
| Compilation | `error: cannot find 'Foo' in scope` / `undeclared type` / Swift type mismatch | Error points to specific source file and line; message contains `cannot find` / `undeclared` / `type mismatch` |
| Linking | `Undefined symbol: _OBJC_CLASS_$_Foo` / `ld: framework not found` | Error occurs after compilation passes; message contains `Undefined symbol` / `ld:` / `framework not found` |
| Signing | `Code signing error` / `provisioning profile` / `entitlements` issues | Error text contains `signing` / `provisioning` / `entitlement` / `team ID` |
| Archiving | Resource files missing / Info.plist validation failure / archive failure | Error occurs in post-linking archive stage; message contains `archive` / `Info.plist` / `resource` |
| Testing | XCTest assertion failure / test target configuration error | Error occurs during test target execution; message contains `XCTAssert` / `test failure` |

Diagnostic flow: match error signals top-to-bottom; once a layer is hit, resolve that layer's issue before continuing build; do not jump to downstream processing. Cache clearing or regenerating project files only used after all above layers are ruled out.

### Simulator vs. Device Build Strategy
- First clarify whether the failure is related to simulator SDK, architecture, system capabilities, or third-party binary dependencies.
- If simulator cannot complete compilation verification, must switch to device build to continue verification, rather than directly declaring it cannot compile.
- After switching to device build, must record the simulator failure reason and device verification scope; avoid misidentifying platform differences as "code is fully correct".
- If the issue only appears on device or only on simulator, must treat it as a platform difference issue for separate analysis; do not conflate with general build failure.

## Dependency Governance
### SPM
- Lock dependency version strategy; avoid unconstrained drift.
- Shared packages must clearly define minimum platform version and public API boundaries.
- Packages must not leak App-layer dependencies; avoid forming reverse coupling.

### Hybrid Dependency Management
- Do not let multiple package management systems coexist long-term in the same project without a migration plan.
- If temporary coexistence is necessary, clearly define which is the primary source, which is the transition layer, and when the old approach will be removed.
- If build failures come from binary dependencies or script phases, must record reproducible conditions and environment differences.

## CI Gates
### Minimum Gates
- Must include at least: compilation, core tests, static analysis, or equivalent quality gates.
- Pre-merge gates and pre-release gates defined separately; must not be conflated into one standard.
- Add specialized gates for high-risk modules, e.g., concurrency tests, snapshot tests, performance regression checks.
- When modifying public API, module boundaries, dependency resolution, build configuration, or release scripts, cannot just write "passes locally"; must explain whether corresponding CI gates are covered; uncovered items must enter residual risk.
- Snapshot tests, integration tests, and performance regression checks triggered by risk, not as fixed cost for all commits; trigger conditions must be explainable from UI-visible changes, cross-module chains, or performance metric changes.

### Pipeline Design
- Pipeline steps remain traceable: dependency resolution, build, test, artifacts, distribution each output results separately.
- Failure logs must be traceable to module, Target, test case, or script phase.
- When caching is needed, cache strategy must be invalidatable and rollbackable; do not turn cache into a new instability source.

### Environment Consistency
- Pin Xcode version, SDK, key tool versions, and certificate sources.
- Build configuration differences between local, CI, and release machines must be visible.
- Issues appearing in CI but not locally: prioritize investigating environment, signing, resources, and script I/O declarations.

## Release & Rollout
### Pre-release Mandatory Questions
- Which pages, modules, analytics, caches, and critical paths does the release affect?
- Are there feature flags, route flags, or configuration flags for rollout?
- Which metrics to monitor post-release to determine success or failure?

### Rollout Strategy
- High-risk changes gradually increase volume by population, channel, version, or flag.
- When old and new paths coexist, define consistency check methods.
- During rollout, retain rapid shutdown or rollback capability; do not depend on re-releasing as the only rollback path.

## Failure Signals & Rollback
- Failure signals at minimum include: Crash metrics, key business success rate, API error rate, stutter or launch degradation, core analytics anomalies.
- Rollback conditions must be quantified; do not write "if there are issues, keep watching".
- Rollback paths must be executable: responsibilities and order for closing flags, switching back to old paths, withdrawing configurations, reverting versions must all be clear.

## Common Anti-Patterns
- Hardcoding environment differences in code instead of managing through configuration or build settings.
- Same dependency managed simultaneously by SPM, Pods, or manual integration.
- Only validating Happy Path before release; not validating upgrade, rollback, degradation, and exception paths.
- Directly clearing cache and retrying after CI failure without first confirming failure layer and root cause.
- Pushing high-risk changes live without rollout and rollback conditions.
