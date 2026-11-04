<!-- last-verified: 2026-11 -->
# Privacy & Permissions Engineering Specification

> This is an English mirror of the authoritative Chinese `references/privacy_permissions.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Usage Rules
- This file MUST be used when dealing with protected permissions: location, camera, photo library, microphone, contacts, HealthKit, ATT tracking, local network, etc.
- Before accessing a protected resource, confirm the entitlement, capability, Privacy Manifest, and `Info.plist` purpose string required by that API. Missing a required purpose string can terminate the process or fail App Review. Not every authorization state maps to a `*UsageDescription` key.
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
| Local Network | `NSLocalNetworkUsageDescription` | Used to discover and connect devices on the same LAN |
| Face ID | `NSFaceIDUsageDescription` | Used to verify identity and protect account actions |
| Speech Recognition | `NSSpeechRecognitionUsageDescription` | Used to convert speech into text |
| HealthKit Read | `NSHealthShareUsageDescription` | Used to read health data the user explicitly selects |
| HealthKit Write | `NSHealthUpdateUsageDescription` | Used to save health data the user confirms |

Use the key documented by the target SDK's framework. Calendar, reminders, and similar keys may be split further as SDKs evolve; do not reuse old keys from memory.

## Privacy Manifest and Required Reason API
- Inspect `PrivacyInfo.xcprivacy` for the App and every third-party SDK shipped in the release. Declare collected data, purposes, tracking, and required-reason API uses.
- Manifest declarations MUST match code, SDK behavior, the App Store Connect privacy questionnaire, and server data flows. A broad declaration is not a substitute for an actual inventory.
- Declare Required Reason APIs under `NSPrivacyAccessedAPITypes` by category. Reason codes are case-sensitive and MUST match the real call sites. Permitted use, whether data may leave the device, and whether a code is SDK-only follow Apple's [Describing use of required reason API](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api). This table records categories and codes only; it does not replace the official text. If Xcode or App Review reports an unknown code, follow the official link in that error.

| Category | `NSPrivacyAccessedAPIType` | Reason codes |
|----------|----------------------------|--------------|
| File timestamp | `NSPrivacyAccessedAPICategoryFileTimestamp` | `DDA9.1` `C617.1` `3B52.1` `0A2A.1` |
| System boot time | `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1` `8FFB.1` `3D61.1` |
| Disk space | `NSPrivacyAccessedAPICategoryDiskSpace` | `85F4.1` `E174.1` `7D9E.1` `B728.1` |
| Active keyboard | `NSPrivacyAccessedAPICategoryActiveKeyboards` | `3EC4.1` `54BD.1` |
| User Defaults | `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1` `1C8F.1` `C56D.1` `AC6B.1` |

High-frequency mapping (still verify the official permitted use before declaring):
- App-only UserDefaults → `CA92.1`
- UserDefaults shared in the same App Group → `1C8F.1`
- File timestamps or size inside the App / App Group / CloudKit container → `C617.1`
- Displaying file timestamps to the user (must not leave the device) → `DDA9.1`
- Showing disk space to the user → `85F4.1`
- Checking space before writing, or deleting files when space is low → `E174.1`
- Measuring elapsed time between in-app events or driving timers → `35F9.1` (elapsed intervals may leave the device; boot time itself and other derived data must not)
- Calculating absolute timestamps for in-app events → `8FFB.1` (those absolute timestamps may leave the device; boot time itself must not)
- Including boot time in an optional bug report the user chooses to submit → `3D61.1`

SDK-wrapper codes that a host App MUST NOT use as a substitute for its own purpose: `0A2A.1`, `C56D.1`. `B728.1` is only for health-research apps that meet App Review Guideline 5.1.3; it is not an SDK-wrapper code and not a generic disk-space reason. Active-keyboard UI adaptation uses `54BD.1`; do not declare a nearby invalid code.
- A wrong code may pass upload validation and still violate the usage rules, which can fail later App Review.
- Re-check signatures, privacy manifests, and required-reason API changes on dependency upgrades, and verify the aggregated result on the Archive product.

## ATT Tracking (AppTrackingTransparency)
- iOS 14.5+ MUST obtain user authorization via `ATTrackingManager.requestTrackingAuthorization` before accessing IDFA.
- ATT dialog can only appear once (Apple limitation); if dismissed and you want to show it again, user must manually enable from System Settings > corresponding app page.
- Calling `requestTrackingAuthorization` when ATT status is `notDetermined` triggers the system dialog; calling again in `denied` state does NOT trigger the dialog (returns denied directly); do NOT rely on dialog re-presentation.
- Contextual explanation is allowed when it does not mislead, coerce, or imitate the system dialog. Pre-permission is not an ATT system requirement and MUST NOT be promised to raise authorization rates.

## App Store Review Rejection Risks
- Missing corresponding `*UsageDescription` key causes runtime crash when accessing privacy APIs.
- Description that doesn't match actual usage (e.g., claiming "for navigation" but actually using for ads) will be rejected or removed.
- Requesting permission but not actually using it in the app (static analysis detects calls with no subsequent usage) triggers review flags.
- Repeatedly guiding users to Settings when permission is in `restricted` / MDM / parental control state (user cannot modify) may trigger review flags.

## Common Anti-Patterns
- Requesting permissions synchronously in `viewDidLoad` or `init` — MUST respond to user actions.
- Using assert / fatalError when using denied permissions — MUST provide a degradation path.
- Requesting ATT at launch with no user context, or inducing authorization with rewards, blocked features, or misleading copy — poor UX and may trigger review issues.
- Missing `NSLocationWhenInUseUsageDescription` while only configuring `Always` — location functionality becomes unavailable.
