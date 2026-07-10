<!-- last-verified: 2026-07 -->
# Privacy & Permissions Engineering Specification

> This is an English mirror of the authoritative Chinese `references/privacy_permissions.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with protected permissions: location, camera, photo library, microphone, contacts, HealthKit, ATT tracking, local network, etc.
- Each permission MUST have a corresponding `Info.plist` description string (`*UsageDescription` key); missing keys will cause App Store rejection or runtime crashes.
- Default output: "Permission Type → Request Timing → Denial Degradation → plist String → Review Risk" five sections.

## Permission Request Best Practices
- Permission requests MUST occur within a clear user action context (e.g., requesting camera when user taps "Take Photo"); batch permission prompts at App launch are prohibited.
- Post-denial degradation path MUST be visible: disabled buttons, guidance text, entry point to System Settings.
- iOS permission requests only trigger the system dialog in `notDetermined` state; `denied` / `restricted` should NOT re-trigger the system dialog — MUST follow visible degradation and Settings page guidance; photo library `limited` needs a separate functional path for limited access.
- Location permissions split into `When In Use` and `Always`: request `When In Use` first, then `Always` after approval; requesting `Always` directly is very likely to be rejected by users.

## Required Baseline (Info.plist)
| Permission Type | plist Key | Example Description |
|---------|-----------|------------|
| Location Always | `NSLocationAlwaysAndWhenInUseUsageDescription` | Used to continuously record your route |
| Location WhenInUse | `NSLocationWhenInUseUsageDescription` | Used to show your current location on the map |
| Camera | `NSCameraUsageDescription` | Used for photo capture / QR scanning |
| Photo Library Read | `NSPhotoLibraryUsageDescription` | Used to select photos for upload |
| Photo Library Add | `NSPhotoLibraryAddUsageDescription` | Used to save images to photo library |
| Microphone | `NSMicrophoneUsageDescription` | Used for voice message recording |
| Contacts | `NSContactsUsageDescription` | Used to invite friends |
| ATT Tracking | `NSUserTrackingUsageDescription` | Used to provide personalized ads |
| Bluetooth | `NSBluetoothAlwaysUsageDescription` | Used to connect smart devices |

## ATT Tracking (AppTrackingTransparency)
- iOS 14.5+ MUST obtain user authorization via `ATTrackingManager.requestTrackingAuthorization` before accessing IDFA.
- ATT dialog can only appear once (Apple limitation); if dismissed and you want to show it again, user must manually enable from System Settings > corresponding app page.
- Calling `requestTrackingAuthorization` when ATT status is `notDetermined` triggers the system dialog; calling again in `denied` state does NOT trigger the dialog (returns denied directly); do NOT rely on dialog re-presentation.
- Recommendation: Show a pre-permission explanation dialog before the ATT dialog, explaining why tracking is needed, to improve authorization rate.

## App Store Review Rejection Risks
- Missing corresponding `*UsageDescription` key causes runtime crash when accessing privacy APIs.
- Description that doesn't match actual usage (e.g., claiming "for navigation" but actually using for ads) will be rejected or removed.
- Requesting permission but not actually using it in the app (static analysis detects calls with no subsequent usage) triggers review flags.
- Repeatedly guiding users to Settings when permission is in `restricted` / MDM / parental control state (user cannot modify) may trigger review flags.

## Common Anti-Patterns
- Requesting permissions synchronously in `viewDidLoad` or `init` — MUST respond to user actions.
- Using assert / fatalError when using denied permissions — MUST provide a degradation path.
- ATT dialog shown directly at launch without pre-permission explanation — may be rejected by review.
- Missing `NSLocationWhenInUseUsageDescription` while only configuring `Always` — location functionality becomes unavailable.
