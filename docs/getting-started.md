# Getting started

MauiEssentials is a catalog of focused .NET MAUI plugins. You do not reference this repository as a single NuGet package. Install the plugin that matches the requirement.

## 1. Pick a package

Use the [requirement → package map](packages/README.md) or the tables in the [root README](../README.md).

Examples:

- Real internet vs captive portal → `Plugin.Maui.NetworkMonitor`
- GPS + reverse geocoding → `Plugin.Maui.GeoLocator`
- Durable work that must survive process death → `Plugin.Maui.JobQueue`
- OS-scheduled refresh → `Plugin.Maui.BackgroundTasks`

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

- BackgroundTasks can call `JobQueue.Current.DrainAsync()`
- MediaPipeline can hand off to FileVault or SmartUpload
- SecureSession persists tokens with SecureStoragePlus
- Observability registers several sibling plugins — only use it when you want that umbrella

Do not add Observability or the full catalog for a single feature.

## Next

- [Architecture](architecture.md)
- [Package directory](packages/README.md)
- [AGENTS.md](../AGENTS.md)
