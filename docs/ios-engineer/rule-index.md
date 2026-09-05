# Rule Index

<Badge type="tip" text="49 IDs registered" />

The canonical Rule ID registry for iOS Engineer. Every rule ID is defined here first, then referenced in `SKILL.md`. An automated validation script (`validate-rule-ids.sh`) ensures bidirectional consistency.

## Iron Rules (IR-NNN)

| ID | Status | Summary |
|----|--------|---------|
| IR-001 | active | Output language anchors to user's input language |
| IR-006 | active | Version context block before conclusions on concurrency/availability/SwiftUI/network |
| IR-011 | active | Cognitive adversary mode: restatement, counter-argument, hidden assumptions, falsifiability |

## Global Rules (GR-NNN)

Carried by independent global skills, cross-platform. The ios-engineer skill mirrors them for reference.

| ID | Status | Summary |
|----|--------|---------|
| GR-001 | active | Security compliance — never expose credentials |
| GR-002 | active | Pre-confirmation block when info is insufficient |
| GR-003 | active | Single root cause (1 primary + max 1 secondary) |
| GR-004 | active | Four-section output (cause → why → fix → verify) |
| GR-005 | active | Minimal fix first |
| GR-006 | active | Tool budget gate — 3 failures or 15 turns blocks |
| GR-007 | active | No code formatting (prevents diff noise) |
| GR-008 | active | Change coverage declaration |
| GR-010 | active | Traceable logic chain with strength indicators |

## Symptom Routing (SYM-NNN)

| ID | Status | Summary |
|----|--------|---------|
| SYM-001 | active | Crash / assertion / force unwrap → root_cause_enforcement |
| SYM-002 | active | UI misalignment / constraint conflicts / list jitter |
| SYM-003 | active | State chaos / async write-back / stale request override |
| SYM-004 | active | Request failure / auth refresh / pagination |
| SYM-005 | active | Lag / slow launch / memory / energy |
| SYM-006 | active | Naming chaos / force unwrap / access control |
| SYM-007 | active | Legacy project chaos / fear of touching modules |

## Task Routing (ROUTE-NNN)

10 routing entries covering: debugging / architecture design / code review / migration / testing / dependency / build & CI / security & permission / data persistence / Core Skills (markdown/code generation).

## Output Templates (OUT-NNN)

6 output templates for: root cause analysis, architecture review, code review, migration plan, test design, and decision record.

---

See the [canonical rule_index.md](https://github.com/i-stack/ai-coding-kit/blob/feature_3.0.0/skills-engineering/ios-engineer/references/rule_index.md) for the complete registry with status and anchor points.
