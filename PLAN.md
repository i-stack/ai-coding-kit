# Plan: Login Rate Limiting With Redis

## Goal
Reduce credential-stuffing and brute-force login risk by throttling repeated failed login attempts without creating an easy account-lockout denial-of-service path.

## Constraints & assumptions
- The web service may run on multiple application instances, so process memory is not an acceptable shared counter.
- Redis is available as shared, low-latency storage for rate-limit state.
- The application is deployed behind a trusted reverse proxy that can provide a canonical client IP; raw user-controlled forwarding headers are not trusted.
- Usernames are case-insensitive for login and can be normalized before key construction.
- A short fixed-window approximation is acceptable for this first version; exact sliding-window precision is out of scope.

## Approach
Normalize the submitted username before creating any Redis keys. Resolve the client IP only from the trusted proxy chain. For each failed login, update a Redis key scoped to the normalized username and canonical IP pair, for example `loginfail:v1:u:{hash(username)}:ip:{ip}`. Use a Redis Lua script to atomically increment the failure counter and set the counter TTL on first creation, avoiding the `INCR` then `EXPIRE` crash window.

When the pair exceeds 5 failed attempts in a 15-minute window, create a separate lock key for that username/IP pair with a 15-minute TTL and clear the counter key so the next window starts cleanly. During the lock period, reject login attempts before password verification and return `Retry-After` based on the remaining lock-key TTL. On successful authentication, delete the pair counter for the normalized username and canonical IP. Emit structured security logs and metrics whenever a pair is locked.

## Key decisions & tradeoffs
- Pair-scoped key instead of username-only lock: this reduces targeted account-lockout DoS risk; it is weaker against highly distributed attacks and can be extended later with CAPTCHA or adaptive risk scoring.
- Lua script instead of separate `INCR` and `EXPIRE`: this keeps the counter update and TTL assignment atomic; it adds a small Redis scripting dependency but avoids immortal counters.
- Fixed window instead of sliding window: fixed windows are simpler and adequate for the initial brute-force control; they permit boundary bursts, which is accepted for this version.
- Hash the normalized username in Redis keys and logs: this avoids storing raw identifiers in infrastructure keys; it slightly complicates manual debugging.
- Fail open on Redis errors with alerting: this preserves login availability during Redis incidents; it temporarily weakens brute-force protection and must be observable.

## Validation plan
- Unit tests for username normalization, trusted client-IP extraction, key construction, and `Retry-After` using remaining TTL rather than a hard-coded duration.
- Redis integration test for the Lua script: first failure sets TTL, concurrent failures do not drop counts, and no key remains without TTL after the script path.
- Behavioral tests: attempts 1-5 are allowed to reach password verification, attempt 6 for the same username/IP pair is rejected, a different IP is not automatically locked, and successful login clears the pair counter.
- Expiry tests: lock TTL expires automatically, the cleared counter does not immediately relock the user, and `Retry-After` decreases over time.
- Observability checks: lock events emit structured logs and increment metrics with non-raw username identifiers.

## Risks / non-blocking open questions
- Distributed low-and-slow attacks across many IPs may bypass pair-scoped limits; a later layer can add username-level CAPTCHA or adaptive risk scoring without changing this first control.
- NAT-heavy networks may see shared-IP friction for the same username/IP pair, though pair scoping limits the blast radius compared with IP-only throttling.
- Redis fail-open behavior weakens protection during outages; alerting is required so operations can respond.

## Out of scope
- CAPTCHA, MFA step-up, and risk-based authentication policy.
- Global IP reputation or distributed abuse intelligence feeds.
- Account recovery, help-desk unlock flows, or manual administrative override tooling.
