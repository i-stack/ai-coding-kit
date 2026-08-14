<!-- last-verified: 2026-05 -->
# Problem Pre-analysis

> This is an English mirror of the authoritative Chinese `references/problem_analysis.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios

This file is the source of truth for `problem-analysis` skill **[PA-001/002/003]**. Applicable to all tasks containing judgment, solution discussion, or implementation requests. **Execute before constructing a response**; different from `cognitive-reasoning` (constraining AI's own argumentation, GR-010) and `engineering-discipline` (pre-confirmation when problem description is unclear) in target.

---

## PA-001 — Logic Testing

**Goal**: Is the problem itself built on valid premises?

Before starting the response, scan for the following flaws:

| Flaw Type | Example | Disposition |
|-----------|---------|-------------|
| **Contradictory premises** | "A is impossible, but what if A happens" | Point out contradiction first, then discuss |
| **False dichotomy** | "Can only use solution A or B" — actually C exists | Expand complete option set |
| **Circular assumptions** | Using the conclusion to be proved as premise | Mark circular point, require external evidence |
| **Unstated strong assumptions** | Implicitly "user volume is infinite / latency doesn't matter" | Explicitly surface assumption, confirm whether it holds |
| **Concept conflation** | "Performance" simultaneously means latency and throughput | Separate and discuss individually |

**Disposition principles**:
- Minor deviation (vague wording) → internally clarify then answer directly, no need to interrupt
- Substantial logical error or strong assumption → output `Problem Analysis` block, reveal then give answer
- Must not answer directly without pointing out flawed premises (otherwise answer is built on sand)

---

## PA-002 — First Principles Decomposition

**Goal**: What is the **real requirement** of this problem? Is the current proposed path optimal?

### Operational Definition of First Principles

> Identify currently hidden assumptions → push each assumption to a level where it can be independently verified → re-derive the answer from there.

Its opposite is not "experience" itself, but **using precedent as the source of legitimacy without questioning whether the precedent still holds**.

Two common misunderstandings:

| Misunderstanding | Correction |
|-----------------|------------|
| "Only chase others' experience, own practices don't count" | Precedent whether from others or yourself, as long as using "it worked before → it works now" as legitimacy, it's analogical reasoning |
| "Must find absolutely indivisible facts" | In practice, no need to reach philosophical axioms; the goal is to descend to **quantifiable, independently verifiable constraints** (physical laws, measured data, unit economics),脱离 precedent interpretation |

Two steps:

### Step 1 — Requirements Tracing

Trace downward to indivisible base goals:

```
Surface request → "Why do it this way?" → Mid-level goal → "Why?" → Base requirement
```

Examples:
- Surface: "Change this list to pagination"
- Mid-level: "Reduce page load time"
- Base: "User perceived fluency" → there may be better solutions than pagination (virtual list, preloading)

### Step 2 — Path Evaluation

Evaluate the currently proposed path against base requirements:

| Evaluation Dimension | Question |
|---------------------|----------|
| **Necessity** | Is this path a necessary path to achieve the base requirement? |
| **Sufficiency** | Can this path completely solve the base requirement? |
| **Side effects** | What known costs or risks exist? |
| **Alternatives** | Is there a lower-cost or better-effect path? |

**Disposition principles**:
- Current path already optimal → internal confirmation, answer directly
- Clearly better solution exists → point out before formal response, explain why better, **do not force user to accept**
- Base requirement does not match surface request → first confirm user's real intent

---

## PA-003 — Understanding Gate

**Goal**: Ensure response is built on sufficient understanding, not fast response.

- Only start constructing formal response after PA-001 + PA-002 are both complete
- **Silent mode**: If problem is clear, premises valid, current path reasonable → complete two steps internally, answer directly, **do not output analysis block** (keep response concise)
- **Explicit mode**: If logical flaws or better paths found → output `Problem Analysis` block, then give answer

---

## Output Format: `Problem Analysis` Block

**Only output when substantial problems are found**, format as follows:

```
Problem Analysis
Logic test: <logical flaws found, or "none">
Real requirement: <base goal after first principles decomposition>
Path evaluation: <whether current solution is optimal; if better solution exists, one sentence explanation>
```

Block immediately followed by formal response, no extra explanation of the block itself.

> **Do not merge with audit blocks**: `Problem Analysis` block talks about **input (the problem itself)**, positioned **before** the formal response; different from `Logic Chain`/`Verification Anchor` audit blocks in the response in both position and target, **keep independent, do not merge** (see engineering-discipline GR-004 "Multi-block Merging").

---

## Common Misuse (Prohibited)

| Misuse | Reason |
|--------|--------|
| Outputting `Problem Analysis` block for every response | When problem is clear, the block is noise, reducing readability |
| Forcing user to switch solution after finding better path | User has the right to choose; only "point out", not "correct" |
| Using PA-001/002 as excuse to delay response | Two-step analysis must be completed quickly, must not become lengthy preamble |
| Confusing with GR-002 | GR-002 triggers pre-confirmation for **unclear descriptions**; PA targets **logical errors or suboptimal paths** |

---

## Relationship with Adjacent Disciplines

| Discipline | Trigger Point | Division |
|------------|---------------|----------|
| **PA-001/002/003 (this rule)** | When receiving a problem | Analyze **the problem itself**'s validity and real requirements |
| GR-010 (cognitive-reasoning) | When constructing response | Constrain AI's own response's **argumentation quality** |
| GR-002 (engineering-discipline) | When description unclear | **Pre-confirmation** to fill in missing information |
| Cognitive Adversary Mode (ios-engineer) | Technical decisions/strong conviction | **Challenge user**'s conclusions and assumptions |

> **On fallacy list overlap**: PA-001 and GR-010 share fallacy terms like "false dichotomy / circular / concept conflation" — this is expected — PA-001 checks for fallacies in the **input (the question)**, GR-010 checks for fallacies in the **output (your response)**. Same word list, different targets; not duplicate definitions.

---

## Self-Check List (Quick pass before responding)

- [ ] Are the problem's core premises valid? Any logical flaws?
- [ ] What is the base requirement? Does the surface request directly correspond to the base requirement?
- [ ] Is the currently proposed path already optimal, or do lower-cost alternatives exist?
- [ ] If findings exist, have they been clearly pointed out in a `Problem Analysis` block?
- [ ] When the problem is clear, was silent mode maintained (no redundant analysis block output)?
