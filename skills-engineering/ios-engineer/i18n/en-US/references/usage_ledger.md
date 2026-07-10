<!-- last-verified: 2026-06 -->
# Usage Ledger (Real Task Hit Observation)

> This is an English mirror of the authoritative Chinese `references/usage_ledger.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Purpose
- Structured append of "expected hit / actual hit / deviation / result" from each real iOS engineering task completion to [evolution/usage/usage.jsonl](../evolution/usage/usage.jsonl).
- Is the data source for Step 4 summarize / proposal clustering; this file only defines schema and write protocol, **does not implement statistics**.
- Maintainer/tools: writing relies on [scripts/append_usage_entry.sh](../scripts/append_usage_entry.sh); batch import from audit blocks relies on [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh); legality guarded by [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh).

## 1. JSONL Schema (one line per entry)

```json
{
  "time": "2026-05-08T14:30:00+0800",
  "tool": "claude-code",
  "session_id": null,
  "prompt_summary": "Search page rapid input results cross-contamination",
  "task_type": "concurrency",
  "expected_rules": ["GR-005", "ROUTE-007", "SYM-003"],
  "hit_rules": ["GR-005", "ROUTE-007"],
  "missed_rules": ["SYM-003"],
  "deviations": ["Did not explicitly cancel old request chain"],
  "outcome": "partial",
  "evolution_signal": "Refine expression"
}
```

| Field | Type | Required | Constraint |
|------|------|------|------|
| `time` | string | Yes | ISO8601 with timezone, e.g., `2026-05-08T14:30:00+0800` |
| `tool` | string | Yes | Enum: `codex` / `claude-code` / `cursor` / `manual` / `other` |
| `session_id` | string \| null | Yes | Three-platform fillable session ID for traceability; fill `null` when not needed |
| `prompt_summary` | string | Yes | **Summary**, 5-200 characters; no raw prompts, source code snippets, or identifiable project names |
| `task_type` | string | Yes | Enum: `layout` / `parameter-pass-through` / `concurrency` / `review` / `migration` / `mcp-control` / `notifications` / `privacy` / `persistence` / `storekit` / `extensions` / `other` |
| `expected_rules` | string[] | Yes | Elements must be IDs with `status=active` in [rule_index.md](rule_index.md) (e.g., `GR-005`) |
| `hit_rules` | string[] | Yes | Same as above; may be empty array |
| `missed_rules` | string[] | Yes | **Must equal** `expected_rules - hit_rules` set difference; append script auto-calculates |
| `deviations` | string[] | Yes | Free-text array; may be empty array |
| `outcome` | string | Yes | Enum: `pass` / `partial` / `fail` |
| `evolution_signal` | string | Yes | Enum: `none` / `Refine expression` / `Add capability` / `Merge duplicates` / `Retire rule` (consistent with 4 change types in [self_evolution.md](self_evolution.md)) |

## 2. Write Protocol (universal for human/script)

- **Append one entry after each real task completion** — regardless of success or failure. **Stable successful tasks must also be recorded**: only recording failures would severely bias the ledger toward negative samples, and hit rate statistics would be directly distorted.
- When a single session has multiple independent tasks, record as multiple entries (each corresponding to one task_type judgment).
- `prompt_summary` must be desensitized:
  - Do not paste raw user input
  - Do not paste source code snippets or stack traces
  - Do not paste file paths containing identifiable project names (unless the project itself is public)
  - 5-character minimum ensures there is content; 200-character maximum prevents abuse
- `expected_rules` source suggestion: first go to [rule_index.md](rule_index.md) to find ROUTE-XXX matching `task_type`, then add cross-task iron rules (GR-002 pre-confirmation / GR-005 minimal fix / GR-008 residual risk statement, etc.).
- `hit_rules` must be honest — if unsure, **leave empty** rather than guessing. Guessing will pollute Step 4 hit rates.

## 3. CLI Writing

```bash
bash scripts/append_usage_entry.sh \
  --tool claude-code \
  --task-type concurrency \
  --prompt-summary "Search page rapid input results cross-contamination" \
  --expected-rules "GR-005,ROUTE-007,SYM-003" \
  --hit-rules "GR-005,ROUTE-007" \
  --deviations "Did not explicitly cancel old request chain" \
  --outcome partial \
  --evolution-signal "Refine expression"
```

- Non-compliant fields exit non-zero; do not pollute ledger
- `time` auto-takes system time
- `missed_rules` auto-calculated from `expected - hit`; **do not pass manually**
- Optional: `--session-id <id>` / omit `--deviations` (defaults to empty array) / omit `--evolution-signal` (defaults to `none`)
- Locked atomic write; concurrency-safe

## 4. Three-Platform Audit Block Format (Unified)

Any tool (Codex CLI / Claude Code / Cursor) outputs the following text block at appropriate times; then batch-imported into ledger by human using [scripts/extract_usage_audit.sh](../scripts/extract_usage_audit.sh):

```
<usage-audit>
tool: codex
task-type: concurrency
prompt-summary: Search page rapid input results cross-contamination
expected-rules: GR-005, ROUTE-007, SYM-003
hit-rules: GR-005, ROUTE-007
deviations: Did not explicitly cancel old request chain
outcome: partial
evolution-signal: Refine expression
</usage-audit>
```

- Tags and field names fixed (kebab-case; corresponds to JSONL field underscore versions)
- Array fields comma-separated
- Empty array: write empty string (e.g., `deviations:`)
- `session-id` may be omitted; equivalent to null
- Multiple blocks separated by blank lines; extract script parses all at once

## 5. Three-Platform system-prompt Snippets (Pasteable)

Each platform's system-prompt adds the corresponding section below. **Unified core constraint**: only output audit block when task hits ios-engineer theme and `task_type` falls within 11 fixed slugs + `other`; do not fabricate `hit-rules`; leave empty if unsure.

### 5.1 Codex CLI

Add to `~/.codex/AGENTS.md` or project-level `AGENTS.md`:

```
## ios-engineer skill audit
When task involves iOS / Swift / SwiftUI / UIKit / Xcode engineering, and task_type falls within
{layout, parameter-pass-through, concurrency, review, migration, mcp-control,
notifications, privacy, persistence, storekit, extensions, other},
append a <usage-audit> block after final answer (format per ios-engineer skill
references/usage_ledger.md §4):
- tool: codex
- task-type: one of the above 12
- prompt-summary: 5-200 character desensitized summary
- expected-rules / hit-rules: use IR-XXX / SYM-XXX / ROUTE-XXX / OUT-XXX / GR-XXX form,
  sourced from ios-engineer/references/rule_index.md active set
- deviations: what was deviated from; leave empty if none
- outcome: pass / partial / fail
- evolution-signal: none / Refine expression / Add capability / Merge duplicates / Retire rule
Do not fabricate hits; leave hit-rules empty if unsure.
```

### 5.2 Claude Code

Add to project-level `CLAUDE.md` or global `~/.claude/CLAUDE.md`:

```
## ios-engineer skill audit
After completing any iOS / Swift / SwiftUI / UIKit / Xcode engineering task, append a
<usage-audit> block at the end of your answer. Format strictly follows
ios-engineer/references/usage_ledger.md §4.
- tool: claude-code
- task-type must fall within {layout, parameter-pass-through, concurrency, review,
  migration, mcp-control, notifications, privacy, persistence, storekit,
  extensions, other}
- expected-rules / hit-rules use ios-engineer/references/rule_index.md
  status=active IDs
- Leave hit-rules empty when unsure; do not guess from memory
- prompt-summary desensitized, 5-200 characters
Non-iOS engineering tasks (writing docs, reading code, answering API questions) do not need audit blocks.
```

### 5.3 Cursor

Add to `.cursorrules`:

```
## ios-engineer skill audit
For iOS / Swift / SwiftUI / UIKit / Xcode engineering tasks, append <usage-audit> block
after answer; format per ios-engineer/references/usage_ledger.md §4.
- tool: cursor
- task-type ∈ {layout, parameter-pass-through, concurrency, review, migration,
  mcp-control, notifications, privacy, persistence, storekit, extensions, other}
- expected-rules / hit-rules use IR-XXX / SYM-XXX / ROUTE-XXX / OUT-XXX / GR-XXX
- Leave empty if unsure; do not guess
- prompt-summary 5-200 character desensitized
```

## 6. Batch Import

```bash
bash scripts/extract_usage_audit.sh path/to/transcript.txt
```

- Extracts all `<usage-audit>...</usage-audit>` blocks from the file
- Parses KV; calls `append_usage_entry.sh` per block
- **Any block with incomplete or illegal fields → entire batch rejected**; already-written entries not rolled back (v1 limitation), so extract designed as dry-run validating all before unified write
- No interactive confirmation; extract is "audit block author's copier", not an auditor

## 7. Notice on Self-Grading Bias

**Important**: Model outputting audit blocks is essentially LLM self-grading. This leads to:

- `hit_rules` systematically overestimated (models tend to claim they did it)
- `deviations` systematically underestimated (models don't easily notice their own deviations)
- Same model has common blind spots in both "executing task" and "auditing task" roles

**Therefore this ledger's data is "biased draft"**, not ground truth. Truly reliable hit rates depend on [validation_scenarios.md](validation_scenarios.md) + [evolution/scenarios/*.json](../evolution/scenarios/) regression scenario set for independent replay confirmation.

Step 4's summarize script buckets by `tool` field, exposing self-grading bias between different tools — this is the ledger's most useful secondary diagnosis at this stage.

**Lightweight self-grading verification**: [scripts/lint_hit_rules.sh](../scripts/lint_hit_rules.sh) cross-checks audit block's `hit-rules` against response body template fields for IR-001 / GR-002 / GR-004 / IR-006 / GR-008 / GR-010 — these rules all have stable text anchors (pre-confirmation / version prerequisite / residual risk statement / four-section / findings-first skeleton / logic chain block). Script outputs PASS / FAIL / UNSUPPORTED per entry; FAIL > 0 exits non-zero; UNSUPPORTED does not count as failure. This script is a pre-filter before ledger entry; does not replace validation_scenarios replay — the latter remains the final authority on hit rates.

## 8. Proposal Candidate Signal Thresholds

[scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) L69-L72 hardcodes 4 threshold constants; exceeding any surfaces as proposal candidate signal in summarize output. This section is the documented mirror of those 4 constants:

| Constant | Value | Candidate Proposal Signal | Meaning |
|------|----|-------------|------|
| `MISSED_RULE_THRESHOLD` | 3 | Add capability | Same `rule_id` appears in `missed_rules` ≥ 3 times → existing rule expression may be insufficient or lacks trigger conditions |
| `TASK_TYPE_OTHER_THRESHOLD` | 5 | Add capability (new task_type) | `task_type=other` accumulates ≥ 5 entries → existing 11 slugs incomplete; may need new scenario |
| `DEVIATION_THRESHOLD` | 2 | Refine expression | Same deviation string repeats ≥ 2 times → stable failure pattern; corresponding rule needs tighter expression |
| `TOOL_DIVERGENCE_THRESHOLD` | 0.4 | Self-grading bias comparison | Same `rule_id` hit_rate differs ≥ 40% across different `tool` (and each side expected ≥ 5) → tool/model understanding of rules is split; needs independent replay confirmation |

**Drift prevention**: Thresholds correspond one-to-one with [scripts/summarize_usage_ledger.sh](../scripts/summarize_usage_ledger.sh) `*_THRESHOLD` constants. Changing this document must simultaneously change the script; otherwise summarize output (`thresholds` field carries script truth) and document explanation will drift. Future proposals may consider adding "script constant ↔ table figures" bidirectional verification to [scripts/validate_skill_evolution.sh](../scripts/validate_skill_evolution.sh).

## 9. Maintenance

- Adding `task_type` enum values: first expand [validation_scenarios.md](validation_scenarios.md) and [evolution/scenarios/](../evolution/scenarios/), then sync [scripts/validate_usage_ledger.sh](../scripts/validate_usage_ledger.sh) and this file.
- Adding `tool` enum values (e.g., Aider / Continue etc.): directly modify this file + `validate_usage_ledger.sh` + `append_usage_entry.sh` whitelist.
- Consider sharding or compressed archiving only when ledger gets very large (> 10k rows); Step 3 does not reserve sharding mechanism.
