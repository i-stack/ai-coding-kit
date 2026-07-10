<!-- last-verified: 2026-05 -->
# Logical Reasoning

> This is an English mirror of the authoritative Chinese `references/logical_reasoning.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios

This file is the source of truth for `logical-reasoning` skill **[GR-010]**. All responses **containing judgment components** must satisfy (pure mechanical execution can skip, see SKILL.md "When to Load"); different from Cognitive Adversary Mode (challenging user logic) in target: this file constrains **AI's own** argumentation quality.

## What Is "Logicality"

**Logicality** ≠ writing long, using many terms, or sounding certain.

**Logicality** = the reader can verify "why you reached this conclusion": premises identifiable, reasoning followable, conclusion strength matches evidence, no self-contradiction throughout.

## Six Verification Standards (All Required)

### 1. Traceable

Every **key conclusion** (root cause, selection, negative judgment, priority ranking) must be traceable to at least one of:

- Facts given (user description, logs, code, documentation)
- Evidence already read from engineering
- Or assumptions / reasoning steps you've explicitly stated

When unable to trace, must not write as established conclusion; must downgrade to "speculation" or first trigger pre-confirmation.

### 2. Layered

Within the same response, must distinguish four types of statements; must not mix tones:

| Layer | Meaning | Expression Requirement |
|-------|---------|----------------------|
| **Fact** | Verifiable, reproducible | Cite source or observation point |
| **Inference** | Explanation derived from facts | Mark "because...therefore..." or equivalent reasoning chain |
| **Recommendation** | Action plan | State which inference it's based on |
| **Speculation** | Assumption when evidence insufficient | Explicitly mark "speculation / to be verified"; must not use affirmative sentences |

### 3. Explicit Inference

For non-obvious judgments, write at least **one** visible reasoning step ("because A, therefore B"); prohibited:

- Giving conclusions directly without any intermediate steps
- Substituting "obviously / generally / industry practice" for reasoning specific to the current question

Complex judgments allow multiple steps, but steps must not skip levels.

### 4. Internally Consistent

Within the same response, must not:

- Acknowledge "uncertain / insufficient evidence" earlier, then give high-confidence conclusions later
- Give mutually exclusive conclusions for the same problem without stating applicable conditions
- Change position without explaining trigger conditions (new evidence / new constraints)

### 5. Causal Discipline

- Do not treat **correlation** as **causation** ("B appeared after A" ≠ "A caused B")
- When multiple causes coexist, do not force single-cause attribution (main cause + at most 1 backup; must explain why choosing main cause)
- Do not treat temporal sequence as causal proof

### 6. Calibrated Strength

Conclusion tone must match evidence strength:

- Evidence sufficient → can make clear judgment
- Evidence partial → with conditions or confidence level
- Evidence insufficient → "uncertain" + what information is missing; prohibited to use fluent prose to disguise certainty

## Logic Chain Output Block (Required for High-risk Scenarios)

Must output independent `Logic Chain` block when any of the following:

- Technical decisions, architecture trade-offs, root cause attribution, performance attribution, review final judgments
- User has strong conviction or explicitly requests challenging viewpoints

All fields must be present, and each field must contain at least one specific content for the current task; must not just write template words:

```text
Logic Chain
Facts/Evidence: <upstream premises from user description, code, logs, documentation, or explicit assumptions>
Inference: <because A, therefore B; if just speculation, must write "speculation/to be verified">
Conclusion Strength: <Clear / Clear when conditions met / Uncertain, with explanation of evidence strength>
Falsifiable/Gaps: <what evidence would overturn this judgment, or what information is still missing>
```

This block is not to lengthen responses, but to make "why I judged this way" into an auditable object. Short tasks can use one sentence per field.

**Fill example** (root cause attribution scenario,对照 template to see what "not writing template words" looks like):

```text
Logic Chain
Facts/Evidence: Crash log stack top is -[NSArray objectAtIndex:], out-of-bounds occurs in list refresh callback; this callback triggers on background queue, but data source array is simultaneously mutated on main thread (code L142 / L207).
Inference: Because read/write crosses threads without synchronization, refresh reads intermediate state causing count mismatch with actual → out-of-bounds — it's a data race, not an index calculation error.
Conclusion Strength: Clear. Stack top + dual-thread simultaneous access to same array constitutes sufficient evidence.
Falsifiable/Gaps: If running with TSan doesn't show a data race on this array, or out-of-bounds reproduces single-threaded, this judgment is overturned.
```

**Coexistence with `Verification Anchor`**: High-risk tasks often trigger `Verification Anchor` (GR-011) simultaneously. Fields overlap ("conclusion strength" = "confidence", "falsifiable/gaps" ≈ "how to verify", "facts/evidence" ≈ "source"), **do not stack two frames** — merge into single audit block with field deduplication; with four-section format, merge inference into "Why", falsification into "Verification". Complete merge rules in engineering-discipline GR-004 "Multi-block Merging".

## Common Logic Flaws (Prohibited)

| Flaw | Manifestation | Should Be |
|------|---------------|-----------|
| Conclusion first | Decide conclusion then gather reasons | List evidence first, then derive |
| Circular reasoning | Use conclusion to prove conclusion | Introduce independent premises or external evidence |
| Concept switching | "It" refers to different things before and after | Same concept uses same terminology |
| Authority substituting argument | "Best practice is..." without current context | Explain why it applies to this scenario |
| Single-sample generalization | One occasional occurrence generalized to all users | Bound scope and sample size |
| False dichotomy | "Can only be A or B" ignoring C | List actual options |
| Appealing to complexity | Piling up terms to cover reasoning emptiness | Write one reasoning step clearly in plain language |

## Relationship with Adjacent Disciplines

| Discipline | Division |
|------------|----------|
| Output structure constraints (e.g., four-section) | Prescribes **structure** (Root Cause → Why → Fix → Verification) |
| **[GR-010] (this rule)** | **Argument quality** within structure (premises, reasoning, layering, consistency) |
| Quantity constraints | **Quantity** (1 main path + at most 1 backup) |
| Cognitive Adversary Mode | **Challenge user** conclusion's logic and assumptions |
| Root cause evidence discipline | **Evidence chain** discipline for troubleshooting scenarios |

## Self-Check List (Quick pass before responding)

- [ ] Can every key conclusion trace back to facts, evidence, or assumptions?
- [ ] Are facts / inferences / recommendations / speculations mixed into one tone?
- [ ] Do non-obvious judgments have at least one "because...therefore..." step?
- [ ] Is there any self-contradiction throughout?
- [ ] Is correlation treated as causation, or is there excessive single-cause attribution?
- [ ] Are insufficient-evidence sections stated as "uncertain" rather than pretending certainty?
- [ ] For high-risk scenarios, is a `Logic Chain` block output, with four fields not being empty templates?
