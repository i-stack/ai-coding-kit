<!-- last-verified: 2026-07 -->
# Skill Self-Evolution Governance

> This is an English mirror of the authoritative Chinese `references/self_evolution.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Trigger Signals
- Self-Evolution Closed Loop
- Candidate Constraints
- Automated Validation Gate
- Promotion & Rollback
- Rule ID Governance
- Real-Task Observation
- Explicitly Forbidden Patterns
- Proposal Template

## Usage Rules
- Only use this file when real tasks reveal rule gaps, rule conflicts, rule duplication, rule invalidation, or output distortion in the current skill.
- This file defines the controlled self-evolution process for the skill; it is not a business problem answering template.
- Default: generate candidate changes and validate; do not directly treat unverified rule changes as the new active version.
- Any new or modified rule must state whether it is adding capability, correcting expression, merging duplicates, or retiring an old rule; if the replacement relationship cannot be explained, default to not adding.
- Version state is stored in `evolution/active_version.json`; proposals, validation records, approval records, and historical snapshots are stored in `evolution/proposals/`, `evolution/validations/`, `evolution/approvals/`, and `evolution/history/` respectively.

## Trigger Signals
Any of the following signals is sufficient to enter the self-evolution process:
- Similar problems appear repeatedly without coverage by existing rules.
- Existing rules can cover, but unclear expression causes persistent execution drift.
- Multiple documents define the same thing redundantly, causing context bloat or priority conflicts.
- A rule has been consistently and stably hit for a long time but still appears in multiple documents redundantly.
- A rule consistently causes misleading, over-expanding, or incorrectly constraining behavior in real tasks.
- A ref file's `<!-- last-verified -->` header exceeds 12 months (detectable via [scripts/audit_ref_freshness.sh](../scripts/audit_ref_freshness.sh)), and the ref involves iOS / Swift / SwiftUI / Xcode content subject to system iteration changes.

## Self-Evolution Closed Loop
Advance in the following fixed order:

1. Record Signal
- What the problem phenomenon is.
- Which existing rule did not hit, or hit but in the wrong direction.
- Whether this is a capability gap, expression gap, or redundant definition.

2. First Determine Change Type
- **Add Capability**: The current skill genuinely lacks a certain type of stable rule.
- **Correct Expression**: The rule direction is correct but phrasing or trigger conditions are unclear.
- **Merge Duplicates**: Multiple documents redundantly define the same constraint.
- **Retire Rule**: An old rule is obsolete, misleading, or superseded by a new rule.

3. Only Generate Candidate Version
- First create a candidate change; do not claim "the skill has automatically learned."
- First use [scripts/create_skill_proposal.sh](../scripts/create_skill_proposal.sh) to generate a proposal skeleton, then fill in the proposal content.
- Candidate changes must simultaneously specify:
  - What to change
  - Why to change it
  - Which old rule is being replaced or merged
  - What type of distortion is expected to be resolved

4. Run Validation
- At minimum, execute structural validation, reference validation, and scenario validation.
- If candidate changes affect output structure, debugging discipline, or migration gates, must additionally run relevant validation scenarios.
- The unified external entry point is [scripts/validate.sh](../scripts/validate.sh): `--all` for the full gate, `--quick` for fast structural checks, `--scenarios` for scenario specs and internal link validation; `validate_skill_evolution.sh` / `validate_scenario_specs.sh` / `validate_rule_ids.sh` / `validate_usage_ledger.sh` are retained as internal sub-checks or specialized debugging entry points.
- Use [scripts/validate_skill_proposal.sh](../scripts/validate_skill_proposal.sh) to write validation records for the proposal and advance the proposal status to `validated` or `rejected`.
- If concrete scenarios have been replayed, use [scripts/record_validation_scenario.sh](../scripts/record_validation_scenario.sh) to append `pass / partial / fail`, hit points, deviation points, and improvement suggestions to the same validation record; when all scenarios are complete and results meet conditions, the proposal can auto-enter `ready_to_promote`. Scenario specs are deposited in [evolution/scenarios/](../evolution/scenarios/); the `scenario` field written must fall within fixed slugs, otherwise subsequent graders cannot reconcile.
- If the proposal has entered `ready_to_promote`, use [scripts/check_skill_promotion_readiness.sh](../scripts/check_skill_promotion_readiness.sh) to view prompts, then use [scripts/approve_skill_promotion.sh](../scripts/approve_skill_promotion.sh) to record authorization and advance the proposal to `approved`.

5. Promote Only After Passing
- Only when the candidate version passes validation is it used as the new active version.
- When validation fails, only continue correcting the candidate version; direct overwrite of the active version is forbidden.
- `ready_to_promote` can be auto-determined but does not auto-promote.
- `approved` must be produced through explicit authorization; it does not advance automatically.
- When promoting, use [scripts/promote_skill_evolution.sh](../scripts/promote_skill_evolution.sh) to archive the current stable snapshot, update the active version, and advance the proposal status to `promoted`; this script requires the proposal status to already be `approved`.
- To quickly demonstrate the full chain, use [scripts/demo_skill_evolution_flow.sh](../scripts/demo_skill_evolution_flow.sh); the script auto-rolls back to `v1` at the end by default.

## Candidate Constraints
- Each proposal should prioritize minimal changes; do not simultaneously rewrite the main skill and a large number of references.
- Each proposal should ideally handle one core problem; if multiple problems are found simultaneously, split into multiple candidate changes first.
- If adding a new rule, must simultaneously answer: which old rule it replaces, or why old rules cannot be reused.
- Proposals involving cross-file shared concepts (chains / layers / output formats / routing tables / terminology entries — concepts referenced across multiple files): before generating the candidate, must first grep the concept across SKILL.md + references/ in full, list all occurrence locations, and cover all locations in the proposal's "Change Content" (or explicitly mark as scope of a future proposal); do not modify a single location and claim the fix is complete.
- When proposals use cross-file references ("see file X section Y"), they must first open file X's section to confirm it actually contains the referenced content; do not reference "content that a future proposal intends to bear but currently lacks."
- If two consecutive proposals only add rules without merging, tightening, or retiring old rules, the third must first undergo a slimming check.

## Automated Validation Gate
Candidate versions must pass at least the following checks:
- `SKILL.md` frontmatter is valid.
- `agents/openai.yaml` structure is valid.
- All `references/` files referenced in `SKILL.md` exist.
- The main skill still maintains layering; root cause discipline, output templates, and tool budgets are not re-mixed.
- Hit validation scenarios show no regressions.

Recommended execution:
- Run [scripts/validate.sh](../scripts/validate.sh) `--all` for the full gate; for local quick checks use `--quick`; for scenario specs only use `--scenarios`.
- Run [scripts/update_skill_proposal_status.sh](../scripts/update_skill_proposal_status.sh) to maintain proposal status; allowed statuses are only `draft`, `validated`, `ready_to_promote`, `approved`, `promoted`, `rejected`.
- Per [validation_scenarios.md](validation_scenarios.md), select affected scenarios for forward validation.
- Run [scripts/record_validation_scenario.sh](../scripts/record_validation_scenario.sh) to append structured scenario validation conclusions.
- Run [scripts/check_skill_promotion_readiness.sh](../scripts/check_skill_promotion_readiness.sh) to check whether authorization preconditions and recommended prompts are met.
- Run [scripts/approve_skill_promotion.sh](../scripts/approve_skill_promotion.sh) to record explicit authorization.
- When rollback is needed, use [scripts/rollback_skill_evolution.sh](../scripts/rollback_skill_evolution.sh) to restore an archived version.

## Promotion & Rollback
- Promotion principle: Only candidate versions that have passed validation, are in `ready_to_promote`, and have recorded explicit authorization can become the new active version upon receiving an explicit command.
- Rollback principle: If new rules cause longer output, decreased hit rate, runaway tool calls, or conflict with existing Iron Rules, roll back to the previous stable version.
- If the current task is merely exploring whether rules need adjustment, candidate changes can be retained without forcing immediate promotion.

## Rule ID Governance
- All structured rules in SKILL.md carry an `[ID]` prefix (Iron Rules IR-NNN / Symptom Navigation SYM-NNN / Task Routing ROUTE-NNN / Output Templates OUT-NNN); the ID canonical index is deposited in [rule_index.md](rule_index.md).
- New IDs: **modify [rule_index.md](rule_index.md) first, then sync SKILL.md**; both sides are asserted to be bidirectionally consistent by [scripts/validate_rule_ids.sh](../scripts/validate_rule_ids.sh).
- IDs are never reused once published: upon retirement, change the status in [rule_index.md](rule_index.md) to `retired` or `deprecated` and fill in the replacement ID (use `retired-no-replacement` if none), and simultaneously **remove the inline reference from SKILL.md** — the validator will reject retired IDs still appearing in SKILL.md.
- Numbering may have gaps; no continuity is enforced. New entries prefer `max(existing number) + 1` within the prefix.
- IDs carry no semantic suffix; semantics are communicated via [rule_index.md](rule_index.md)'s "Summary" column to avoid meaning drift during rename/split.
- The `expected_hits[].rule_id` / `failure_signals[].rule_id` fields in [evolution/scenarios/*.json](../evolution/scenarios/) may be filled with existing active IDs from SKILL.md for cross-scenario hit frequency statistics; filling retired/deprecated IDs or non-existent IDs will cause the validator to fail.

## Real-Task Observation
- Real-task hit data is deposited in [evolution/usage/usage.jsonl](../evolution/usage/usage.jsonl); schema, write protocol, three-end audit block format, and Codex / Claude Code / Cursor system-prompt fragments are unified and deposited in [usage_ledger.md](usage_ledger.md).
- Two write paths: single-entry via [scripts/append_usage_entry.sh](../scripts/append_usage_entry.sh); batch ingestion from audit blocks via [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh). Both paths atomically reject invalid entries without polluting the ledger.
- Ledger validity is guarded by [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh), integrated into the unified validation step `[8/14]`: rule_ids must be in the [rule_index.md](rule_index.md) active set, `task_type` must be within the fixed scenario slug set + `other`, `missed_rules == expected_rules - hit_rules`.
- The ledger is the data source for subsequent summarization / proposal clustering (Step 4). Three-end audit blocks are self-assessed by the LLM and carry self-grading bias — data should be viewed as **biased drafts**; truly trustworthy hit rates still rely on [validation_scenarios.md](validation_scenarios.md) + [evolution/scenarios/*.json](../evolution/scenarios/) regression scenario set independent replay confirmation.
- Do not record only failure cases: stable successful tasks must also be appended, otherwise sampling bias will distort hit rate statistics.
- Periodically run [scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) to view summary reports and proposal candidate signals; the script is read-only for the repo, outputs markdown to stdout by default, supports `--json` for machine-readable output and `--since` / `--tool` for narrowing the dataset.

## Explicitly Forbidden Patterns
- Adding a permanent rule due to a single occasional mistake.
- Adding a rule without stating the replacement relationship.
- Using new rules to mask the problem of unclear expression in existing rules.
- Announcing the skill has "learned" without running validation.
- Continuously expanding rules without slimming, merging, or retiring.
- Submitting a candidate version after modifying only one location for a cross-file shared concept without grepping other reference locations.
- Submitting a candidate version with cross-file references that haven't been verified against the actual target file content (dead reference).

## Proposal Template
When self-evolution is needed, organize changes per the following template as a priority:

```text
Problem Signal
- What deviation appeared in real tasks

Change Type
- Add capability / Correct expression / Merge duplicates / Retire rule

Change Content
- Which files are modified
- Which old rule is being replaced or merged

Expected Benefits
- What distortion will be reduced
- What context waste will be reduced

Validation
- Which structural checks were run
- Which validation scenarios were replayed
- What residual risks remain
```

## Ref Freshness Audit

Each `references/*.md` file carries an HTML comment header `<!-- last-verified: YYYY-MM -->` recording the year-month of the most recent content review. This field is file-level metadata orthogonal to IR / SYM / ROUTE / OUT rules.

Field update protocol:
- After modifying ref content (excluding formatting / link fixes), last-verified must be updated to the current year-month.
- If content is unchanged but a manual line-by-line review confirmed iOS / Swift API status is still correct, it may also be proactively updated.
- Bulk timestamp pushes without genuine review are forbidden.

Audit cycle:
- Recommended: run [scripts/audit_ref_freshness.sh](../scripts/audit_ref_freshness.sh) quarterly.
- Default thresholds: `STALE_MONTHS=12` (mark STALE) / `CRITICAL_MONTHS=18` (mark CRITICAL).
- The script exits nonzero if any of CRITICAL / UNDATED / INVALID is nonzero, suitable for CI or scheduled checks.
- Thresholds can be overridden via environment variables.
- STALE / CRITICAL refs should be prioritized for entry into the "Trigger Signals" list's last item, opening a new proposal for content review or retirement determination.

## Evolution History GC Strategy

`evolution/history/` generates full snapshots with each promotion and rapidly inflates with version accumulation. `evolution/proposals/` and `evolution/approvals/` are cleaned in tandem to maintain consistency.

**Retention Rules**:
- Always retain full snapshots of the most recent 10 versions.
- Retain one milestone snapshot every 10 versions (v10, v20, v30...) as long-term restore points.
- Snapshots of other versions are automatically cleaned after promoting the next version.

**Proposals / Approvals Tandem Cleanup Rules**:
- Each history version's `metadata.json` records `source: "proposal:<slug>"`, linking to the corresponding proposal and approval.
- When **all** associated history versions of a proposal have been GC-deleted, that proposal and its approval are cleaned simultaneously.
- Proposals / approvals not associated with any history version (still in draft, validating, approved-but-not-promoted) are **always retained**.
- Orphan approval files without a corresponding proposal file are also cleaned.

**Cleanup Trigger Timing**:
- Auto-triggered after each new version promotion (called at the end of [scripts/promote_skill_evolution.sh](../scripts/promote_skill_evolution.sh)).
- Can also be run manually (will not delete the current active version or the most recent 10 version snapshots).
- To temporarily skip auto-cleanup, set `SKIP_EVOLUTION_GC=1` before running the promotion script; run GC manually once afterward.

**Protected Snapshots (Never Deleted)**:
- The current version snapshot pointed to by `active_version.json`.
- Milestone version snapshots (version numbers divisible by 10 and ≥ v10).
- The most recent 10 version snapshots.
- Proposal / approval files associated with the above retained versions.
- In-progress proposals (WIP) not associated with any history are always retained.

**Dry-run Mode**:
- `gc_evolution_history.sh --dry-run` lists only what would be deleted without actually deleting.
- First deployment should dry-run to confirm the list.
