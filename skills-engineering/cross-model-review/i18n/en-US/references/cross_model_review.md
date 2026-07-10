<!-- last-verified: 2026-07 -->
# Cross-Model Adversarial Review

> This is an English mirror of the authoritative Chinese `references/cross_model_review.md`.
> In case of discrepancies, the Chinese source takes precedence.

> **Source of truth**: This file is the sole detailed specification. `cross-model-review/SKILL.md` is the entry point; full copies for each platform are synced by `scripts/sync-skills.sh`; within Cursor projects, `sync-agent-preamble.sh` generates `.cursor/rules/cross-model-review.mdc`.

## Positioning

cross-model-review addresses the 2nd failure mode of AI-assisted coding: **the plan sounds right but will crash**. A single model doing both planning and grading cannot discover its own structural blind spots — it **must** rely on **cross-provider model** adversarial review.

This skill is based on the Act 2 approach from `chaseai-yt/grill-me-codex` (MIT license), adapted for this project's multi-adapter architecture.

## Prerequisites

- `PLAN.md` must already be locked by `plan-grill` (PG-004 output). When there's no PLAN.md, run plan-grill first.
- The current environment must have at least two reviewer CLIs from different providers available (CMR-001探测).

## CMR-001 Auto-discover Reviewers

Directly probe for reviewer CLIs in the current environment. The installed skill does not depend on repository-level scripts; within the `ai-coding-kit` repository, auxiliary scripts can optionally be run:

```bash
bash skills-engineering/scripts/detect-review-clis.sh
```

Universal probing method:

```bash
command -v codex >/dev/null 2>&1 && codex --version
command -v gemini >/dev/null 2>&1 && gemini --version
command -v claude >/dev/null 2>&1 && claude --version
```

Organize the probe results into equivalent JSON (manual organization, no file generation required):

```json
{
  "clis": [
    {"name":"codex","available":true,"path":"...","version":"0.142.5","readonly_flag":"-s read-only","noninteractive_flag":"exec"},
    {"name":"gemini","available":true,"path":"...","version":"0.49.0","readonly_flag":"--approval-mode plan","noninteractive_flag":"-p"},
    {"name":"claude","available":false}
  ],
  "available_count": 2
}
```

**Hard gate**: When available provider count < 2, **stop** and prompt the user to install missing CLIs; do not fabricate cross-model. Cross-model adversarial review requires at least two CLIs from different providers.

## CMR-002 Recommended Combinations + User Selection

From available CLIs, recommend a combination of two **different providers**:

| Main Agent | Recommended Reviewer Combination |
|---|---|
| Claude (host is Claude Code) | codex + gemini (avoid Anthropic) |
| Codex (host is Codex CLI) | gemini + claude (avoid OpenAI) |

Present the candidate table to the user for confirmation or adjustment:

```
Detected available reviewers:
1. codex 0.142.5  (OpenAI)     Read-only: -s read-only
2. gemini 0.49.0  (Google)     Read-only: --approval-mode plan

Recommended combination: codex + gemini (two different providers)
Confirm? Or specify two different reviewers?
```

**Do not silently make the choice for the user**. Only enter review after user confirmation. If the user specifies only one reviewer, must explain this degrades to ordinary single-model review and the `cross-model-review` process will not be used.

## CMR-003 Reviewer Read-only (Three Adapter Invocation Commands)

Each reviewer must run in read-only mode. Reviewers do not write code, only read PLAN.md and related repo files, outputting `VERDICT: APPROVED` or `VERDICT: REVISE` + specific modification suggestions.

### In-project Output Directory (Mandatory)

Reviewer raw output, intermediate output, and delivery logs must all be saved under the **current project root directory**; using `/tmp` as a reviewer output buffer is prohibited. Recommended to create before starting review:

```bash
REVIEW_SLUG="<yyyy-mm-dd-slug>"
REVIEW_DIR="./.plan-reviews/${REVIEW_SLUG}"
RAW_DIR="${REVIEW_DIR}/raw"
mkdir -p "${RAW_DIR}"
grep -qxF ".plan-reviews/" .gitignore 2>/dev/null || printf "\n.plan-reviews/\n" >> .gitignore
```

Rules:

- `PLAN.md` and `PLAN-REVIEW-LOG.md` are deliverables at the current project root.
- If PLAN.md references `.plan-reviews/<slug>/architecture-analysis.md`, the reviewer must treat it as read-only input and review it together with PLAN.md.
- Reviewer raw output is written to `${RAW_DIR}/<reviewer>-round<N>.<txt|json>`.
- When optionally archiving, sync project root `PLAN.md` / `PLAN-REVIEW-LOG.md` to `${REVIEW_DIR}/`; `raw/` is preserved as-is.
- When creating `.plan-reviews/`, by default append `.plan-reviews/` to the current project root `.gitignore`; review evidence is local work product by default, unless the user explicitly requests version control.
- `/tmp` is only allowed for ordinary one-time shell scratch unrelated to this process; it must not be used to save reviewer verdicts, critiques, thread/session ids, or any cross-model-review evidence requiring audit.

### Review Prompt (Sent to Reviewer Each Round)

```
You are an adversarial reviewer for an implementation plan. Be skeptical and specific — your job is to find what breaks, not to be agreeable. Read the plan at PLAN.md, any architecture-analysis.md file referenced by PLAN.md, and any repo files you need (you are read-only). Identify concrete flaws: security holes, race conditions, missing edge cases, schema conflicts, wrong assumptions, observability gaps, simpler alternatives. For each, give a one-line fix. Do NOT modify any files. End your reply with EXACTLY one line: `VERDICT: APPROVED` if the plan is sound enough to implement, or `VERDICT: REVISE` if it still has material problems.
```

### Codex Adapter

```bash
# Round 1 — New session, get thread_id
codex exec -s read-only --json -o "${RAW_DIR}/codex-round1.json" "$REVIEW_PROMPT" \
  < /dev/null 2>/dev/null | grep '"type":"thread.started"'

# Round 2+ — Resume same session (Codex remembers prior criticisms)
codex exec resume "$THREAD_ID" -c sandbox_mode="read-only" --json \
  -o "${RAW_DIR}/codex-round${ROUND}.json" \
  "I revised the plan. Re-review PLAN.md — check whether your prior findings are addressed and flag anything new. End with VERDICT: APPROVED or VERDICT: REVISE." \
  < /dev/null 2>/dev/null >/dev/null
```

**Key points**:
- `< /dev/null` is mandatory — `codex exec` reads stdin in non-interactive mode; without redirection it will hang permanently.
- `resume` does not support `-s`; must use `-c sandbox_mode="read-only"` to force read-only.
- 600s timeout guard (see security rules).

### Gemini Adapter

```bash
# Round 1 — New session
gemini -p "$REVIEW_PROMPT" --approval-mode plan -o json --skip-trust \
  > "${RAW_DIR}/gemini-round1.json"

# Round 2+ — Resume same session
gemini -r "$SESSION_ID" -p "$RESUME_PROMPT" --approval-mode plan -o json \
  > "${RAW_DIR}/gemini-round${ROUND}.json"
```

**Key points**: `--approval-mode plan` is read-only mode; `-r/--resume` supports `latest` or session index.

**Invocation Notes**:

1. **Preamble and workspace**: gemini startup loads global `~/.gemini/GEMINI.md` (written by this project's `sync-agent-preamble.sh`); the preamble requests reading files under `~/.gemini/skills/`, but workspace restrictions may refuse → produces `Error executing tool read_file: Path not in workspace` noise. This does not block the reviewer's main process.
   - Mitigation: Add `--include-directories ~/.gemini/skills` when invoking to eliminate noise.
2. **context-calibrator**: If `GEMINI_API_KEY` is a third-party relay (not Google official), it may not support the `context-calibrator` model → `Hot start calibration failed` 503. This error is noise and does not prevent the reviewer from outputting VERDICT.

### Claude Adapter

```bash
# Round 1 — New session
claude -p "$REVIEW_PROMPT" --permission-mode plan --output-format json \
  > "${RAW_DIR}/claude-round1.json"

# Round 2+ — Resume same session (resume parameters per claude --help)
claude --resume "$SESSION_ID" -p "$RESUME_PROMPT" --permission-mode plan --output-format json \
  > "${RAW_DIR}/claude-round${ROUND}.json"
```

> Claude adapter's resume parameters must be verified against actual `claude --help`; if resume is unavailable in the first version, it can be downgraded to passing complete conversation history (messages array) each round.

### First Version Does Not Pin Model

Each adapter uses the **default model** in the CLI configuration. `--model` is only passed when the user explicitly specifies it. This is consistent with Chase upstream's "don't casually pin model" safety experience — pinning `gpt-5.x-codex` variants will 400 under ChatGPT account authentication.

## CMR-004 Main Agent Arbitration

After each reviewer returns:

1. Complete invocation of all selected reviewers for this round, reading in-project raw files (`${RAW_DIR}/<reviewer>-round<N>.<txt|json>`).
2. Append each to project root `PLAN-REVIEW-LOG.md`: `## Round <N> - <reviewer>` + full critique + raw file relative path.
3. Summarize this round's verdict:
   - **All** reviewers return `VERDICT: APPROVED` → can proceed to Resolution (convergence).
   - **Any** reviewer returns `VERDICT: REVISE` → main agent decides **which are worth adopting**. Revise `PLAN.md`. Append `### Orchestrator response` to LOG: Accepted / Rejected + reasoning. Proceed to next round.
   - Any reviewer fails to output a legal verdict → this round fails, stop and inform the user; do not treat missing verdict as approval.
4. **Arbitration discipline**:
   - Adopt criticisms with evidence (specific to code/assumptions/edge cases).
   - Reject criticisms that don't hold, with reasoning (e.g., "reviewer misread X, actual is Y").
   - Neither blindly follow (otherwise lose arbitration value) nor ignore (otherwise lose adversarial value).

## CMR-005 MAX_ROUNDS + Deadlock

| Parameter | Default | Meaning |
|---|---|---|
| `MAX_ROUNDS` | `5` | Hard limit. Loop terminates here. |
| `PLAN_FILE` | `PLAN.md` | Plan locked by plan-grill. |
| `LOG_FILE` | `PLAN-REVIEW-LOG.md` | Append-only argumentation record, is a deliverable. |
| `RAW_DIR` | `.plan-reviews/<date>-<slug>/raw` | Reviewer raw output directory, must be within current project root. |

If `rounds=3` is passed at invocation, use that value to override `MAX_ROUNDS`. Echo the parsed value before starting.

### Resolution (User Final Sign-off)

- **APPROVED**: Present final PLAN.md + 3 improvement summaries + round count. Ask: "After N rounds of cross-model review. Implement now?" Only write code after user agrees. **No code written between the two acts.**
- **deadlock (MAX_ROUNDS exhausted without APPROVED)**: **Do not pretend approved**. List each unresolved point + main agent's counter-position, hand to user for adjudication. One clearly marked disagreement is better than a false "approved".

## Archiving (Optional, User-triggered)

After review completion, main agent prompts user whether to archive. Archiving saves PLAN.md + PLAN-REVIEW-LOG.md to `.plan-reviews/` under the **current project root** for future reference on similar problems — "what questions were asked when designing rate limiting last time? What defects were found?"

### Archive Directory Structure

```
<project-root>/.plan-reviews/
└── <YYYY-MM-DD>-<slug>/
    ├── PLAN.md              # Plan locked by plan-grill
    ├── PLAN-REVIEW-LOG.md   # Complete argumentation record from cross-model-review
    ├── architecture-analysis.md  # Optional, PG-005 quick architecture analysis
    ├── raw/                 # Reviewer raw output (one file per reviewer per round)
    │   ├── claude-round1.json
    │   └── gemini-round1.json
    └── SUMMARY.md           # Optional, manually organized summary
```

### Trigger Flow

1. After Resolution (APPROVED or deadlock), main agent prompts: "Review complete. Archive to `./.plan-reviews/<date>-<slug>/`? You can edit PLAN.md / PLAN-REVIEW-LOG.md before saving."
2. User provides slug (e.g., `login-rate-limit`).
3. Main agent executes:

   ```bash
   ARCHIVE_DIR="./.plan-reviews/$(date +%Y-%m-%d)-${SLUG}"
   mkdir -p "${ARCHIVE_DIR}/raw"
   grep -qxF ".plan-reviews/" .gitignore 2>/dev/null || printf "\n.plan-reviews/\n" >> .gitignore
   cp PLAN.md PLAN-REVIEW-LOG.md "${ARCHIVE_DIR}/"
   # If PLAN.md referenced PG-005 architecture analysis file, also copy as "${ARCHIVE_DIR}/architecture-analysis.md".
   ```

4. User can optionally write `SUMMARY.md` (manually organized: key grilling questions, discovered defects, fix key points).

### Archiving Principles

- **Saved by project**: Archived to current project root's `.plan-reviews/`, not into the skill repository; different projects are independent. Reviewer raw output also belongs to audit evidence and must be preserved under that directory's `raw/`.
- **Ignored by default**: When creating `.plan-reviews/`, must by default write `.plan-reviews/` to current project root `.gitignore`. If the team确实wants to share review archives, the user should explicitly remove the ignore or selectively copy organized summary files.
- **Manual organization**: Before archiving, user can edit PLAN.md / PLAN-REVIEW-LOG.md, trimming noise and adding summaries; not mechanical saving.
- **Purpose**: Knowledge accumulation, reference for similar problems.
- **Commit boundary**: Do not commit `.plan-reviews/` by default; if committing, prefer manually organized `SUMMARY.md` or desensitized archives, not raw reviewer output.

### When Not to Archive

- Trivial review (no learning value)
- User explicitly says "don't archive"
- Sensitive project (PLAN.md contains business logic, not suitable for leaving traces)

## PLAN-REVIEW-LOG.md Format

```markdown
# Plan Review Log: <title>

MAX_ROUNDS=<n>
Reviewers:
- <cli/model A>
- <cli/model B>

## Round 1 - <reviewer>
<critique>
VERDICT: REVISE

### Orchestrator response
Accepted:
- <accepted point 1>
Rejected:
- <rejected point 1> because <reason>

## Resolution
<approved | deadlock>
```

## Security Rules

1. **Reviewer read-only each round** — codex `-s read-only` / resume `-c sandbox_mode="read-only"`; gemini `--approval-mode plan`; claude `--permission-mode plan`. Reviewer never writes files.
2. **`< /dev/null` mandatory** (codex) — non-interactive stdin not redirected will hang permanently (0% CPU silent freeze).
3. **No `/tmp` reviewer buffering** — reviewer raw output, verdicts, critiques, thread/session ids, PLAN-REVIEW-LOG must all be written under current project root, recommended `.plan-reviews/<date>-<slug>/raw/`; otherwise audit chain is not reproducible.
4. **600s timeout guard** — each reviewer invocation adds a 10-minute limit. Claude Code's Bash tool passes `timeout: 600000`; pure shell uses `timeout 600` (Linux) or `gtimeout 600` (macOS coreutils). Timeout treated as failure, stop and inform user, no blind retries.
5. **Do not pin model** — use CLI default model, unless user explicitly specifies.
6. **Loop must terminate at MAX_ROUNDS** — hard limit, no infinite loops.
7. **Deadlock does not pretend approved** — when not converged, mark honestly and hand to user for adjudication.

## Skip Conditions

- No PLAN.md (run plan-grill first)
- Trivial changes (no cross-model review needed)
- User explicitly says "implement directly"
- Available reviewer providers < 2 (CMR-001 hard gate)

## Arbitration Quality Self-Check

Before review ends, go through:

- [ ] Does every REVISE have an Accepted or Rejected record?
- [ ] Does every Rejected have reasoning written?
- [ ] Did all reviewers APPROVE in the same round before entering Resolution?
- [ ] Are all reviewer raw outputs saved under current project root (e.g., `.plan-reviews/<date>-<slug>/raw/`), with no `/tmp` used?
- [ ] Does PLAN-REVIEW-LOG.md completely preserve all rounds of argumentation?
- [ ] At deadlock, was it honestly marked without pretending approved?

## Acknowledgments

This skill is based on `chaseai-yt/grill-me-codex` (MIT license, https://github.com/chaseai-yt/grill-me-codex) Act 2 cross-model adversarial review mechanism. The Codex adapter's invocation commands (`codex exec -s read-only`, `resume -c sandbox_mode`, `< /dev/null` anti-hang, timeout 600s) come directly from upstream validation (2026-06-04). Extended to three-adapter (codex/gemini/claude) auto-discovery architecture.
