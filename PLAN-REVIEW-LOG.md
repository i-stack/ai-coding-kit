# Plan Review Log: Login Rate Limiting With Redis

MAX_ROUNDS=5
Reviewers:
- claude 2.1.195 (Anthropic)
- gemini 0.49.0 (Google)

## Round 1 - claude

### Flaw 1 - Lock transition is not fully atomic
The plan makes the counter increment and TTL atomic, but it describes lock-key creation and counter deletion as later actions. If the lock key is written and the counter delete fails, the counter can persist and keep re-triggering lock creation.

Fix: Put increment, threshold check, lock-key creation, and counter deletion into one Redis Lua script.

### Flaw 2 - Successful auth on the threshold attempt leaves the user locked
The plan deletes only the pair counter on successful authentication. If the attempt that crosses the threshold later authenticates successfully, the lock key may remain and block the legitimate user.

Fix: On successful authentication, delete both the counter key and the lock key for that normalized username/IP pair.

### Flaw 3 - Unkeyed hash enables targeted account-lockout
The plan says to hash usernames but does not specify a keyed hash. A predictable hash scheme can leak or allow targeted manipulation of key space.

Fix: Use HMAC-SHA-256 or another keyed server-side digest for username identifiers in Redis keys and logs.

### Flaw 4 - Username normalization algorithm is undefined
The plan says usernames are normalized but does not define Unicode normalization, case folding, or trimming rules. Divergence between auth and rate-limit paths can permit bypass.

Fix: Specify and share one normalization function across auth and rate-limit code, with tests for Unicode and whitespace variants.

### Flaw 5 - `Retry-After` TTL race is not handled
Fetching a remaining TTL can return an expired-key sentinel such as `-2`. The plan does not specify how to handle this edge case.

Fix: Treat missing or expired lock-key TTL as "lock expired" and allow the request path to continue.

### Flaw 6 - Redis eviction can silently void locks
If Redis uses an eviction policy such as `allkeys-lru`, security lock keys can disappear without a connection error, bypassing the fail-open alert path.

Fix: Require a Redis namespace or instance configured for security keys with a no-eviction policy, or add explicit early-disappearance detection.

### Flaw 7 - Trusted-IP header behavior is underspecified
The plan says to resolve IP from a trusted proxy chain, but does not name the header, parsing rule, absent-header behavior, or multi-value handling.

Fix: Specify the exact trusted proxy configuration and extraction algorithm, then test absent and multi-hop header cases.

### Flaw 8 - No lock-duration escalation
The plan permits a persistent attacker to obtain a steady rate of attempts after each lock expires.

Fix: Either add escalation for repeated lock events or explicitly document the accepted steady-state attack throughput.

VERDICT: REVISE

### Orchestrator response
Accepted:
- Flaw 1: Accepted. The Redis state transition must be one script, not a script plus follow-up writes.
- Flaw 2: Accepted. Successful authentication must clear both counter and lock keys for the same pair.
- Flaw 3: Accepted with wording adjustment. The concrete risk is predictable identifiers and privacy/key-space leakage; HMAC-SHA-256 is the right plan-level requirement.
- Flaw 4: Accepted. Normalization must be exact and shared.
- Flaw 5: Accepted. `PTTL == -2` should be treated as expired, not emitted as a negative `Retry-After`.
- Flaw 6: Accepted. Redis eviction policy is a real deployment constraint for security state.
- Flaw 7: Accepted. "Trusted proxy chain" is not actionable enough for implementation.
- Flaw 8: Rejected as blocking for this first version. The plan already acknowledges low-and-slow limits as a non-blocking risk; adding escalation changes the product/security policy and can increase false positives. The plan should document the accepted throughput more explicitly instead.

Rejected:
- None of the correctness or deployment-specific issues above are rejected.

## Round 1 - gemini

Attempted reviewer command in read-only plan mode with the user-confirmed reviewer `gemini`.

Result:
- Sandbox run failed before model invocation because macOS cache lookup failed: `getconf DARWIN_USER_CACHE_DIR: Input/output error`.
- Escalated run started but produced no reviewer output and no `VERDICT` before being interrupted.
- A retry limiting MCP initialization to the connected `github` MCP also produced no reviewer output and no `VERDICT` before being interrupted.

VERDICT: MISSING

### Orchestrator response
Accepted:
- The missing Gemini verdict is a workflow failure, not an approval.

Rejected:
- Do not substitute Gemini with another reviewer without user approval, because the user explicitly chose `gemini + claude`.

## Resolution
failed

Reason: `cross-model-review` requires every selected reviewer to produce a legal `VERDICT: APPROVED` or `VERDICT: REVISE`. Claude returned `VERDICT: REVISE`; Gemini did not return a legal verdict, so this run stops rather than pretending the plan passed.

## Retry 1 - project-local raw outputs only

User correction: reviewer raw output must not be staged in `/tmp`; all raw and final artifacts should be created under the current project root.

Project-local raw outputs:
- `.plan-reviews/2026-07-06-login-rate-limit/raw/claude-round1.txt`
- `.plan-reviews/2026-07-06-login-rate-limit/raw/gemini-round1.txt`

### Retry 1 - claude
Claude completed the read-only review and wrote 5896 bytes to the project-local raw output file.

Key result:
- `VERDICT: REVISE`
- Claude observed that root `PLAN.md` is unchanged from the prior review and still does not incorporate the accepted findings.
- Claude repeated the still-unaddressed flaws: atomic Redis lock transition, clearing lock key on success, keyed username digest, exact normalization, TTL sentinel handling, Redis eviction policy, and exact trusted-IP extraction.
- Claude added new flaws: lock-key TTL should not be reset unconditionally during an active lock, Redis timeouts need a short deadline and fail-open behavior, clearing counters removes future escalation signal, and accepted steady-state attack throughput must be quantified.

### Retry 1 - gemini
Gemini was rerun in read-only plan mode with raw output redirected to `.plan-reviews/2026-07-06-login-rate-limit/raw/gemini-round1.txt`.

Result:
- Gemini again started with a Node debugger listener message on stdout.
- Gemini produced 0 bytes in the project-local raw output file.
- Gemini did not produce `VERDICT: APPROVED` or `VERDICT: REVISE` before being interrupted.

VERDICT: MISSING

### Orchestrator response
Accepted:
- The user correction is valid: `/tmp` is only acceptable for disposable scratch in ordinary command execution, but this workflow's evidence should be project-local because the skill defines project review artifacts.
- The retry proves the storage-location issue is fixed: raw reviewer outputs and final logs now live under the project root.
- The workflow still fails because Gemini did not produce a legal verdict.

Rejected:
- Do not mark the plan approved.
- Do not silently replace Gemini with Codex; the user explicitly chose `gemini + claude`.

## Retry 1 Resolution
failed

Reason: The no-`/tmp` storage correction is complete, but `cross-model-review` still cannot complete successfully with the selected reviewer pair because Gemini produced no legal verdict.
