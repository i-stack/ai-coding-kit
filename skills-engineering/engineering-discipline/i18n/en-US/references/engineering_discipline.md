<!-- last-verified: 2026-06 -->
# Engineering Discipline

> This is an English mirror of the authoritative Chinese `references/engineering_discipline.md`.
> In case of discrepancies, the Chinese source takes precedence.

This file is the source of truth for the `engineering-discipline` skill. Applies to all engineering tasks, not limited by platform or language.

## GR-001 Security Compliance Defense

**Iron rule**: AI Agent must never read, print, or output the specific contents of sensitive environment variables or secret files, and must never commit them to the repository.
- Strictly prohibited to view or output `.env`, `.git/` sensitive configurations, password files, or directories containing private keys/certificates.
- Before executing `run_shell_command` commands with system write access, destructive, or highly sensitive operations, a command self-check must be performed first. If potential sensitive credential exposure is detected, immediately block and prompt the user.
- Strictly prohibited to transmit any current Workspace keys to insecure external network endpoints (API / Webhook / Web-fetch).

## GR-002 Pre-confirmation

For questions with unclear descriptions, insufficient context, or ambiguity, must first output ≥1 specific questions in a standalone "Pre-confirmation" block literally before continuing with the solution.

**Trigger conditions (typical):** Vague wording / runtime environment not provided / reproduction conditions not provided / attempted solutions not provided / affected scope not stated.

**Format requirements**: Output as a standalone block literally, with section heading "Pre-confirmation" as the mechanical verification anchor; only saying "need more information" or "suggest supplementing" in prose is considered a violation of this rule.

**Principle**: Facts that can be read from engineering or context should be read first, don't make the user repeat input; only ask the minimum questions needed to disambiguate the main assumption; specific follow-up dimensions are completed by the corresponding task's primary read ref.

**Coordination (with PG-000 / GR-006 / PA-003):** If `plan-grill` PG-000 has already entered grilling, this rule's pre-confirmation question is absorbed as the first grill question, and no separate "Pre-confirmation" block is opened. Grilling proceeds per PG-001 "one question at a time"; this rule's "≥1 question" folds into the grill cadence and is not asked again. If `GR-006` strategic interruption triggers during grilling or troubleshooting, its standalone "Pre-confirmation" block merges with this rule at the same anchor — the ≥2 strategic branches the interruption block must contain absorb this rule's question and are not listed separately. This differs from `problem-analysis` PA-003's "Problem Analysis" block: PA-003 addresses the input (the problem) itself and sits before the formal reply, so it is kept independent from this block (see GR-004 Multi-block Merging).

## GR-003 Single Root Cause Lock

By default, first lock 1 highest-probability root cause or main path, with at most 1 backup supplement; do not expand multiple major branches simultaneously to consume context.

**Applicable**: All troubleshooting, root cause analysis, architecture selection tasks.

**Principle**: Increase probability weight when there's evidence; when unable to distinguish, first ask 1 most critical confirmation question, rather than expanding long parallel guesses.

## GR-004 Four-Section Output

Default output follows the four-section format below, platform-independent:

| Section | Semantics |
|---------|-----------|
| **Root Cause** (conclusion) | Highest probability root cause or main path |
| **Why** | Evidence or reasoning supporting the judgment |
| **Fix** | Minimal structural repair steps |
| **Verification** | How to prove no side effects introduced |

If the task hits a long template requirement, the four-section format serves as the summary layer, with the detailed template as an additional layer.

**Exception**: Code review / PR Review and other review scenarios may use findings-first format; specific conditions and skeleton defined by platform skill (e.g., ios-engineer OUT-002).

### Multi-block Merging (When Multiple High-risk Disciplines Trigger Simultaneously)

High-risk tasks often trigger multiple structure blocks simultaneously (`Logic Chain` GR-010 / `Verification Anchor` GR-011 / Four-section / `Problem Analysis` PA / `Residual Risk Statement` GR-008). Principle: **one reply one audit area, do not stack duplicate fields**.

**Keep independent (different positions or mechanical anchors, do not merge):**

- `Problem Analysis` (PA): Talks about **input (the problem)**, positioned **before** the formal reply → keep independent.
- `Residual Risk Statement` (GR-008): Mechanical verification anchor, its own rules require literal independence → do not merge into any block.
- Cognitive expansion footnote (cognitive-expansion): Already self-gated and is a footnote → keep independent.

**Merge (same position, overlapping "evidence-inference-strength-falsification" fields):**

`Logic Chain` (inward: constraining own argumentation) and `Verification Anchor` (outward: conclusion grounding with the world) have highly overlapping fields; with four-section format, further overlaps with "Why / Verification". When triggered simultaneously, merge into a single audit block with field deduplication:

| Semantic Slot | Overlapping Fields | Merge Destination |
|---------------|-------------------|-------------------|
| Evidence / Source | Logic Chain "facts/evidence" · Verification Anchor "basis/source" · Four-section "Why" | Write once; with four-section goes to "Why" |
| Inference | Logic Chain "inference" | Goes to four-section "Why" |
| Confidence | Logic Chain "conclusion strength" · Verification Anchor "confidence" | Same measure, write once |
| Falsification / Verification | Logic Chain "falsifiable/gaps" · Verification Anchor "how to verify" · Four-section "Verification" | Write once; with four-section goes to "Verification" |

**Criterion**: Each fact written only once; "conclusion strength = confidence" written once; outward-specific "how to verify (primary source / tool)" and inward-specific "gaps / assumptions" can each take one line in the merged block, but do not start a separate frame. Without four-section format (pure factual Q&A), `Logic Chain` + `Verification Anchor` merge into a single block.

#### Inclusion of Calibration Layer and iOS-specific Blocks

The above merging covers the trio's (engineering / logic / epistemic) audit blocks. The following structures must coordinate under the same "one reply one audit area, field deduplication" principle to avoid stacking into silos:

- **Cognitive Adversary Mode (CAM / ios-engineer Tier 2):** Its Step 0–6 and `Confidence: X%` field overlap heavily with `Logic Chain` and `Verification Anchor` semantics. Coordination: **do not duplicate output semantics, but preserve the CAM mechanical format** — when CAM is active, `Logic Chain` and `Verification Anchor` do not open as separate blocks (their semantics are already carried by CAM fields); CAM's own fields (Step 0–6 + `Confidence`) are output verbatim per the Cognitive Adversary detail spec, and must not be omitted or merged into other blocks (see that mode's "Relationship with Engineering Skills"); the preamble's lightweight calibration section is also carried by CAM at this point (see global cognitive calibration section). Only when CAM is unavailable does it fall back to a merged `Logic Chain` + `Verification Anchor` block.
- **iOS-specific blocks:** `Version Baseline` (IR-006), `<usage-audit>` (audit block) do not overlap with four-section / Verification Anchor semantics and stay independent; but they must be declared not to conflict with the audit area — `Version Baseline` belongs to pre-constraints, `<usage-audit>` to the tail; neither crowds the audit area.

#### Cross-block Confidence Coordination

All confidence / strength signals within the same reply must be **co-sourced**: `Logic Chain` "conclusion strength", `Verification Anchor` "confidence", CAM `Confidence`, `Cognitive Calibration` "uncertain" — when they point to the same judgment, they must write the same value / level; there must be no "high strength" + "low confidence" + "unverified" fighting each other. Take the weakest falsifiable evidence as the basis (minimum), appear only once within the merged block, and normalize the caliber to **the single confidence / conclusion-strength field retained this round** (when CAM carries it: `Confidence: X%`; otherwise `Verification Anchor`'s "confidence" or `Logic Chain`'s "conclusion strength").

#### Read and Budget Ceiling when Multiple SKILLs Stack (Mitigate Stack Explosion)

When multiple global skills trigger in the same round, do not each "force full-text read" indiscriminately, exhausting budget and forcing a GR-006 interruption:

- **Graded reading:** Each skill's "must first read references/...md in full" only executes when **that skill's detail spec is genuinely triggered**; an untriggered skill does not load its ref (the preamble section itself is the gate summary, which can be used to judge).
- **Priority order:** When multiple skills trigger in the same round, allocate read and output budget per `problem-analysis (input) → engineering-discipline / logical-reasoning / epistemic-integrity (argumentation and delivery) → plan-grill (plan locking) → ios-engineer (platform specifics)`; argumentation refs are read first, platform / tool refs only when the task falls on that platform.
- **Budget declaration:** Within a single reply, the total number of independent output blocks triggered by stacked skills should be controlled; those mergeable by this SOP (audit-class) merge into a single audit area; those not mergeable (problem analysis / residual risk / cognitive footnote / usage-audit) stay independent but concise; if still approaching GR-006's 15-turn / 3-failure threshold, prioritize completing "minimal usable reply + residual risk statement", leaving deep dives to later rounds rather than spreading multiple skill full-texts in parallel.

## GR-005 Minimal Fix Priority

First give the minimal verifiable fix; do not first propose whole-module rewrites, architecture overhauls, or large-scale refactoring.

**Principle**: One change only solves the currently confirmed problem; do not add hypothetical future requirements; do not attach incidental cleanup. If large-scale refactoring is truly needed, first give the minimal fix to stabilize the current problem, then discuss the refactoring path separately.

### Engineering Delivery Quality Gate

This section is the implementation constraint of GR-005: minimal fix does not mean only making local compilation pass. Implementation, fix, or refactoring solutions must simultaneously satisfy the following minimum thresholds:

- **No boundary smuggling**: Changes must not access implementation details across layers for local availability, bypass established abstractions, or temporarily copy business logic. If cross-boundary access is necessary, first explain the real owner, caller, dependency direction, and alternatives.
- **Public surface reviewable**: When adding or modifying public APIs, module boundaries, cross-module calls, must explain callers, visibility, replaceability, and compatibility impact; default to minimum exposure scope, do not expand API for "might be useful later".
- **Specifications triggered by changes**: When public API semantics change, error model changes, configuration changes, or cross-team calling convention changes occur, must synchronize necessary documentation comments, naming semantics, and validation methods; do not use specification requirements as an excuse to format unrelated code.
- **Tests graded by risk**: Pure logic changes prioritize unit tests; state or UI behavior changes add interaction / snapshot / regression verification; cross-module paths add integration tests; release risk adds build, CI, grayscale, or rollback verification.
- **CI is not an afterthought**: When changes involve public APIs, module boundaries, build configuration, dependencies, release paths, or high-risk refactoring, delivery description must include whether local verification and CI / build gates are covered; if not covered, write into residual risk statement.

## GR-007 Do Not Format Code (Prevent Diff Noise)

Do not format code unless explicitly asked to format the current code.

**Reason**: Formatting is a destructive diff operation; in code review and refactoring it covers up real changes and increases merge conflict risk.

**Implementation details**:
- **Strictly prohibit full-file reformatting**: When executing Lint auto-fix (e.g., `eslint --fix`) or code beautification (e.g., `prettier --write`), prohibited to run global formatting on the entire file or unchanged areas.
- **Format only changed lines**: If the development tool or IDE supports it (e.g., `clang-format` line ranges mode), must specify range to only operate on `git diff` affected Staged changed lines.
- **Eliminate blank line/layout noise**: Committed code changes must absolutely not contain meaningless newline, indentation, or trailing whitespace adjustments; ensure Commit Diff is highly focused.

## GR-006 Budget Interception and Proactive Interruption

**Interruption conditions**:
- **Troubleshooting death loop interception**: When locating the same bug or compile/link failure, if 3 fix attempts still don't resolve the issue, must stop retrying.
- **Depth defense**: During a single engineering task interaction, if tool call depth (turn count) exceeds 15, the path has deviated.

**Execution details**:
- When any interruption condition is met, AI must proactively announce a **strategic interruption** (interruption is not giving up, but loss containment), and output a standalone "Pre-confirmation" block.
- In the confirmation block: honestly acknowledge current cognitive limitations, organize the 3 failed paths already tried, point out epistemological vulnerabilities in current reasoning (GR-010/011 intersection), provide user with ≥2 decision branches with strategic turning significance for user adjudication.
- **Coordination (with GR-002 / PG-000):** If this interruption occurs during `plan-grill` PG-000 grilling, this interruption block **merges with `engineering-discipline` GR-002's "Pre-confirmation" at the same anchor**, without duplicate output; its ≥2 strategic branches absorb GR-002's question, and grilling proceeds per PG-001 "one question at a time" (see GR-002 Coordination clause).
- Strictly prohibited to use temporary `guards`, `retries`, or irrelevant `logs` to forcibly delay tool consumption.

## GR-008 Change Coverage Statement

Any change (troubleshooting fix / architecture change / concurrency migration / performance optimization / refactoring implementation) must declare three fields:

```text
Residual Risk Statement
- Covered: Paths / scenarios / callers verified by this change
- Not covered: Paths / scenarios / callers explicitly not verified
- Residual risk: Assumptions / edge cases / dependencies that could still fail even if the above pass
```

**Requirements**: Three fields must exist as independent paragraphs literally, with section heading "Residual Risk Statement" as the mechanical verification anchor; not allowed to scatter the three fields into the "Verification" paragraph or merge into one block of text. Do not promise "no new risks".
