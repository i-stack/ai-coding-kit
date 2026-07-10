<!-- last-verified: 2026-07 -->
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
- Receipt validation: StoreKit 2 uses `Transaction.currentEntitlements` to get verified transactions; server-side validation can optionally use `AppTransaction` / `Transaction` JWS signatures (verified online via Apple's verification endpoint).
- Restore purchases: `AppStore.sync()` syncs cross-device transactions, returning transactions not previously completed on this device; should NOT be called on every launch — trigger on demand.

## StoreKit 1 (iOS 14 and Below Compatibility)
- Use `SKProductsRequest` to fetch product information (delegate pattern).
- Use `SKPaymentQueue.default().add(payment)` to initiate purchase; monitor transaction state changes via `SKPaymentTransactionObserver`.
- Receipt validation: get receipt file via `Bundle.main.appStoreReceiptURL`, base64 encode, and send to server for validation.
- Important: Start monitoring `SKPaymentQueue` in `application(_:didFinishLaunchingWithOptions:)`; forgetting to add the observer causes purchase callbacks to be lost.

## Receipt Validation Dual Path
| Path | Use Case | Advantages | Risks |
|------|---------|------|------|
| On-device validation | Simple check for non-consumables / auto-renewing subscriptions | Works offline, low latency | Easily bypassed on jailbroken devices |
| Server-side validation | Consumables / subscriptions / sensitive entitlements | Secure, Apple authoritative | Adds network latency; must handle validation plaintext timeout |

Server-side validation priority: legacy receipt validation should only fall back to sandbox when the production endpoint explicitly returns a sandbox receipt indicator; other production validation failures MUST be handled separately by network error, signature error, status code error, or server exception — do NOT swallow all errors and retry sandbox; do NOT hardcode validation URLs in code.

## Subscription Management
- Subscription status is determined via `Transaction.currentEntitlements` (StoreKit 2) or receipt parsing (StoreKit 1); do NOT rely solely on expiration time cached in `UserDefaults`.
- Promotional Offers: configured in App Store Connect, handled via `paymentQueue(_:shouldAddStorePayment:for:)`.
- Subscription offer codes / introductory promotions: StoreKit 2 handles via `Product.SubscriptionInfo.PromotionalOffer`.
- MUST provide a subscription management entry point (`AppStore.showManageSubscriptions(in:)` iOS 15+ or open `itms-apps://` link).

## Common Anti-Patterns
- Storing purchase state in `UserDefaults` without receipt validation — easily cracked.
- Calling `AppStore.sync()` / `restoreCompletedTransactions()` on every launch — wastes Apple server resources and is rate limited.
- Only monitoring `Transaction.updates` when App is in foreground — need to check for missed transactions when App returns from background.
- Not blocking user with loading state during purchase — user may tap multiple times causing duplicate purchases (multiple charges).
