# Getting started

MauiEssentials is a catalog of focused .NET MAUI plugins. You do not reference this repository as a single NuGet package. Install the plugin that matches the requirement.

## 1. Pick a package

Use the [requirement → package map](packages/README.md) or the tables in the [root README](../README.md).

Examples:

- Real internet vs captive portal → `Plugin.Maui.NetworkMonitor`
- Internet works but the API does not → `Plugin.Maui.NetworkDiagnostics`
- GPS + reverse geocoding → `Plugin.Maui.GeoLocator`
- Durable work that must survive process death → `Plugin.Maui.JobQueue`
- Retry a failed API call (orders, telemetry, payments) → `Plugin.Maui.RetryQueue`
- OS-scheduled refresh → `Plugin.Maui.BackgroundTasks`
- BLE printer / POS / sensor connection manager → `Plugin.Maui.BluetoothManager`
- Sensitive clipboard / OTP expiry / image clips → `Plugin.Maui.ClipboardPlus`
- Device fingerprint / NFC / biometric / GPS capability → `Plugin.Maui.DeviceInfoPlus`
- NFC NDEF read/write, tag ID, attendance / inventory → `Plugin.Maui.NfcPlus`
- Lock the app after background (Face ID / PIN / lock timer) → `Plugin.Maui.AppLock`
- HTTP GET cache / CacheFirst / StaleWhileRevalidate → `Plugin.Maui.ApiCache`
- Form validation / email / phone / `Validation.For` → `Plugin.Maui.FormValidation`
- Hide / show keyboard, dismiss on tap, resize vs pan → `Plugin.Maui.KeyboardManager`
- Lock / unlock landscape or portrait, per-page orientation → `Plugin.Maui.DeviceOrientationPlus`

## 2. Install

```bash
dotnet add package Plugin.Maui.NetworkMonitor
```

Confirm the package supports your target frameworks. Most plugins ship `net10.0`, `net10.0-android`, and `net10.0-ios`. NetworkMonitor also ships `net8.0` / `net9.0`.

## 3. Register

Each plugin adds a MAUI builder extension. Typical pattern:

```csharp
builder
    .UseMauiApp<App>()
    .UseNetworkMonitor(options =>
    {
        options.EnableHttpProbe = true;
        options.EnableCaptivePortalDetection = true;
    });
```

Resolve the interface from DI, or use the static `Current` / `Default` accessor documented in that plugin's README.

## 4. Platform setup

Read the plugin README before generating code. Many plugins need:

- Android `AndroidManifest.xml` permissions
- iOS `Info.plist` usage strings or background modes
- iOS privacy manifest entries for User Defaults
- Host-app Firebase / APNs / Play Core setup (PushRouter, AppUpdate)

## 5. Verify with the sample

Each repository includes `samples/` and usually `tests/`. Prefer the sample over inventing a new registration sequence.

## 6. Compose, do not stack blindly

These plugins are designed to compose:

- BackgroundTasks can call `JobQueue.Current.DrainAsync()` or `RetryQueue.Current.DrainAsync()`
- MediaPipeline can hand off to FileVault or SmartUpload
- SecureSession persists tokens with SecureStoragePlus
- ApiCache caches GET responses; ApiResilience retries them; OfflineSync owns local writes
- Observability registers several sibling plugins — only use it when you want that umbrella

Do not add Observability or the full catalog for a single feature.

## 7. Upgrade hardened 1.x plugins

Fourteen plugins shipped fail-closed and correctness fixes on 3 September 2026. DeepLinks, PushRouter, SmartUpload, and FeatureFlags changed defaults. See [Hardened releases](hardened-releases.md) before bumping:

```bash
dotnet add package Plugin.Maui.DeepLinks --version 1.0.6
dotnet add package Plugin.Maui.PushRouter --version 1.0.6
dotnet add package Plugin.Maui.SmartUpload --version 1.0.6
dotnet add package Plugin.Maui.FeatureFlags --version 1.0.7
dotnet add package Plugin.Maui.ApiResilience --version 1.0.8
```

## Continuous integration

The hub workflow at `.github/workflows/ci.yml` runs only when started manually (`workflow_dispatch`). It does not run on push to `main`, so adding or bumping a submodule does not rebuild every plugin. Every job builds the library, runs tests, then `dotnet pack` with portable PDBs so each plugin produces a `.nupkg` and a `.snupkg`. Packages are not published to NuGet.org.

- Ubuntu: `net10.0`
- macOS: `net10.0`, `net10.0-android`, `net10.0-ios` (and Mac Catalyst when the plugin declares it)
- Windows: `net10.0` plus `net10.0-windows` for shared libraries and MVVMExpress

Each plugin repo can reuse the same job via `.github/plugin-repo-ci.yml`.

## Next

- [Hardened releases](hardened-releases.md)
- [Architecture](architecture.md)
- [Package directory](packages/README.md)
- [AGENTS.md](../AGENTS.md)
