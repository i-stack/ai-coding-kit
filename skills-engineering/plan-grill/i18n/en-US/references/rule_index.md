<!-- last-verified: 2026-11 -->
# Rule ID Index (plan-grill)

> This is an English mirror of the authoritative Chinese `references/rule_index.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage
- This file indexes `PG-NNN` rules declared in [SKILL.md](../SKILL.md). Add / change / retire IDs **here first, then SKILL.md**.
- ID format: `^[A-Z]+-\d{3}$`. Prefix `PG-` is exclusive to plan-grill.

## Plan Grill rules PG-NNN

| ID | Status | Summary | SKILL.md anchor |
|----|--------|---------|-----------------|
| PG-000 | active | Requirements clarity gate: auto-grill only when a blocking decision cannot be found from code/context and would substantially change delivery | `## Seven Core Rules` |
| PG-001 | active | One question at a time | same |
| PG-002 | active | Recommended answer + one-sentence reason | same |
| PG-003 | active | Traverse the design tree; check code instead of asking when possible | same |
| PG-004 | active | Lock output: write workspace-root `.plan-reviews/<plan-slug>/PLAN.md` and read it back; do not execute before confirmation | same |
| PG-005 | active | Architecture analysis delegation: when a platform engineer is loaded, fill architecture-analysis.md from that skill's quick-architecture template | same |
| PG-006 | active | History recall is delegated to global historical-recall; this skill does not call it inline | same |

## Retired

| ID | Status | Reason | Replacement |
|----|--------|--------|-------------|
| (none) | | | |
