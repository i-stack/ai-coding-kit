<!-- last-verified: 2026-06 -->
# Networking Patterns

> This is an English mirror of the authoritative Chinese `references/networking_patterns.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- Request Chain
- Pagination Patterns
- Retry Patterns
- Caching Patterns
- Auth Refresh Patterns
- Upload/Download Patterns
- Idempotency & Deduplication
- Error Layering
- Common Anti-Patterns

## Usage Rules
- When involving pagination, caching, retry, auth, upload/download, or request deduplication, MUST use the patterns defined in this file.
- Do NOT reduce networking issues to "send request and parse JSON".
- Every networking pattern MUST explain boundaries, failure strategies, and verification methods.

## Request Chain
Complete chain and responsibility definitions see [architecture_and_network.md](architecture_and_network.md) "Basic Structure". This file focuses on specific networking patterns (pagination / retry / caching / auth refresh / upload-download / idempotency deduplication); does not repeat the chain skeleton.

## Pagination Patterns
### Page-based
For:
- APIs with explicit page numbers and page sizes

Requirements:
- State explicitly stores current page, whether there's a next page, and whether pagination is in progress.
- Initial load, pull-to-refresh, and load-more are three separate paths to model.

### Cursor-based
For:
- Streaming lists, timelines, cursor-based APIs

Requirements:
- Explicitly store `nextCursor`.
- Do NOT confuse empty cursor with first page.

### Unified Pagination Requirements
- Do NOT re-request the next page.
- Do NOT let stale pagination results overwrite fresh results.
- MUST verify empty page, last page, and repeated pagination trigger paths.

## Retry Patterns
- Only idempotent requests may have automatic retry.
- MUST define max retry count, backoff strategy, and termination conditions.
- Network instability and business failures MUST be distinguished; business failures MUST NOT be silently retried.

Suitable for retry:
- Fetching configuration
- Loading lists
- Querying details

Not suitable for retry:
- Placing orders
- Payments
- Form submissions
- Write operations without idempotency guarantees

## Caching Patterns
### Display Cache
- For first-screen speedup and weak network fallback.

### Business Cache
- For reducing repeated requests and controlling read costs.

### Offline Cache
- For offline-readable or delayed sync scenarios.

Unified requirements:
- MUST define cache keys.
- MUST define invalidation conditions.
- MUST define write timing and cleanup strategy.
- ViewModel MUST NOT directly perceive cache implementation details.

## Auth Refresh Patterns
- Token refresh MUST be serialized.
- When concurrent requests hit an expired token, do NOT trigger multiple simultaneous refreshes.
- Refresh failure MUST have a clear exit strategy: re-login, degrade, read-only, prompt.
- Refresh logic MUST NOT be scattered across business Services.

## Upload/Download Patterns
- Upload/download MUST have state modeling: waiting, in-progress, success, failure, cancelled.
- Large file tasks MUST support cancel, retry, and progress reporting.
- Background upload/download MUST clarify system constraints and recovery strategy.
- File paths, temporary files, and disk usage MUST be included in lifecycle governance.

## Idempotency & Deduplication
- All write operations MUST first assess idempotency requirements.
- When the same request is triggered repeatedly in a short time, MUST define deduplication or merge strategy.
- Submit-type operations MUST prevent duplicate submission from user repeated taps and network jitter.

## Error Layering
Error layering, per-layer ownership, and UI-facing mapping rules — complete definition see [domain_modeling.md](domain_modeling.md) "ErrorModel Modeling Rules".

Networking layer (APIClient) responsibility: capture transport errors / status code errors / decoding errors, convert to `ErrorModel` and throw upward; do NOT directly expose `NSError` or HTTP codes to Repository and above.

## Common Anti-Patterns
- Directly constructing requests and parsing DTOs in ViewModel
- Unconditional automatic retry
- Cache without invalidation strategy
- Token refresh concurrency out of control
- Upload/download without cancel and recovery design

> The universal `NetworkManager` anti-pattern (with identification criteria / risks / fix) see [anti_patterns.md](anti_patterns.md) §1 "Universal Manager".
