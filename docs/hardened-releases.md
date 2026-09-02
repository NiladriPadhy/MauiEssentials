# Hardened plugin releases — 3 September 2026

Fourteen MauiEssentials plugins shipped new NuGet versions after a catalog security and correctness review. Plugin READMEs already describe the APIs. This page is the upgrade map for host apps and the technical record for agents.

**Tests:** 351 passing across the 14 projects.  
**Hub commit:** `Point hardened plugins at their new NuGet releases and document the defaults.`

| Package | Version | Tests | Kind |
| --- | --- | ---: | --- |
| [Plugin.Maui.ApiResilience](https://www.nuget.org/packages/Plugin.Maui.ApiResilience/1.0.8) | 1.0.8 | 13 | Default change |
| [Plugin.Maui.AppLock](https://www.nuget.org/packages/Plugin.Maui.AppLock/1.0.5) | 1.0.5 | 20 | Additive |
| [Plugin.Maui.AppUpdate](https://www.nuget.org/packages/Plugin.Maui.AppUpdate/1.0.6) | 1.0.6 | 30 | Packaging |
| [Plugin.Maui.BackgroundTasks](https://www.nuget.org/packages/Plugin.Maui.BackgroundTasks/1.0.6) | 1.0.6 | 10 | Behavior |
| [Plugin.Maui.DeepLinks](https://www.nuget.org/packages/Plugin.Maui.DeepLinks/1.0.6) | 1.0.6 | 43 | Breaking default |
| [Plugin.Maui.DeviceSession](https://www.nuget.org/packages/Plugin.Maui.DeviceSession/1.0.6) | 1.0.6 | 21 | Additive |
| [Plugin.Maui.FeatureFlags](https://www.nuget.org/packages/Plugin.Maui.FeatureFlags/1.0.7) | 1.0.7 | 45 | Breaking default |
| [Plugin.Maui.FileVault](https://www.nuget.org/packages/Plugin.Maui.FileVault/1.0.8) | 1.0.8 | 31 | Behavior + API |
| [Plugin.Maui.NetworkMonitor](https://www.nuget.org/packages/Plugin.Maui.NetworkMonitor/1.0.7) | 1.0.7 | 28 | Metadata |
| [Plugin.Maui.Observability](https://www.nuget.org/packages/Plugin.Maui.Observability/1.0.7) | 1.0.7 | 23 | Build wiring |
| [Plugin.Maui.OfflineSync](https://www.nuget.org/packages/Plugin.Maui.OfflineSync/1.0.9) | 1.0.9 | 13 | Behavior |
| [Plugin.Maui.PushRouter](https://www.nuget.org/packages/Plugin.Maui.PushRouter/1.0.6) | 1.0.6 | 24 | Breaking default |
| [Plugin.Maui.SecureSession](https://www.nuget.org/packages/Plugin.Maui.SecureSession/1.0.6) | 1.0.6 | 26 | Additive |
| [Plugin.Maui.SmartUpload](https://www.nuget.org/packages/Plugin.Maui.SmartUpload/1.0.6) | 1.0.6 | 24 | Breaking default |

Install the version in the table. SemVer is still 1.x — defaults changed, public type names did not.

```bash
dotnet add package Plugin.Maui.DeepLinks --version 1.0.6
```

## Breaking defaults (set these on upgrade)

Hosts that relied on “empty means allow everything” or cleartext HTTP must opt back in.

### DeepLinks 1.0.6

Incoming App Links, Universal Links, and custom schemes are **fail-closed**.

- Empty `Hosts` rejects HTTPS links.
- Empty `CustomSchemes` rejects `myapp://` links.
- `http://` is rejected unless `AllowInsecureHttp = true`.
- Set `PermissiveMode = true` only when you intentionally accept any host or scheme.

```csharp
builder.UseMauiDeepLinks(options =>
{
    options.Hosts.Add("example.com");
    options.CustomSchemes.Add("myapp");
    // options.PermissiveMode = true;      // old default-open behavior
    // options.AllowInsecureHttp = true;   // local http:// only
});
```

### PushRouter 1.0.6

Navigation uses registered `Map` keys or `DefaultRoute` only. A raw payload path such as `"//order?id=1842"` is ignored unless `AllowUnmappedPayloadRoutes = true`.

```csharp
builder.UsePushRouter(options =>
{
    options.Map("order", "//order?id={orderId}");
    options.DefaultRoute = "//notifications";
    // options.AllowUnmappedPayloadRoutes = true;
});
```

### SmartUpload 1.0.6

Upload endpoints must be `https`. Set `RequireHttps = false` only for local development.

```csharp
builder.UseSmartUpload(options =>
{
    options.RequireHttps = true; // default
});

await SmartUpload.Current.EnqueueAsync(new UploadRequest
{
    FilePath = photoPath,
    Endpoint = new Uri("https://uploads.example.com/files/"),
    Protocol = UploadProtocolKind.Tus
});
```

### FeatureFlags 1.0.7

`RemoteUri` must be `https` (`RequireHttps = true`). Optional `SignatureKey` verifies `X-FeatureFlags-Signature` as HMAC-SHA256 hex over the response body.

```csharp
builder.UseFeatureFlags(options =>
{
    options.RemoteUri = new Uri("https://cdn.example.com/flags.json");
    options.RequireHttps = true;
    options.SignatureKey = hmacSecret; // optional
});
```

### ApiResilience 1.0.8

The offline queue file is AES-256-GCM (`EncryptQueue = true`). Existing plaintext queue files still load. Set `PersistRequestBodies = false` to store a redacted placeholder instead of POST/PUT bodies.

```csharp
builder.UseApiResilience(options =>
{
    options.OfflineQueue.Enabled = true;
    options.OfflineQueue.EncryptQueue = true;
    options.OfflineQueue.PersistRequestBodies = false;
});
```

The queue key lives next to the queue file in the app sandbox (not in Keystore / Keychain).

## Additive APIs and behavior

### FileVault 1.0.8

- Background lock **always** clears the in-memory master key, even when an in-flight write holds the gate longer than the wait timeout.
- Prefer `GetStatisticsAsync`. Sync `GetStatistics()` times out after 5 seconds.
- `RootDirectory` must resolve inside the host-chosen folder (`VaultName` cannot traverse with `..`).
- `Events.OnProtectionFailed` reports iOS Data Protection or backup-exclusion failures. Files stay encrypted.

```csharp
builder.UseFileVault(options =>
{
    options.LockOnBackground = true;
    options.Events.OnProtectionFailed = (path, ex) =>
        logger.LogWarning(ex, "platform protection failed for {Path}", path);
});

var stats = await FileVault.Current.GetStatisticsAsync();
```

### SecureSession 1.0.6

`LoginAsync(TokenBundle)` is still host-trusted by default (`AcceptUnvalidatedTokens = true`) so existing OAuth restore flows keep working. Set it to `false` so only `IAuthGateway` can create a session.

```csharp
builder.UseSecureSession(options =>
{
    options.AcceptUnvalidatedTokens = false;
});
```

### DeviceSession 1.0.6

IDs stay in MAUI `Preferences`. Set `UseSecureStorage = true` for a higher-assurance store on rooted or jailbroken devices. Identifiers are not secrets.

```csharp
builder.UseDeviceSession(options =>
{
    options.UseSecureStorage = true;
});
```

### AppLock 1.0.5

If the automatic resume prompt throws, `AuthenticationCompleted` still fires with a failed result so the cover stays up. Subscribe when the host must distinguish cancel vs platform error.

### BackgroundTasks 1.0.6

Android `JobService` logs handler exceptions (`Plugin.Maui.BackgroundTasks`). `OperationCanceledException` is a cancelled run and is **not** retried.

### OfflineSync 1.0.9

Timer and connectivity-driven auto-sync catch exceptions so a failed push does not crash the process. Subscribe to `SyncCompleted` / `StatusChanged`, or call `SyncAsync`, when the UI must surface errors. Android `JobFinished` is null-safe.

### Observability 1.0.7

A MauiEssentials hub clone uses sibling `ProjectReference`s (`UseMonorepoRefs=true`). A standalone clone of this repo uses the published PackageReferences (NetworkMonitor 1.0.7, ApiResilience 1.0.8, BackgroundTasks 1.0.6, …). Set `UseMonorepoRefs=false` to force NuGet packages inside the hub.

### NetworkMonitor 1.0.7

NuGet metadata only: `Authors` and `PackageLicenseExpression` MIT. No API change. Still the only catalog plugin that also ships `net8.0` / `net9.0`.

### AppUpdate 1.0.6

Adds a Visual Studio solution (`Plugin.Maui.AppUpdate.sln`). No API change.

## What did not change

- Target frameworks stay `net10.0`, `net10.0-android`, `net10.0-ios` (NetworkMonitor also `net8.0` / `net9.0`).
- Android API 21+ except SecureSession / AppLock (API 23+). iOS 15+.
- Registration helpers (`UseMauiDeepLinks`, `UsePushRouter`, `UseApiResilience`, …) and `Current` / `Default` accessors.
- Mac Catalyst and Windows remain non-targets except MVVMExpress.

## Suggested upgrade order

1. DeepLinks and PushRouter — inbound URI / push navigation can stop if allowlists are empty.
2. SmartUpload and FeatureFlags — cleartext `http://` endpoints fail closed.
3. ApiResilience — confirm the encrypted queue still drains after the first run.
4. FileVault — switch UI stats to `GetStatisticsAsync`.
5. SecureSession / DeviceSession — opt into the stricter flags if the threat model needs them.
6. AppLock, BackgroundTasks, OfflineSync, Observability — take the behavior fixes; no host config required.
7. NetworkMonitor, AppUpdate — bump for metadata / packaging only.

## Per-package docs

Each repository README is the code-level source of truth. Hub indexes:

- [Getting started](getting-started.md)
- [Package directory](packages/README.md)
- [Architecture](architecture.md)
- [llms-full.txt](../llms-full.txt)

Public catalog: https://nuvyntralabs.github.io/packages/
