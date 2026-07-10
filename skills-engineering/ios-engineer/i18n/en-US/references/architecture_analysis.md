<!-- last-verified: 2026-05 -->
# Architecture Analysis & Technical Debt Assessment

> This is an English mirror of the authoritative Chinese `references/architecture_analysis.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios
For the following tasks:
- Conducting **architecture reviews**, health scoring, and technical debt grading for an entire project or a business domain
- Performing **systematic risk identification**: cross-module stability, performance, and maintainability hazards
- After taking over an unfamiliar codebase, first building an index before proposing a remediation roadmap — rather than jumping straight into fixes
- Users initiating consulting with assessment-oriented questions like "architecture checkup", "is the current architecture problematic", "how severe is the technical debt", "where are the systemic risks"

This file only defines the disciplines, fields, and phases for **assessment-type output**. Specific fix implementations remain the responsibility of dedicated refs (architecture → [architecture_and_network.md](architecture_and_network.md), concurrency → [swift_concurrency.md](swift_concurrency.md), performance → [performance_optimization.md](performance_optimization.md), etc.).

## Why These Constraints
The real difficulty in "getting AI to stably output high-quality architecture analysis" is not analytical capability but **preventing four types of degradation**:
1. Hand-waving: outputting unsubstantiated conclusions like "recommend decoupling" or "recommend adding tests".
2. Dumping dozens of items at once: users cannot prioritize or act on them.
3. Mixing minimal fixes with architecture overhauls: short-term and long-term actions crammed into one recommendation.
4. Speculative leaps: drawing conclusions when information is insufficient, presenting guesses as facts.

Every rule in this file targets one of these degradation types. Skipping any one will immediately degrade output quality, so full execution is mandatory.

## Usage Rules
- Before entering Phase 2, Phase 1 index must be complete; no risk levels, health scores, or roadmaps may be output without an index.
- Default behavior: execute Phase 1 and stop; only continue to Phase 2–4 when the user explicitly requests "continue with full analysis", "output final report", or "complete it in one pass".
- Each round outputs **at most 5 issues**, sorted by severity; overflow items defer to the next round or become observation items.
- Conclusions must have code evidence; insufficient information must be explicitly labeled as "assumption pending confirmation", never treated as a conclusion.
- First provide "minimal-change actionable Plan A", then "long-term optimal Plan B"; the two must not be intermixed in the same paragraph.
- Comply with SKILL.md core iron rules (lock the main path first / minimal verifiable fix first / covered–uncovered–residual risk) and root-cause discipline from [root_cause_enforcement.md](root_cause_enforcement.md).

## Shortcut Phrases
When the user says only "architecture checkup", it is equivalent to:
- Execute this file's architecture analysis playbook on the current iOS project.
- Execute Phase 1 only — build the project index without outputting optimization suggestions, health scores, or risk levels.
- Phase 1 must cover module responsibilities, directory structure, core business flows, state/data flow, threading model, networking layer, and caching layer.
- All conclusions must distinguish "confirmed facts" from "assumptions pending confirmation".
- Stop after Phase 1 and wait for user confirmation to proceed to Phase 2.

When the user says "full architecture checkup" or "one-shot architecture checkup", it is equivalent to:
- Execute Phase 1–4 completely and output the final report.
- Risk items output at most Top 5, sorted by severity.
- Each risk must include the 10 mandatory fields defined in this file.
- Do not output vague conclusions without code evidence.
- Do not modify code; analysis only — unless the user explicitly requests fixes.

## Role & Capability Constraints
When entering this playbook, the default role is Staff iOS Engineer for the project, with:
- Architecture review capability
- Performance optimization capability
- Stability governance capability
- Engineering & maintainability governance capability

Goal: Without disrupting business iteration, identify and prioritize **systemic risks**, output an actionable remediation roadmap; do not suggest rewrites or cosmetic refactors unrelated to the primary risks.

## Analysis Scope
Scan in the following 6 dimensions; scan order ≠ output order — output is sorted by severity.

### 1. Architecture & Modules
- Are module boundaries clear
- Are dependency directions reasonable (reverse / circular dependencies)
- Is layering stable (UI / Domain / Data / Infra)
- Are there Massive ViewControllers / God Objects

Detailed principles see [architecture_and_network.md](architecture_and_network.md).

### 2. State & Data Flow
- Is the state source unique
- Are there races in state synchronization
- Is data flow traceable, replayable, testable
- Do async callback chains cause state drift

Detailed patterns see [ui_state_patterns.md](ui_state_patterns.md).

### 3. Concurrency & Thread Safety
- Is `@MainActor` usage correct
- Are `async/await` and `Task` lifecycles safe
- Are there data races, deadlock risks, priority inversions
- Are singletons, caches, shared mutable state thread-safe

Detailed requirements see [swift_concurrency.md](swift_concurrency.md).

### 4. Memory & Lifecycle
- Are retain cycles, closure captures, Timer / Observer properly released
- Do VC / ViewModel / Service lifecycles match
- Are images and large objects managed reasonably (peak memory risk)

### 5. Performance & Stability
- First screen, list scrolling, render blocking
- Off-screen rendering, frequent layout, main thread heavy work
- Network retries, timeouts, cancellation, idempotency, token refresh
- Cache consistency, stale reads, cache penetration, avalanche
- High crash-risk paths (null values, out-of-bounds, concurrency timing)

Detailed metrics and paths see [performance_optimization.md](performance_optimization.md) and [networking_patterns.md](networking_patterns.md).

### 6. Engineering & Maintainability
- SOLID violations
- Test coverage and testability (unit / integration tests)
- Observability (logging, analytics, error grading)
- Refactoring friction (coupling points, migration cost)

Detailed requirements see [testing_strategy.md](testing_strategy.md) and [observability_logging.md](observability_logging.md).

## Mandatory Fields Per Issue
Each output must include all 10 fields below; if a field cannot be provided, explicitly write "pending confirmation" and state what information is missing.

1. **Severity**: Critical / High / Medium / Low. Criteria:
   - Critical: will directly cause Crash, data loss, financial loss, or large-scale user unavailability
   - High: significant degradation in stability / performance / security, or core business iteration structurally slowed by coupling
   - Medium: maintainability or局部 UX issues; accumulates to High over time
   - Low: style or consistency issues; no behavioral impact
2. **Location**: file path + relevant symbol / method (precise to class or function)
3. **Evidence**: key code snippet (as concise as possible, retaining enough context to illustrate the issue)
4. **Problem Mechanism**: why it happens (structural reason, not just symptom description)
5. **Trigger Conditions**: under what scenarios it appears (device, concurrency, network, data scale, etc.)
6. **Impact Scope**: which of user / business / stability / performance are affected
7. **Fix Plan A — Minimal Change**: low-risk, quickly deployable止血 plan
8. **Fix Plan B — Long-term**: architecture-level optimization direction
9. **Cost Estimate**: person-days + key risk points
10. **Benefit Estimate**: quantifiable or verifiable description of stability / performance / maintainability improvement

Missing fields are the most common source of quality degradation. If the output contains "recommend refactoring XXX" without location, evidence, or cost, that item must be rejected and rewritten.

## Execution Flow (strictly phased; no skipping)

### Phase 1 — Project Index Building (understand only, do not optimize)
Purpose: Before producing any conclusions, build a verifiable factual foundation.

Read first:
1. Project configuration: `.xcodeproj` / `.xcworkspace` / `Package.swift` / `Podfile`
2. Directory & modules: source directories, resource directories, test directories, internal frameworks / packages
3. App entry: `App` / `SceneDelegate` / `AppDelegate` / root router or root container
4. Assembly layer: dependency injection, Router / Coordinator, Service registration, global state entry points
5. Data boundaries: networking layer, persistence, caching, DTO / Entity / ViewState mapping
6. Core business flows: launch, login, home page, main business detail or transaction flows
7. Quality entry points: test directories, CI configuration, logging and analytics wrappers

Output only:
1. Module inventory and responsibilities
2. Directory structure summary
3. Core business main flows
4. State flow / data flow paths
5. Threading model
6. Networking layer and caching layer structure

Expression requirements: clearly distinguish "confirmed facts" from "assumptions pending confirmation"; do not intermix. **Phase 1 must not output any optimization suggestions, scores, or severity judgments.**

### Phase 2 — Architecture & Boundary Assessment
Based on Phase 1 index, output only **Critical / High** risk items, at most 5; each with all 10 mandatory fields.

### Phase 3 — Concurrency / Memory / Performance Deep Dive
Targeted review: main thread blocking, list rendering, async timing, Task lifecycle, shared state contention, cache consistency.
At most 5 items, fields same as Phase 2. Concurrency evidence must include at least one of: task creation, state writeback, main-thread hop.

### Phase 4 — Phased Refactoring Roadmap
Must be divided into 3 segments, each with independent goals, change scope, risks, rollback strategy, and acceptance criteria (quantifiable):
- 1–2 weeks: quick止血
- 1–2 months: structural governance
- 1–3 months: architecture upgrade

Roadmap items must **explicitly map to Phase 2 / Phase 3 issues** (which issue is resolved by which phase); no orphan roadmap actions allowed.

## Final Output Format
After Phase 4, aggregate and output in the following 8 fixed sections; missing sections must explicitly state "not applicable in this round":

1. **Project Health Score (0–100, with scoring rationale)**
2. **Architecture Maturity & Technical Debt Level**
3. **Top Risk List** (at most 5, sorted by severity)
4. **Immediate Actions (1–2 weeks)**
5. **Mid-term Governance (1–2 months)**
6. **Long-term Evolution Recommendations (1–3 months)**
7. **Refactoring Roadmap** (milestones / dependencies / acceptance criteria)
8. **Supplementary Information Needed** (if any; if none, write "information sufficient for this round")

Section 1 scoring must list deduction items and rationale, not just a total score. Section 8 is not optional courtesy — it is part of output discipline: every conclusion labeled "assumption pending confirmation" must list the supplementary information needed here.

## Anti-Patterns (would undermine analysis credibility)
- Drawing conclusions without evidence, or treating "common recommendations" as specific risks (e.g., unsubstantiated "recommend introducing Coordinator")
- Outputting more than 5 risks at once; users cannot prioritize
- Mixing minimal fixes with long-term plans, causing short-term actions to be dragged down by architecture overhauls
- Roadmap actions without corresponding issues
- Scoring before Phase 1 is done
- Using vague conclusions like "recommend strengthening tests" or "recommend decoupling" without location or evidence

## Quick Architecture Analysis Mode (for plan-grill PG-005 delegation)

When plan-grill's PG-005 delegates a quick architecture analysis to ios-engineer, **skip full Phase 1–4** and produce only the following.

### Applicability Conditions
- PG-003 interrogation involves cross-file dependencies across a small number of files (typically ≤10).
- Only needs to answer "call chain", "modification impact scope", "module coupling" — no health score or refactoring roadmap needed.
- Difference from full checkup: no Phase 1–4 flow, no 10 mandatory fields, no health score — describe the status quo only, do not evaluate quality.

### Output Format

Save to `.plan-reviews/<plan-slug>/architecture-analysis.md`:

```markdown
# Architecture Analysis — <plan-slug>

## Files Involved
- `<absolute file path>` — <one-line responsibility>
- ...

## Call Chain
\```
<entry class.method>()
  → <called class.method>()  // <trigger condition or data flow note>
  → ...
\```

## Modification Impact
- Modifying `<File A>`: affects `<File B>` (<brief reason>), `<File C>` (<brief reason>)
- ...

## Potential Risks (if any)
- <concise description; mark "pending confirmation" if no code evidence>
- If no risks, write "No significant risks identified in this analysis"
```

### Discipline
- Do not output health scores, technical debt levels, or refactoring roadmaps.
- Do not output optimization suggestions or "recommend refactoring XXX" conclusions.
- Only describe the **status quo** (call relationships + impact scope); do not evaluate quality.
- Call chains use text arrows (`→`); Mermaid diagrams not required — but if call chain complexity is high (≥5 layers or ≥4 branches), a Mermaid diagram may be added for clarity.
- Modification impact must specify **concrete affected files and methods**; vague statements like "affects multiple modules" are not allowed.

## Collaboration with Other Refs
- For specific fix approaches: jump to [architecture_and_network.md](architecture_and_network.md) / [swift_concurrency.md](swift_concurrency.md) / [performance_optimization.md](performance_optimization.md) / [networking_patterns.md](networking_patterns.md) / [ui_state_patterns.md](ui_state_patterns.md) by hit dimension
- For migration risk gates and phased regression: [migration_strategy.md](migration_strategy.md)
- For decision record format: [decision_records.md](decision_records.md)
- For review dimension checklists: [review_checklists.md](review_checklists.md)
- For output skeleton field details: [examples.md](examples.md)
