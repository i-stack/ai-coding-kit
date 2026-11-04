<!-- last-verified: 2026-11 -->
# StoreKit / In-App Purchase Engineering Specification

> This is an English mirror of the authoritative Chinese `references/storekit_iap.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with StoreKit 2 (iOS 15+), StoreKit 1 (legacy), IAP products, subscriptions, receipt validation, or promotional offers.
- iOS 15+: prefer StoreKit 2's `Product` / `Transaction` / `Transaction.updates` API; fall back to StoreKit 1 (`SKPaymentQueue` system) when iOS 14 support is needed.
- Default output: "Product Fetch → Purchase Flow → Receipt Validation → Restore & Sync → Subscription Management" five sections.

## StoreKit 2 (iOS 15+ Recommended)
- Product loading: `Product.products(for:)` asynchronously returns `[Product]`; handle network failures and empty results (user has no purchase permission or region unavailable).
- Purchase: `product.purchase()` returns `Product.PurchaseResult`; `.success(.verified(transaction))` means purchase succeeded and verified; `.success(.unverified(_,_))` means purchase exists but signature verification failed (requires manual handling).
- Transaction listening: `Transaction.updates` is an `AsyncSequence` that listens for new transactions throughout the App lifecycle (including cross-device sync and subscription renewals); MUST start listening at App launch and keep running.
- Entitlement restore: iterate `Transaction.currentEntitlements` and accept only `.verified` results. Consumable catch-up also inspects `Transaction.unfinished`. Servers may verify `Transaction` / `AppTransaction` JWS and sync state with App Store Server API plus Server Notifications V2.
- `AppStore.sync()` force-refreshes transactions and subscription status, returns `Void`, and may prompt App Store account authentication. Call it only when the user explicitly taps Restore Purchases (or equivalent). Everyday launch should read `currentEntitlements` / `all` / `unfinished`.
- Call `transaction.finish()` after entitlements are successfully granted. Unfinished transactions MUST be processed idempotently to avoid double grants or permanent hangs.

## StoreKit 1 (iOS 14 and Below Compatibility)
- Use `SKProductsRequest` to fetch product information (delegate pattern).
- Use `SKPaymentQueue.default().add(payment)` to initiate purchase; monitor transaction state changes via `SKPaymentTransactionObserver`.
- Receipt validation: get receipt file via `Bundle.main.appStoreReceiptURL`, base64 encode, and send to server for validation.
- Important: Start monitoring `SKPaymentQueue` in `application(_:didFinishLaunchingWithOptions:)`; forgetting to add the observer causes purchase callbacks to be lost.

## Receipt Validation Dual Path
| Path | Use Case | Advantages | Risks |
|------|---------|------|------|
| On-device StoreKit verification | Low-risk or offline-recoverable non-consumable entitlements | StoreKit 2 verifies signatures automatically; low latency | Server cannot do cross-device risk control and audit from client state alone |
| Server JWS / App Store Server API | Consumables, subscriptions, sensitive entitlements, cross-platform accounts | Centralized idempotency, revocation, refund, and subscription-state sync | Adds network and ops cost; must handle timeouts and notification replay |

Server-side validation priority: legacy receipt validation should only fall back to sandbox when the production endpoint explicitly returns a sandbox receipt indicator; other production validation failures MUST be handled separately by network error, signature error, status code error, or server exception — do NOT swallow all errors and retry sandbox; do NOT hardcode validation URLs in code.

## Subscription Management
- Subscription status is determined via `Transaction.currentEntitlements` (StoreKit 2) or receipt parsing (StoreKit 1); do NOT rely solely on expiration time cached in `UserDefaults`.
- Promoted In-App Purchases are handled by StoreKit 1 entry points such as `paymentQueue(_:shouldAddStorePayment:for:)`; do not mix them with subscription Promotional Offers.
- Promotional Offers require a server-generated signature with the subscription key and participate in the purchase via StoreKit 2 `Product.PurchaseOption.promotionalOffer`. Offer Codes use the system redemption sheet or the corresponding StoreKit API.
- MUST provide a subscription management entry (for example `AppStore.showManageSubscriptions(in:)`, choosing the API available for the deployment target).
- Subscription entitlements must handle active subscriptions, grace period, billing retry, expiration, refunds, and revocations. Consume server notifications idempotently by notification UUID and transaction ID.

## Common Anti-Patterns
- Storing purchase state in `UserDefaults` without receipt validation — easily cracked.
- Calling `AppStore.sync()` / `restoreCompletedTransactions()` on every launch — wastes Apple server resources and is rate limited.
- Only monitoring `Transaction.updates` when App is in foreground — need to check for missed transactions when App returns from background.
- Not blocking user with loading state during purchase — user may tap multiple times causing duplicate purchases (multiple charges).
