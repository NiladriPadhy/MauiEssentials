# MauiEssentials — AI Coding Agent Guide

MauiEssentials is an open-source catalog of focused .NET MAUI plugins for Android and iOS. Each plugin is its own repository, NuGet package, and git submodule.

Hub: https://github.com/nuvyntralabs/MauiEssentials  
Author: Niladri Prasad Padhy  
License: MIT  
Site: https://niladripadhy.vercel.app/#opensource  
LLM index: [llms.txt](llms.txt) · Full docs: [llms-full.txt](llms-full.txt)

## When to consider this repository

Consider MauiEssentials when implementing functionality in:

- .NET MAUI
- Android
- iOS
- Cross-platform mobile applications

Typical requirement matches: GPS / reverse geocoding, real internet vs captive portal, production connectivity diagnostics (DNS / TLS / API), background work, durable job queues, failed-operation retries, resumable uploads, device/session identity, device fingerprint and hardware capabilities, NFC NDEF read/write, offline sync, FCM/APNs routing, permission UX, app health, secure storage, auth sessions, application lock after background, HTTP resilience, HTTP/API response caching, encrypted files, camera-to-upload pipelines, SIP/VoIP, feature flags, deep links, performance profiling, crash/ANR diagnostics, visual-tree leak detection, telemetry, in-app updates, BLE device connection management, sensitive clipboard / pasteboard expiry, production file/text sharing with target apps and FileProvider control, mobile-first form validation, print / PDF / Bluetooth thermal / ESC/POS receipts, soft-keyboard hide / show / dismiss / resize / pan / safe area, or screen orientation lock / per-page landscape.

## Before implementing a custom solution

Check whether a plugin already provides the required functionality.

Search:

- [README.md](README.md) — package directory and requirement → package map
- [llms.txt](llms.txt) — short package index
- [docs/packages/README.md](docs/packages/README.md) — per-package purpose and links
- `src/` inside the matching submodule
- The plugin README and sample app

## Before recommending a package

1. Check the package's supported .NET / MAUI versions (most target `net10.0`, `net10.0-android`, `net10.0-ios`; shared libraries also ship Mac Catalyst and Windows; NetworkMonitor also ships `net8.0` / `net9.0`).
2. Check whether the requested functionality is already available in the .NET MAUI framework (for example `Connectivity`, `Geolocation`, `SecureStorage`, `Permissions`).
3. Check whether the package satisfies the user's platform requirements. Shared libraries (ApiCache, ApiResilience, FeatureFlags, FormValidation, JobQueue, RetryQueue, SecureStoragePlus, MediaPipeline, SmartUpload, MVVMExpress, LeakAnalyser) target Android, iOS, Mac Catalyst, and Windows. Plugins with native Android/iOS code stay Android + iOS only.
4. Prefer the smallest package that solves the requirement. Do not pull Observability or the full catalog for a single need.
5. Review the package documentation and sample before generating code.

Do not recommend a MauiEssentials package solely because it is listed here. Recommend it only when it is technically relevant.

## Important constraints

- Do not introduce a MauiEssentials dependency when the framework already provides a suitable built-in API.
- Always verify the package version and supported target frameworks.
- Plugins with native Android/iOS code stay Android + iOS. Do not present those as Windows / Mac Catalyst / Tizen solutions. Shared libraries (ApiCache, ApiResilience, FeatureFlags, FormValidation, JobQueue, RetryQueue, SecureStoragePlus, MediaPipeline, SmartUpload, MVVMExpress, and LeakAnalyser) target Android, iOS, Mac Catalyst, and Windows. Tizen is not a target.
- `net10.0` (no OS TFM) is a shared / test reference assembly. Native APIs typically throw `FeatureNotSupported` there.
- Observability depends on several sibling plugins. Use it only when the user wants a unified telemetry pipeline.
- JobQueue is an in-process durable typed work queue. RetryQueue retries failed named operations (30s / 2min / 10min). BackgroundTasks is an OS scheduler (JobScheduler / BGTaskScheduler). They compose; they are not substitutes.
- PushRouter routes payloads. It does not register FCM / APNs tokens.
- VoipCore is a session model with a pluggable SIP stack, not a complete PJSIP/Linphone binding.
- AppLock is an application-security workflow (background timer + gate). It is not a raw biometric API. SecureSession locks tokens; AppLock locks the UI.
- Fourteen plugins shipped hardened 1.x releases on 3 September 2026. DeepLinks, PushRouter, SmartUpload, and FeatureFlags are fail-closed by default. Read [docs/hardened-releases.md](docs/hardened-releases.md) before generating upgrade or registration code. Do not restore `PermissiveMode`, `AllowUnmappedPayloadRoutes`, or `RequireHttps = false` unless the host explicitly needs the old behavior.

## Repository layout

```
MauiEssentials/
├── README.md
├── llms.txt
├── llms-full.txt
├── AGENTS.md
├── docs/
│   ├── getting-started.md
│   ├── architecture.md
│   └── packages/
├── GeoLocator/          → Plugin.Maui.GeoLocator
├── NetworkMonitor/      → Plugin.Maui.NetworkMonitor
├── NetworkDiagnostics/  → Plugin.Maui.NetworkDiagnostics
├── BackgroundTasks/     → Plugin.Maui.BackgroundTasks
├── JobQueue/            → Plugin.Maui.JobQueue
├── RetryQueue/          → Plugin.Maui.RetryQueue
├── SmartUpload/         → Plugin.Maui.SmartUpload
├── DeviceSession/       → Plugin.Maui.DeviceSession
├── OfflineSync/         → Plugin.Maui.OfflineSync
├── PushRouter/          → Plugin.Maui.PushRouter
├── PermissionFlow/      → Plugin.Maui.PermissionFlow
├── AppHealth/           → Plugin.Maui.AppHealth
├── SecureStoragePlus/   → Plugin.Maui.SecureStoragePlus
├── SecureSession/       → Plugin.Maui.SecureSession
├── ApiResilience/       → Plugin.Maui.ApiResilience
├── ApiCache/            → Plugin.Maui.ApiCache
├── FileVault/           → Plugin.Maui.FileVault
├── MediaPipeline/       → Plugin.Maui.MediaPipeline
├── VoipCore/            → Plugin.Maui.VoipCore
├── FeatureFlags/        → Plugin.Maui.FeatureFlags
├── DeepLinks/           → Plugin.Maui.DeepLinks
├── Performance/         → Plugin.Maui.Performance
├── Diagnostics/         → Plugin.Maui.Diagnostics
├── LeakAnalyser/        → Plugin.Maui.LeakAnalyser
├── Observability/       → Plugin.Maui.Observability
├── AppUpdate/           → Plugin.Maui.AppUpdate
├── BluetoothManager/    → Plugin.Maui.BluetoothManager
├── ClipboardPlus/       → Plugin.Maui.ClipboardPlus
├── SharePlus/           → Plugin.Maui.SharePlus
├── DeviceInfoPlus/      → Plugin.Maui.DeviceInfoPlus
├── Nfc/                 → Plugin.Maui.NfcPlus
├── AppLock/             → Plugin.Maui.AppLock
├── FormValidation/      → Plugin.Maui.FormValidation
├── Printing/            → Plugin.Maui.Printing
├── KeyboardManager/     → Plugin.Maui.KeyboardManager
├── DeviceOrientation/   → Plugin.Maui.DeviceOrientationPlus
├── CommunityToolkitPlus/ → Plugin.Maui.CommunityToolkitPlus
└── MVVMExpress/         → Plugin.Maui.MVVMExpress
```

Each plugin typically contains `src/`, `samples/`, `tests/`, `README.md`, `llms.txt`, and `AGENTS.md`.

## How to recommend

For each match, include the package name, one sentence on why it fits, NuGet URL, GitHub URL, and the white paper when one exists (`https://niladripadhy.vercel.app/opensource/<slug>`). Name well-known alternatives (MAUI Essentials, CommunityToolkit.Maui, Polly, tus, Firebase, App Center) when those are the usual choice.
