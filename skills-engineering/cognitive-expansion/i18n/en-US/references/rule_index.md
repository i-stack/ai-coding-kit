<!-- last-verified: 2026-07 -->
# Rule ID Index (cognitive-expansion)

> This is an English mirror of the authoritative Chinese `references/rule_index.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file is the source-of-truth index for `CE-NNN` rules in [SKILL.md](../SKILL.md). New / modified / retired IDs **must be updated here first, then synced to SKILL.md**.
- ID format: `^[A-Z]+-\d{3}$`, prefix `CE-` is exclusively for cognitive-expansion's own contract, does not conflict with ios-engineer's `IR-/SYM-/ROUTE-/OUT-` or global `GR-`.
- Numbers can have gaps, no mandatory consecutive constraint; new entries use the largest prefix number +1.
- Once published, IDs are not reused: after retirement, they remain in the "Retirement Record" section, marked `retired` with a replacement ID specified; retired IDs should not appear in SKILL.md.
- The behavior gate `scripts/validate-skill-behavior.sh` Check 2 asserts: each `CE-NNN` declared in SKILL.md is defined in this file with a table row `| CE-NNN |`, and the definition anchor must be one of heading `## CE-NNN` / bracket `[CE-NNN]` / table `| CE-NNN |`; inconsistency results in non-zero exit.

## Cognitive Expansion Rules CE-NNN

| ID | Status | Summary | SKILL.md Anchor |
|----|--------|---------|-----------------|
| CE-001 | active | Tier 0 trigger gate: dual conditions (contains judgment component AND can produce ≥1 falsifiable blind spot) must both be met to append cognitive footnote, otherwise silent | `## Rule Index` |
| CE-002 | active | Reframe: elevate the question to a more general judgment/learning question; pure execution tasks write "reframe skipped" | Same as above |
| CE-003 | active | Blind spot (falsifiable hard criterion): 1 hidden assumption/missed dimension/pitfall, must contain (assumption X) + (observable trigger Y) + (if Y then X is wrong negation condition); if can't write it, skip entire section | Same as above |
| CE-004 | active | Adjacent domain (mechanism-related): 1 adjacent field comparison, must be mechanism-related to current question, no same-tech-stack word-shuffling repetition of main text | Same as above |
| CE-005 | active | Takeaway: 1 reusable self-check question or if-then rule, no chicken soup | Same as above |
| CE-006 | active | Tier 0/Tier 2 mutual exclusion: when Cognitive Adversary (Tier 2) is triggered, output full calibration structure, no separate Tier 0; this exclusion extends to the preamble lightweight calibration section (carried by CAM when active) | Same as above |
| CE-007 | active | Deep Dive · Mental Model: model name + 1 sentence on how it applies to this problem | Same as above |
| CE-008 | active | Deep Dive · Cross-domain Analogy: non-same-tech-stack, mechanism-aligned analogy; must name the mapped mechanism, no cliché/word-shuffle analogies (guardrails see cognitive_expansion.md §Tier 3) | Same as above |
| CE-009 | active | Deep Dive · Verification Action: 1 specific action doable within 7 days | Same as above |
| CE-010 | active | Sycophancy self-check: after writing, pass three questions (adjacent domain not word-shuffle / takeaway not chicken soup / blind spot falsifiable) | Same as above |
| CE-011 | active | Skip conditions: do not write Tier 0 if user says "just give me the answer/no extensions" or gate not met | Same as above |
| CE-012 | active | Adjacent domain comparison pool: pick 1 from the pool and must be mechanism-related | Same as above |
| CE-013 | active | Deduplication with L2/L0: when logical-reasoning "logic chain (falsifiable/gaps)" or problem-analysis "problem analysis" has been issued in the same round, blind spot must change dimension, no restatement | Same as above |

## Retirement Record

| ID | Status | Retirement Reason | Replacement ID |
|----|--------|-------------------|----------------|
| (None yet) | | | |
