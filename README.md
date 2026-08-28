# NugetWorld

Catalog of .NET MAUI plugins for **Android** and **iOS**. Each plugin lives in its own repository and is referenced here as a git submodule.

## Plugins

| Plugin | Package | What it does |
| --- | --- | --- |
| [GeoLocator](https://github.com/NiladriPadhy/Plugin.Maui.GeoLocator) | [Plugin.Maui.GeoLocator](https://www.nuget.org/packages/Plugin.Maui.GeoLocator) | On-demand location, tracking, and reverse geocoding |
| [NetworkMonitor](https://github.com/NiladriPadhy/Maui.NetworkMonitor) | [Plugin.Maui.NetworkMonitor](https://www.nuget.org/packages/Plugin.Maui.NetworkMonitor) | Real internet availability, captive portals, and Wi-Fi vs cellular |
| [BackgroundTasks](https://github.com/NiladriPadhy/Plugin.Maui.BackgroundTasks) | [Plugin.Maui.BackgroundTasks](https://www.nuget.org/packages/Plugin.Maui.BackgroundTasks) | One-time and periodic background work on JobScheduler / BGTaskScheduler |
| [SmartUpload](https://github.com/NiladriPadhy/Plugin.Maui.SmartUpload) | [Plugin.Maui.SmartUpload](https://www.nuget.org/packages/Plugin.Maui.SmartUpload) | Chunked, resumable uploads with retry and process-death recovery |
| [DeviceSession](https://github.com/NiladriPadhy/Plugin.Maui.DeviceSession) | [Plugin.Maui.DeviceSession](https://www.nuget.org/packages/Plugin.Maui.DeviceSession) | Device, installation, and analytics session identity |
| [OfflineSync](https://github.com/NiladriPadhy/Plugin.Maui.OfflineSync) | [Plugin.Maui.OfflineSync](https://www.nuget.org/packages/Plugin.Maui.OfflineSync) | Offline-first local writes with queued sync and conflict resolution |
| [PushRouter](https://github.com/NiladriPadhy/Plugin.Maui.PushRouter) | [Plugin.Maui.PushRouter](https://www.nuget.org/packages/Plugin.Maui.PushRouter) | Route FCM / APNs payloads to handlers and Shell screens |
| [PermissionFlow](https://github.com/NiladriPadhy/Plugin.Maui.PermissionFlow) | [Plugin.Maui.PermissionFlow](https://www.nuget.org/packages/Plugin.Maui.PermissionFlow) | Named permission flows with rationale, cooldown, and Settings fallback |
| [AppHealth](https://github.com/NiladriPadhy/Plugin.Maui.AppHealth) | [Plugin.Maui.AppHealth](https://www.nuget.org/packages/Plugin.Maui.AppHealth) | App, device, and environment health reports |
| [SecureStoragePlus](https://github.com/NiladriPadhy/SecureStoragePlus) | [Plugin.Maui.SecureStoragePlus](https://www.nuget.org/packages/Plugin.Maui.SecureStoragePlus) | AES-256-GCM secure storage with expiry and migration |
| [SecureSession](https://github.com/NiladriPadhy/Plugin.Maui.SecureSession) | [Plugin.Maui.SecureSession](https://www.nuget.org/packages/Plugin.Maui.SecureSession) | Access/refresh tokens, 401 retry, logout, biometrics, multi-device sessions |
| [ApiResilience](https://github.com/NiladriPadhy/Plugin.Maui.ApiResilience) | [Plugin.Maui.ApiResilience](https://www.nuget.org/packages/Plugin.Maui.ApiResilience) | HttpClient retry, circuit breaker, offline queue, and token refresh |
| [FileVault](https://github.com/NiladriPadhy/Plugin.Maui.FileVault) | [Plugin.Maui.FileVault](https://www.nuget.org/packages/Plugin.Maui.FileVault) | Encrypted local files with key protection and lifecycle controls |
| [MediaPipeline](https://github.com/NiladriPadhy/Plugin.Maui.MediaPipeline) | [Plugin.Maui.MediaPipeline](https://www.nuget.org/packages/Plugin.Maui.MediaPipeline) | Camera-to-upload image pipeline: resize, compress, EXIF, watermark, blur, encrypt |
| [VoipCore](https://github.com/NiladriPadhy/Plugin.Maui.VoipCore) | [Plugin.Maui.VoipCore](https://www.nuget.org/packages/Plugin.Maui.VoipCore) | SIP/VoIP session model with a pluggable signaling stack |
| [FeatureFlags](https://github.com/NiladriPadhy/Plugin.Maui.FeatureFlags) | [Plugin.Maui.FeatureFlags](https://www.nuget.org/packages/Plugin.Maui.FeatureFlags) | Mobile-first feature flags with MAUI targeting and remote config |
| [DeepLinks](https://github.com/NiladriPadhy/Plugin.Maui.DeepLinks) | [Plugin.Maui.DeepLinks](https://www.nuget.org/packages/Plugin.Maui.DeepLinks) | App Links, Universal Links, custom schemes, and auth-restore |
| [Performance](https://github.com/NiladriPadhy/Plugin.Maui.Performance) | [Plugin.Maui.Performance](https://www.nuget.org/packages/Plugin.Maui.Performance) | Lightweight profiler for startup, pages, APIs, images, and memory |
| [Diagnostics](https://github.com/NiladriPadhy/Plugin.Maui.Diagnostics) | [Plugin.Maui.Diagnostics](https://www.nuget.org/packages/Plugin.Maui.Diagnostics) | Crash, ANR, unhandled exceptions, and pre-crash breadcrumbs |
| [Observability](https://github.com/NiladriPadhy/Plugin.Maui.Observability) | [Plugin.Maui.Observability](https://www.nuget.org/packages/Plugin.Maui.Observability) | Umbrella telemetry pipeline over AppHealth, Network, API, Upload, Sync, Background, Device, and Crash |

## Clone

```bash
git clone --recurse-submodules https://github.com/NiladriPadhy/NugetWorld.git
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

## Install a plugin

Each package is published independently:

```bash
dotnet add package Plugin.Maui.GeoLocator
```

See the plugin README in its repository for registration and platform setup.

## Support

> If these plugins saved you a weekend of native plumbing, consider buying me a coffee.
> Your support keeps this catalog maintained, documented, and free.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/npadhy)

These libraries stay open source. A coffee helps cover time for bug fixes, new features, and docs.
