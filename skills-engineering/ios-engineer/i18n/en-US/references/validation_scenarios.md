<!-- last-verified: 2026-06 -->
# Skill Validation Scenarios

> This is an English mirror of the authoritative Chinese `references/validation_scenarios.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- Use this file to verify whether the `ios-engineer` skill truly achieves: carry less context, grasp root cause first, avoid large changes, complete chains, control tool calls.
- Each validation tests only 1 scenario; do not mix multiple scenarios in one round.
- Validation conclusions only answer four things: whether it hit, where it deviated, why it deviated, how to fix the rule.
- Recommend using fixed scenario identifiers: `layout`, `parameter-pass-through`, `concurrency`, `review`, `migration`, `mcp-control`, `notifications`, `privacy`, `persistence`, `storekit`, `extensions`.
- Structured definitions are in 11 JSON specs under [evolution/scenarios/](../evolution/scenarios/) (`expected_hits` / `failure_signals` / `output_contract` / `primary_refs`); this file serves as human-readable companion. When adding or adjusting scenarios, **change JSON first, then sync this document**; unified entry point [scripts/validate.sh](../scripts/validate.sh) `--scenarios` asserts slug consistency on both sides, field completeness, and checks internal links.

### JSON & Document Sync Flow
Execute in the following order; skipping steps will be caught by corresponding scripts:

1. Change `evolution/scenarios/<slug>.json`'s `expected_hits[].rule_id` / `failure_signals[].rule_id` / `output_contract` / `primary_refs`.
2. Run [scripts/validate.sh](../scripts/validate.sh) `--scenarios` — asserts 11 JSON files and this document's slugs are bidirectionally consistent, fields complete, and checks internal links. Skipping this lets slug drift surface only at grader stage.
3. Sync this document's corresponding scenario description ("User input example / Pass criteria / Failure signals").
4. Run [scripts/validate.sh](../scripts/validate.sh) `--ids` — asserts JSON's `rule_id` are IDs with `status=active` in [rule_index.md](rule_index.md). Skipping this lets retired/deprecated/non-existent IDs enter scenario specs.

## Validation Targets
- Does output prioritize the most likely root cause rather than expanding multiple large branches.
- Does output maintain short structure rather than being lengthened by templates and background explanations.
- Does fix comply with minimal change principle rather than immediately refactoring modules.
- When adding new fields or parameters, does it complete the full data chain rather than only fixing the consumer side.
- Are tool calls controlled; do they avoid repeated searching, repeated reading, and repeated attempts.

## Scenario 1: Layout Anomaly
User input example:
```text
Message bubble height is intermittently wrong; long text gets truncated. Don't refactor; help me find the root cause.
```

Pass criteria:
- First land on layout, reuse, adaptive height chain.
- Do not immediately suggest rewriting the entire message view.
- Output maintains "root cause / why / fix / verification".

Failure signals:
- Giving many candidate causes upfront.
- Not first checking reuse, constraint chain, async writeback.
- Directly suggesting complete layout solution replacement.

## Scenario 2: Parameter Pass-through Chain
User input example:
```text
Fix this method in class A. New field currentModel, but it can't be obtained in A, and B doesn't have it either.
```

Pass criteria:
- Recognize this is a complete data chain problem.
- Trace back to true source, construction point, mapping layer, and intermediate holders.
- Do not just add variables locally in A or B.

Failure signals:
- Only adding properties at the consumer side.
- Giving default values or passing null to make the current file compile.
- Not explaining the true source of truth.

## Scenario 3: Concurrency State Confusion
User input example:
```text
Search page results get cross-contaminated during rapid input. Help me fix it; no large changes.
```

Pass criteria:
- First land on task cancellation, stale result writeback, state ownership.
- Prefer minimal fix, e.g., cancel old task or discard stale results.
- Explain verification method.
- Output contains independent "Version Prerequisite" block before "Conclusion" section (per examples.md §4 template); writes truth or explicit assumption (IR-006).

Failure signals:
- Generalizing the problem as "switch to a different architecture".
- Only adding `DispatchQueue.main.async` or delays.
- Not mentioning cancellation chain.
- Giving concurrency / availability API / SwiftUI behavior advice without truth or explicit assumption; implicitly using some iOS / Swift version's API.
- Not outputting version prerequisite as an independent block literally; only implied in prose.

## Scenario 4: Code Review
User input example:
```text
Review this change; focus on hidden regressions.
```

Pass criteria:
- First report correctness, races, lifecycle, architecture overstepping, test gaps.
- Findings clearly before style opinions.
- Conclusion is brief; no lengthy teaching.
- Output end contains independent "Residual Risk Statement" block with fixed three fields: Covered / Uncovered / Residual Risk; exists as independent paragraph literally; not merged with "Verification Gaps" (GR-008).

Failure signals:
- Talking about naming, formatting, style first.
- Not sorted by severity.
- Not mentioning verification gaps.
- Residual risk statement missing, three fields incomplete, or merged into "Verification Gaps" section.

## Scenario 5: Complex Migration
User input example:
```text
Planning to migrate this old chat page from callback to async/await. Give me an implementation plan.
```

Pass criteria:
- First give four-section summary.
- Then add phase plan, compatibility layer, rollback conditions as needed.
- Do not present migration as one-shot replacement.

Failure signals:
- No phase breakdown.
- No compatibility layer and rollback.
- Only describing end state; not describing migration path.

## Scenario 6: MCP / Tool Call Control
User input example:
```text
Help me investigate this intermittent production issue. There are many logs; take a look yourself.
```

Pass criteria:
- First compress to phenomenon, known facts, key gaps.
- Tool calls progress around 1 main direction.
- After two times with no new evidence, proactively switch direction or converge.

Failure signals:
- Opening large numbers of files or doing large amounts of searches at once.
- No budget awareness.
- Repeatedly trying the same direction.

## Scenario 7: Push Notifications
User input example:
```text
After push arrives, downloading images in the notification extension occasionally fails, and the page the user navigates to after tapping the notification is wrong. Help me investigate.
```

Pass criteria:
- Recognize Notification Service Extension's memory limit and 30-second timeout.
- Point out Extension can only access shared Keychain items if configured with the same Keychain Access Group, and should not initiate long-running network requests inside Extension.
- Output maintains "root cause / why / fix / verification".

Failure signals:
- Not considering Extension's memory/time/sandbox constraints.
- Skipping push arrival → user tap → route navigation chain analysis.
- Suggesting hardcoding notification route mapping in AppDelegate.

## Scenario 8: Privacy Permissions
User input example:
```text
App requests camera permission on first launch; after user denies, the feature is unavailable and there's no guidance to settings. Also ATT prompt timing is wrong; review was rejected.
```

Pass criteria:
- Point out permissions must be requested within the user's explicit behavioral context; must not batch-prompt at launch.
- Provide degradation path when permission is denied.
- ATT prompt needs pre-permission explanation before the dialog.

Failure signals:
- Not checking Info.plist UsageDescription keys.
- Suggesting retrying system permission dialog in denied state (ineffective operation).
- Not mentioning review rejection risk.

## Scenario 9: Persistence & Migration
User input example:
```text
Core Data migration failed after adding a new field; data was lost. Now want to migrate to SwiftData but don't know if smooth transition is possible.
```

Pass criteria:
- Distinguish lightweight migration and heavyweight migration scenarios.
- Must backup before migration; do not clear data on failure.
- Point out context threading model constraints.

Failure signals:
- Suggesting directly clearing persistent store and rebuilding without backup.
- Suggesting passing NSManagedObject across contexts.
- Suggesting mixing NSFetchedResultsController in SwiftData solution.

## Scenario 10: App Extensions
User input example:
```text
Widget refresh occasionally doesn't update data, and tapping Widget to jump to main App crashes. Share Extension also can't access main App's user token.
```

Pass criteria:
- Recognize Extension and main App data sharing must go through App Group / Keychain Group.
- Point out Widget getTimeline's memory and time budget.
- Point out Extension's independent process sandbox constraints.

Failure signals:
- Suggesting Extension directly access main App sandbox directory or UserDefaults.standard.
- Suggesting heavy requests or complex image processing inside getTimeline.
- Ignoring Extension's independent process and memory-constrained reality.

## Scenario 11: StoreKit / In-App Purchase
User input example:
```text
Subscription purchase occasionally doesn't credit, and restore purchases is also unstable. Currently the client stores expiration time in UserDefaults; falls back to sandbox retry when server verification fails.
```

Pass criteria:
- Point out purchase state must not only depend on `UserDefaults`; must be based on StoreKit transaction or server verification result.
- Point out `Transaction.updates` / `SKPaymentTransactionObserver` needs continuous monitoring throughout App lifecycle.
- Point out production to sandbox fallback should only occur when there's a clear sandbox receipt indication; must not swallow all production verification failures.

Failure signals:
- Suggesting using local cache to directly determine subscription entitlements.
- Calling `AppStore.sync()` / `restoreCompletedTransactions()` on every launch.
- Falling back all server verification failures to sandbox.

## Record Template
```text
Validation Scenario
- Scenario name

Passed?
- Pass / Fail / Partial

Hit Points
- Which rules took effect

Deviation Points
- Which behaviors are still out of control or off-topic

Improvement Suggestions
- Which rule should be added
- Which duplicate rule should be removed
```

Structured record suggested fields:

```text
scenario
- Fixed scenario identifier

result
- pass / partial / fail

hits
- Rules or behaviors that hit

deviations
- Deviation points

improvements
- Improvement suggestions
```

Optional fields (in scenario spec JSON's `expected_hits[]` / `failure_signals[]`):

- `rule_id`: fill with existing active ID from SKILL.md (e.g., `IR-006`); used for cross-scenario hit frequency statistics and missed_rules list reconciliation; ID source see [rule_index.md](rule_index.md); validation guarded by [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh).
