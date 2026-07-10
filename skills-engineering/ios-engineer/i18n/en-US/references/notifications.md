<!-- last-verified: 2026-07 -->
# Push Notifications Engineering Specification

> This is an English mirror of the authoritative Chinese `references/notifications.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with remote push (APNs), local notifications (UNUserNotificationCenter), or notification extensions.
- Push design MUST separate three paths: notification arrival, user tap, and foreground presentation; do NOT conflate them.
- Default output: "Registration Chain → Payload Structure → Route Navigation → Extension Handling" four sections.

## Notification Registration Chain
- `UNUserNotificationCenter.requestAuthorization(options:)` MUST provide the minimal combination of `.alert` / `.badge` / `.sound`; provisional authorization is for soft opt-in and cannot replace formal authorization.
- Registration failure MUST NOT be silent: log the error code and provide a user-visible degradation path (e.g., Settings page guidance).
- Main Target registration token is obtained via `application(_:didRegisterForRemoteNotificationsWithDeviceToken:)`; token MUST be re-reported to server when changed.
- During cold start, if `registerForRemoteNotifications()` is not called in `didFinishLaunching`, the token may be expired and unable to refresh.

## Payload Structure
- APNs payload top-level `aps` dictionary is system-reserved; business data goes under custom keys, NOT at the same level as `aps` (to avoid future field conflicts).
- `mutable-content: 1` + Notification Service Extension allows rich media attachment processing (images / videos / audio), but processing timeout is ~30 seconds; `contentHandler` MUST be called promptly in `didReceive(_:withContentHandler:)`.
- Silent push (`content-available: 1`) does NOT guarantee delivery ordering; do NOT rely on its ordering for business logic.

## Route Navigation
- Notification tap navigation should NOT hardcode route mapping in `AppDelegate` / `SceneDelegate`; instead, use `route` / `deepLink` fields in the notification payload to drive navigation.
- When user taps a historical notification, the target content may have been removed; route handling MUST defend against invalid deep links.
- When notification arrives while App is in foreground, banner is NOT shown by default; need `UNUserNotificationCenterDelegate.presentationOptions` to return `.banner` / `.list` / `.sound` / `.badge`.

## Notification Extensions
- Notification Service Extension runs in an independent process; shared files or `UserDefaults(suiteName:)` require App Group; accessing shared Keychain items requires both main App and Extension to configure the same Keychain Access Group — do NOT assume App Group is sufficient for Keychain sharing.
- Extension memory is limited (~24MB iOS 15+); when handling large images or videos, prefer passing URLs over raw data.
- Notification Content Extension is for customizing the expanded notification UI; its lifecycle is managed by the system; do NOT initiate long-running network requests within it.

## Common Anti-Patterns
- In `didFinishLaunching`, assuming user came from notification tap just because `launchOptions[.remoteNotification] != nil` — `launchOptions` presence doesn't mean user saw the notification content; also check if the corresponding payload is complete.
- Coupling token reporting with push strategy — token is just an address; push strategy (timing / frequency control / segmentation) should be managed independently by the server.
- Using `shared` URLSession for large file downloads in Extension — Extension can be terminated by the system at any time; downloads should be minimized in Extension; large files should be downloaded by main App in background.

## Verification Checklist
- [ ] Notification registration success/failure both have logging and degradation paths.
- [ ] Server reflects token changes within 5 minutes.
- [ ] Rich media push (mutable-content) completes processing within 30 seconds in Extension.
- [ ] Notification tap routing handles invalid/expired deep links.
- [ ] Foreground notification presentation behavior matches expectations (banner / no banner).
- [ ] Extension crash rate < 0.1%.
