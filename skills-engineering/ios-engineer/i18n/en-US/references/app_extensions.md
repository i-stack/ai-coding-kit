<!-- last-verified: 2026-07 -->
# App Extensions Engineering Specification

> This is an English mirror of the authoritative Chinese `references/app_extensions.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with Widget (WidgetKit), Share Extension, Watch App, Siri Intent, Notification Content Extension, or Action Extension.
- Extensions run in independent processes and do NOT share memory space with the main App; data sharing MUST go through App Group or Keychain Group.
- Default output: "Type Selection → Data Sharing → Lifecycle → Build Configuration → Verification" five sections.

## Widget (WidgetKit / iOS 14+)
- Use `TimelineProvider` to drive refresh: `snapshot` (preview) → `timeline` (real data) → `placeholder` (placeholder).
- The `date` field of `TimelineEntry` determines when to display and when to refresh; after the `Timeline` `policy` expiration, the system requests new data.
- `WidgetFamily` (systemSmall / systemMedium / systemLarge / accessory*) determines display size and content area; each family MUST have a corresponding view.
- Network requests are made within `getTimeline` and MUST complete within the Extension's memory budget (~30MB iOS 17+); continuous retries are NOT allowed.
- Communication with main App: use `UserDefaults(suiteName:)` (App Group) for lightweight data; for large or structured data, use shared container file URLs.
- Tapping Widget opens main App: use `widgetURL(_:)` or `Link(destination:)` for deep links; `systemSmall` supports only a single `widgetURL`; multiple targets require `systemMedium` or `systemLarge`.

## Share Extension
- Receives `NSExtensionItem` arrays; attachment types are `NSItemProvider`, supporting text, URLs, images, videos, etc.
- MUST share UserDefaults / file URLs with main App via App Group; cannot directly access main App's sandbox directory.
- Lifecycle: user taps "Share" → Extension view opens → user completes action (post / save) → Extension closes; not Suspended during this period.
- UI must not be too heavy — Extension memory limit is strict (~120MB), and user cannot exit before completing the action.

## Watch App
- watchOS apps run in independent processes; communication with iPhone uses `WCSession` (WatchConnectivity).
- `WCSession.sendMessage(_:replyHandler:errorHandler:)` is real-time communication (only when both watch and iPhone are foreground); `transferUserInfo(_:)` / `updateApplicationContext(_:)` for background sync.
- Watch persistence is independent of iPhone; data to sync is coordinated via WCSession + shared container.
- Watch app performance requirements are strict: frontend interaction latency < 200ms, memory limit is very small (~60-120MB depending on model).

## Cross-Target Data Sharing
| Sharing Method | Use Case | Limitations |
|---------|---------|------|
| App Group UserDefaults | Simple key-value pairs (tokens, config flags) | Not guaranteed real-time sync; limited size |
| App Group Container URL | Large files, database files | Manual concurrency management required |
| Keychain Group | Sensitive credentials (tokens, passwords) | Must configure in entitlements |
| Darwin Notification | Lightweight cross-process signal | No payload; unreliable (best-effort) |

## Build Configuration
- Each Extension Target MUST have its own Provisioning Profile and Bundle ID (typically `com.example.app.widget`).
- Debug builds must select the correct Scheme (main App vs Extension); Extensions cannot run independently.
- App Group capability MUST be enabled in both main App and Extension entitlements with matching group identifiers.

## Common Anti-Patterns
- Assuming App Group UserDefaults has been written by Extension in main App's `viewDidLoad` — Extension may not have run yet.
- Heavy network requests and complex image processing in Widget `getTimeline` — should pre-process in main App and share via App Group.
- Reading main App's token directly via Keychain in Share Extension (without Keychain Group configured) — Extension cannot access main App's Keychain.
- Setting Widget refresh interval too short (< 5 minutes) — system will throttle refresh frequency.
