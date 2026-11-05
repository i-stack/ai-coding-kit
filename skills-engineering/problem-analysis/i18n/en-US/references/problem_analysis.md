<!-- last-verified: 2026-11 -->
# Problem Pre-analysis

> This is an English mirror of the authoritative Chinese `references/problem_analysis.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Applicable Scenarios

This file is the source of truth for `problem-analysis` skill **[PA-001/002/003]**. Applicable to all tasks containing judgment, solution discussion, or implementation requests. **Execute before constructing a response**; different from `cognitive-reasoning` (constraining AI's own argumentation, GR-010) and `engineering-discipline` (pre-confirmation when problem description is unclear) in target.

When adjacent skills are not loaded, this skill's split, three states, and block format still apply independently: do not rename fields, refuse the block, or rewrite the `Problem Analysis` block as `Pre-confirmation` just because GR-002 / GR-013 / `Logic Chain` are absent.

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
| **Concept conflation** | "Performance" simultaneously means latency and throughput | If context uniquely disambiguates → silent; if not and the two readings change the answer → explicit then answer |

### "Substantial" flaws (independent criteria)

Count as substantial **if and only if at least one** of the following holds; otherwise it is a minor deviation:

1. **Contradictory premises**: the set of premises cannot all be true at once.
2. **Circular assumption**: the conclusion to be proved is used as a premise.
3. **False dichotomy**: a non-exhaustive option set is written as "only A or B", and which option is chosen would change the answer.
4. **Unstated strong assumption**: context does not supply the assumption, and its truth value would flip the conclusion.

**Not substantial** (do not emit the block):

- Synonyms or concept conflation that context uniquely disambiguates
- Missing environment / reproduction / scope (→ GR-002 pre-confirmation)
- The user did not propose an implementation path
- Fact-class questions (verify; do not grow a requirements tree)

**Disposition principles**:

- Minor deviation → internally clarify then answer directly, no `Problem Analysis` block
- Substantial flaw → PA-003 explicit-then-answer (emit the block, then answer)
- Only substantial flaws forbid answering without pointing them out; minor deviations may stay silent

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
| "Must find absolutely indivisible facts" | No need to reach philosophical axioms; the goal is to descend to **quantifiable, independently verifiable constraints** (physical laws, measured data, unit economics), leaving precedent interpretation |

Two steps:

### Step 1 — Requirements Tracing

Trace downward to independently verifiable constraints (no need to reach philosophical axioms):

```
Surface request → "Why do it this way?" → Mid-level goal → "Why?" → Base requirement
```

### Step 2 — Path Evaluation

**Run this step only when the user proposed an implementation path.** If the user only asks why, only asks a fact, only wants a diagnosis, or specifies no approach → skip this step; do not evaluate "whether the current path is optimal".

Evaluate the currently proposed path against base requirements:

| Evaluation Dimension | Question |
|---------------------|----------|
| **Necessity** | Is this path a necessary path to achieve the base requirement? |
| **Sufficiency** | Can this path completely solve the base requirement? |
| **Side effects** | What known costs or risks exist? |
| **Alternatives** | Is there a lower-cost or better-effect path? |

**Fact / reasoning split (same boundary as GR-013)**:

- **Fact-class** (a library API, an event, an interface behavior, a number) → **verify**; do not derive the answer from first principles applied to empirical facts. Only run a light PA-001 scan (are the premises self-contradictory); do not grow a Step 1/2 requirements tree. Default silent.
- **Reasoning / trade-off** (architecture choice, logical derivation, requirements decomposition) → this rule applies.
- Whether the question is fact or reasoning is decided by `cognitive-reasoning` GR-013; this rule decomposes requirements only on reasoning-class questions. If GR-013 is not loaded, still perform this split; do not grow a requirements tree on a fact question.

### Better path vs stop-and-confirm (mutually exclusive)

Decide by whether the **surface deliverable and the base goal are substitutes**, not by "the base goal sounds different":

| Relation | Criterion | State | Example |
|----------|-----------|-------|---------|
| **Means** | The surface path can still achieve the base goal; it may just not be optimal | **Explicit then answer** (better path) | "The list stutters on scroll; switch it to pagination" → pagination can still reduce stutter; a virtual list may be better. Emit the block, then still answer along the user's pagination path; do not force a switch |
| **Substitute / conflict** | Doing the surface deliverable is no longer doing the base thing, or doing the base thing makes the surface deliverable unnecessary, and context cannot tell which they want | **Stop and confirm** | "Change this internal admin audit log to blockchain anchoring" → on-chain anchoring and "an auditable log" are substitute deliverables. Emit the block, then only ask which they want; do not implement before confirmation |
| **The same thing** | Surface is the base goal, or context already disambiguated | **Silent** | "Change the login button copy to Sign In" |

If "change this list to pagination" has **no** stutter/performance cue, pagination itself can be the requirement → **silent**; do not invent "what you really want is fluency".

**Disposition principles**:

- Current path already optimal, or the user proposed no path → internal confirmation, answer directly
- Clearly better solution exists (means relation) → point out with a `Problem Analysis` block before the formal response, explain why better, **do not force the user to accept**, then still answer along the user's original path
- Surface deliverable and base goal are substitutes or in conflict → stop and confirm; do not advance the solution before confirmation

---

## PA-003 — Understanding Gate

**Goal**: Ensure response is built on sufficient understanding, not fast response.

Only start constructing formal response after PA-001 + PA-002 are both complete. Three mutually exclusive states:

| State | Condition | Action |
|-------|-----------|--------|
| **Silent** | Premises valid; no path or path is reasonable; minor deviation can be disambiguated; fact-class | Complete two steps internally, answer directly, **do not output analysis block** |
| **Explicit then answer** | Substantial logical error, unstated strong assumption, or a better path (means relation) | Output `Problem Analysis` block, then give answer |
| **Stop and confirm** | Surface deliverable and base goal are substitutes or in conflict, and context cannot tell which they want | Output `Problem Analysis` block; write "unconfirmed, do not proceed" in `Path evaluation`; follow the block with only a confirmation question. Do not write a solution or call tools that change system state before confirmation |

Missing information (environment / reproduction / scope) → GR-002 pre-confirmation, not this rule.

---

## Output Format: `Problem Analysis` Block

**Output only in explicit-then-answer or stop-and-confirm**, format as follows:

```
Problem Analysis
Logic test: <logical flaws found, or "none">
Real requirement: <base goal after first principles decomposition>
Path evaluation: <whether current solution is optimal; if better solution exists, one sentence explanation; on stop-and-confirm write "unconfirmed, do not proceed">
```

Explicit then answer: block is immediately followed by the formal response, no extra explanation of the block itself.
Stop and confirm: block is followed only by the confirmation question; do not advance the solution before confirmation.

Chinese mechanical field names (`逻辑检验` / `真实需求` / `路径评估`) remain the source of truth when the runtime locale is zh-CN. This English mirror is not an alias that replaces those names in zh-CN output.

> **Do not merge with audit blocks**: `Problem Analysis` block talks about **input (the problem itself)**, positioned **before** the formal response; different from `Logic Chain`/`Verification Anchor` audit blocks in the response in both position and target, **keep independent, do not merge** (see engineering-discipline GR-004 "Multi-block Merging").

---

## Common Misuse (Prohibited)

| Misuse | Reason |
|--------|--------|
| Outputting `Problem Analysis` block for every response | When problem is clear, the block is noise, reducing readability |
| Emitting the block on diagnosis / fact / no-path requests | No path → skip Step 2, default silent |
| Treating a "better path" as "stop and confirm" | Pagination can still achieve fluency (means relation): emit the block then answer, do not stop |
| Forcing user to switch solution after finding better path | User has the right to choose; only "point out", not "correct" |
| Implementing the surface solution after stop-and-confirm | Do not advance before confirmation |
| Using PA-001/002 as excuse to delay response | Two-step analysis must be completed quickly, must not become lengthy preamble |
| Confusing with GR-002 | GR-002 triggers pre-confirmation for **unclear descriptions**; PA targets **logical errors, suboptimal paths, or substitute goals** |

---

## Relationship with Adjacent Disciplines

| Discipline | Trigger Point | Division |
|------------|---------------|----------|
| **PA-001/002/003 (this rule)** | When receiving a problem | Analyze **the problem itself**'s validity and real requirements |
| GR-013 (cognitive-reasoning) | When classifying the question | Facts are verified; reasoning may use PA-002 |
| GR-010 (cognitive-reasoning) | When constructing response | Constrain AI's own response's **argumentation quality** |
| GR-002 (engineering-discipline) | When description unclear | **Pre-confirmation** to fill in missing information |
| Cognitive Adversary Mode (cognitive-reasoning, CAM-001~005) | Technical decisions/strong conviction | **Challenge user**'s conclusions and assumptions; when both hit, finish problem review first |
| plan-grill (PG-000) | After this rule | Grill the implementation decision tree; do not start before problem review completes |

> **On fallacy list overlap**: PA-001 and GR-010 share fallacy terms like "false dichotomy / circular / concept conflation" — this is expected — PA-001 checks for fallacies in the **input (the question)**, GR-010 checks for fallacies in the **output (your response)**. Same word list, different targets; not duplicate definitions.

---

## Self-Check List (Quick pass before responding)

- [ ] Are the problem's core premises valid? If flawed, does it hit one of the four independent "substantial" criteria?
- [ ] What is the base requirement? Are surface and base a means relation, a substitute relation, or the same thing?
- [ ] Did the user propose a path? If not, was Step 2 skipped?
- [ ] Is this question fact or reasoning? Was first principles misused on a fact-class question?
- [ ] Did the three states stay mutually exclusive: silent / explicit then answer / stop and confirm?
- [ ] When silent, was the `Problem Analysis` block omitted? On stop-and-confirm, is Path evaluation "unconfirmed, do not proceed", and was the solution not advanced?
