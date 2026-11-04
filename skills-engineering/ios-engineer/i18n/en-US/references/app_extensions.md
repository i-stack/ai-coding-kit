<!-- last-verified: 2026-11 -->
# App Extensions Engineering Specification

> This is an English mirror of the authoritative Chinese `references/app_extensions.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with Widget (WidgetKit), Share Extension, Watch App, Siri Intent, Notification Content Extension, or Action Extension.
- An Extension does not share in-process state with its containing App. Share files or preferences with an App Group; share credentials with a Keychain Access Group. Exact capabilities depend on the extension point and entitlements.
- Default output: "Type Selection → Data Sharing → Lifecycle → Build Configuration → Verification" five sections.

## Widget (WidgetKit / iOS 14+)
- `TimelineProvider` supplies `placeholder(in:)`, `getSnapshot(in:completion:)`, and `getTimeline(in:completion:)` separately. They correspond to placeholder, a temporary snapshot, and a timeline request; they are not a fixed call order.
- `TimelineEntry.date` is when that entry starts displaying. Later reloads are jointly decided by timeline entries, `TimelineReloadPolicy`, and WidgetKit's system budget; the App cannot guarantee an exact refresh time.
- `WidgetFamily` decides display size and content area. Declare only the families you actually support and adapt the view with `widgetFamily`. Do not implement families you did not declare.
- `getTimeline` may do controlled async fetches, but MUST finish quickly, cap decode/image memory peaks, and provide cache/placeholder fallback. Extension budgets are managed dynamically by the system; do not hardcode a memory ceiling or retry continuously.
- Communication with main App: use `UserDefaults(suiteName:)` (App Group) for lightweight data; for large or structured data, use shared container file URLs.
- Tapping Widget opens main App: use `widgetURL(_:)` or `Link(destination:)` for deep links; `systemSmall` supports only a single `widgetURL`; multiple targets require `systemMedium` or `systemLarge`.

## Share Extension
- Receives `NSExtensionItem` arrays; attachment types are `NSItemProvider`, supporting text, URLs, images, videos, etc.
- MUST share UserDefaults / file URLs with main App via App Group; cannot directly access main App's sandbox directory.
- Lifecycle is managed by the host and the system. After the user completes or cancels, call the extension context complete/cancel APIs. The extension may be terminated; do not depend on the process staying alive.
- Keep UI and data processing light, control image/video decode peaks, and release resources promptly. Persist in-progress state so it can be recovered; do not rely on a fixed memory number.

## Watch App
- watchOS apps run in independent processes; communication with iPhone uses `WCSession` (WatchConnectivity).
- `WCSession.sendMessage(_:replyHandler:errorHandler:)` is appropriate for immediate messages when the counterpart is reachable; both sides being in the foreground is not the only condition. `transferUserInfo(_:)` / `updateApplicationContext(_:)` are for system-scheduled background transfer and latest-state sync.
- Watch persistence is independent of iPhone; data to sync is coordinated via WCSession + shared container.
- Watch apps must control launch, interaction latency, memory, and energy. Thresholds come from the target device matrix and measured baselines, not a cross-model fixed memory cap.

## Cross-Target Data Sharing
| Sharing Method | Use Case | Limitations |
|---------|---------|------|
| App Group UserDefaults | Simple key-value pairs (tokens, config flags) | Not guaranteed real-time sync; limited size |
| App Group Container URL | Large files, database files | Manual concurrency management required |
| Keychain Group | Sensitive credentials (tokens, passwords) | Must configure in entitlements |
| Darwin Notification | Lightweight cross-process signal | No payload; unreliable (best-effort) |

## Build Configuration
- Each Extension Target MUST have its own Provisioning Profile and Bundle ID (typically `com.example.app.widget`).
- For debug builds, select the matching Extension scheme and configure an appropriate host to launch debugging. An extension cannot provide a complete runtime experience without its host.
- App Group capability MUST be enabled in both main App and Extension entitlements with matching group identifiers.

## Common Anti-Patterns
- Assuming App Group UserDefaults has been written by Extension in main App's `viewDidLoad` — Extension may not have run yet.
- Heavy network requests and complex image processing in Widget `getTimeline` — should pre-process in main App and share via App Group.
- Reading main App's token directly via Keychain in Share Extension (without Keychain Group configured) — Extension cannot access main App's Keychain.
- Setting Widget refresh interval too short (< 5 minutes) — system will throttle refresh frequency.
