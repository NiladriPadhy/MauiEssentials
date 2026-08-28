# Architecture

NugetWorld is a **catalog**, not a monorepo product. Each plugin is an independent git repository, NuGet package, and submodule.

```
Developer requirement
        ↓
README / llms.txt requirement map
        ↓
One plugin repository
        ↓
src/          library
samples/      MAUI host app
tests/        unit tests
README.md     human + LLM docs
llms.txt      LLM index
AGENTS.md     coding-agent guide
```

## Design rules

1. **One problem per package.** Descriptions name the problem (captive portal, durable queue, resumable upload), not “part of MauiEssentials”.
2. **Android and iOS first.** Shared `net10.0` exists so tests and class libraries can reference the API. Native calls typically throw `FeatureNotSupported` on that TFM.
3. **MAUI builder registration.** Plugins expose `UseX(...)` and a `Current` / `Default` accessor.
4. **Compose, do not replace the OS.** BackgroundTasks wraps JobScheduler / BGTaskScheduler. JobQueue is an in-process SQLite worker. PushRouter does not register FCM tokens. VoipCore does not ship PJSIP.
5. **Prefer the framework when it is enough.** `Connectivity`, `Geolocation`, `SecureStorage`, and `Permissions` remain the default if they already solve the request.

## How plugins relate

| Need | Start with | Often compose with |
| --- | --- | --- |
| Location | GeoLocator | PermissionFlow |
| Connectivity | NetworkMonitor | AppHealth, OfflineSync, ApiResilience |
| Background work | BackgroundTasks | JobQueue |
| Durable jobs | JobQueue | BackgroundTasks, SmartUpload |
| Uploads | SmartUpload | MediaPipeline, FileVault, JobQueue |
| Offline data | OfflineSync | NetworkMonitor, BackgroundTasks |
| Auth tokens | SecureSession | SecureStoragePlus, ApiResilience |
| Encrypted files | FileVault | MediaPipeline, SecureStoragePlus |
| Push taps | PushRouter | DeepLinks |
| Telemetry suite | Observability | AppHealth, Diagnostics, NetworkMonitor |

## Observability

`Plugin.Maui.Observability` is the only umbrella package. It depends on AppHealth, NetworkMonitor, ApiResilience, BackgroundTasks, OfflineSync, SmartUpload, and DeviceSession. Recommend it only when the user wants a unified export path.

## Repository inspection order for agents

1. Hub [README.md](../README.md) or [llms.txt](../llms.txt)
2. Matching plugin README
3. Plugin `llms.txt` / `AGENTS.md`
4. `src/` public types
5. `samples/` registration and platform files
6. `tests/` for expected error behavior
