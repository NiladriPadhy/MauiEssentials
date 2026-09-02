# MauiEssentials submodule review

**Date:** 2 September 2026  
**Scope:** All 36 plugin submodules (`src/` plus hub `.gitmodules` / gitlink state)  
**Method:** Static review of source, project metadata, and this clone’s git wiring. Samples and tests were checked for presence, not executed as a full suite.

Nothing critical turned up. There are no hardcoded secrets, no weak crypto, no SQL injection, and no TLS bypass in `src/`. The real issues are default-open security, a few secrets-at-rest gaps, and this clone’s submodule wiring.

| Severity | Count |
| --- | ---: |
| High | 5 |
| Medium | 10 |
| Low | 8 |

| Category | Count |
| --- | ---: |
| Default-open APIs | 5 |
| Secrets at rest | 3 |
| Exception handling | 3 |
| Correctness | 3 |
| Packaging / CI | 6 |
| Hub git wiring | 2 |

## What looks solid

- Every plugin ships `LICENSE`, `README.md`, `AGENTS.md`, `llms.txt`, `tests/`, and a sample.
- Crypto plugins (FileVault, SecureStoragePlus) use AES-256-GCM and PBKDF2-SHA256.
- SQLite plugins (JobQueue, OfflineSync, ApiCache) use parameterized queries or ORM APIs.
- Android / iOS implementations do not throw `NotImplementedException`. `FeatureNotSupported` is limited to the shared `net10.0` TFM, which is intentional.
- Recorded gitlink SHAs match the checked-out commits. Working trees are clean.

## High

### DeepLinks — empty Hosts and CustomSchemes accept any URI

- **Location:** `DeepLinks/src/Plugin.Maui.DeepLinks/Internal/DeepLinkParser.cs`, `DeepLinksOptions.cs`
- **Why:** Defaults document “empty means any host / any custom scheme.” A host that forgets to configure allowlists will dispatch `https://evil.com` and `myapp://` links into registered handlers and Shell.
- **Fix:** Fail closed when `Hosts` or `CustomSchemes` are empty, or require an explicit `PermissiveMode` flag.

### PushRouter — push payloads can drive arbitrary Shell paths

- **Location:** `PushRouter/src/Plugin.Maui.PushRouter/PushRouterImplementation.cs` (`ResolveNavigationRoute`)
- **Why:** If no `RouteMap` template matches, the raw FCM/APNs route (or `RouteKey` data) is used for Shell navigation. Unlike DeepLinks, there is no auth gate or registered-route allowlist.
- **Fix:** Navigate only through registered `RouteMap` templates; reject payload paths that are not in the map.

### FileVault — background lock can skip clearing the master key

- **Location:** `FileVault/src/Plugin.Maui.FileVault/FileVaultImplementation.cs` (`NotifyBackground`)
- **Why:** If `_gate.Wait(2s)` fails during a long write, the method returns without `ClearKey()`. The decrypted master key and manifest stay in memory while the app is backgrounded.
- **Fix:** Queue the lock after in-flight work, or wipe the key even when the wait times out and finish lock asynchronously.

### ApiResilience — offline queue stores request bodies in plaintext

- **Location:** `ApiResilience/src/Plugin.Maui.ApiResilience/Http/HttpRequestMessageCopier.cs` (`ToQueuedRequestAsync`)
- **Why:** `Authorization` is stripped, but `ContentBase64` is written to `plugin.maui.apiresilience.queue.json`. POST/PUT bodies (PII, passwords, payment payloads) sit unencrypted in app data.
- **Fix:** Encrypt the queue file, redact known-sensitive endpoints, or add an opt-in `QueueSensitiveBody` flag defaulting to off.

### Hub — ten submodules are not registered in this clone

- **Location:** `.git/config` vs `.gitmodules`
- **Why:** ApiCache, AppLock, DeviceOrientation, FormValidation, KeyboardManager, MVVMExpress, NetworkDiagnostics, Nfc, Printing, and RetryQueue show as uninitialized (`-` in `git submodule status`). `git submodule update` / `sync` will skip them. Only CommunityToolkitPlus uses a proper `.git/modules/` gitdir; the rest are nested `.git` directories.
- **Fix:** Run `git submodule init` for the ten names, or re-add them so checkouts use `.git/modules/<name>` instead of nested repos.

## Medium

### SecureSession — `LoginAsync(TokenBundle)` skips the auth gateway

- **Location:** `SecureSession/src/Plugin.Maui.SecureSession/SecureSessionImplementation.cs`
- **Why:** Any in-process caller can install a session from a raw token bundle. This is a useful restore API, but there is no `IAuthGateway.ValidateTokensAsync` step.
- **Fix:** Document as host-trusted, or require an explicit `AcceptUnvalidatedTokens` option and reject otherwise.

### SmartUpload — cleartext `http://` upload endpoints are allowed

- **Location:** `SmartUpload/src/Plugin.Maui.SmartUpload/Internal/RequestValidator.cs`
- **Why:** Scheme must be `http` or `https`. File bytes and session headers can go over the wire unencrypted.
- **Fix:** Default `RequireHttps` to true on release builds; allow `http` only when opted in.

### BackgroundTasks — Android JobService swallows every exception

- **Location:** `BackgroundTasks/src/Plugin.Maui.BackgroundTasks/Platforms/Android/PluginJobService.cs`
- **Why:** A bare `catch { retry = true }` treats logic bugs the same as transient failures and logs nothing. `CancellationToken.None` also blocks cooperative cancel.
- **Fix:** Log the exception, distinguish permanent vs transient failures, and honor the job deadline token.

### FileVault — `GetStatistics()` blocks on an async semaphore

- **Location:** `FileVault/src/Plugin.Maui.FileVault/FileVaultImplementation.cs`
- **Why:** Sync `_gate.Wait()` on the UI thread while an async vault operation holds the gate can freeze or deadlock.
- **Fix:** Add `GetStatisticsAsync` and deprecate the sync method, or wait with a timeout and throw.

### FileVault — `RootDirectory` override is not confined

- **Location:** `FileVault/src/Plugin.Maui.FileVault/Platforms/*/PlatformStorage.cs`
- **Why:** `Path.Combine(overrideRoot, vaultName)` is not checked against app-private roots. A mis-set or user-influenced path can place ciphertext on shared storage.
- **Fix:** Resolve with `Path.GetFullPath` and reject paths outside app-private directories.

### FeatureFlags — remote flag JSON is trusted without a signature

- **Location:** `FeatureFlags/src/Plugin.Maui.FeatureFlags/HttpFeatureFlagProvider.cs`
- **Why:** The HTTP body is deserialized with no JWS / HMAC check. A compromised CDN or MITM can flip kill switches or security flags.
- **Fix:** Require HTTPS, optionally pin certificates, and accept signed flag documents for security-sensitive flags.

### AppLock — foreground re-prompt swallows authentication errors

- **Location:** `AppLock/src/Plugin.Maui.AppLock/AppLockImplementation.cs`
- **Why:** `catch (Exception)` keeps the app locked with no event or log. The user sees a frozen lock screen and the host has no failure signal.
- **Fix:** Raise `AuthenticationCompleted` with a failure reason and log cancel vs platform error separately.

### OfflineSync — auto-sync is fire-and-forget; `JobFinished` may receive null

- **Location:** `OfflineSync/src/Plugin.Maui.OfflineSync/Engine/OfflineSyncInitializer.cs`, `Platforms/Android/OfflineSyncJobService.cs`
- **Why:** `StartAutoSyncAsync` is discarded, so startup failures are invisible. Android `JobFinished(@params, false)` does not guard a nullable `JobParameters`.
- **Fix:** Surface sync-status events, log startup failures, and null-guard `JobFinished`.

### Observability — only builds inside this monorepo

- **Location:** `Observability/src/Plugin.Maui.Observability/Plugin.Maui.Observability.csproj`
- **Why:** Seven `ProjectReference`s point at `../../../AppHealth`, `NetworkMonitor`, and siblings. Cloning `Plugin.Maui.Observability` alone cannot build or pack. Sibling versions also drift (1.0.5–1.0.8 vs Observability 1.0.6).
- **Fix:** Use pinned `PackageReference` for release; keep `ProjectReference` behind a `UseMonorepoRefs` property.

### Catalog-wide — no CI workflows in the hub or any plugin

- **Location:** `.github/workflows` (missing)
- **Why:** None of the 36 plugins or the hub have a GitHub Actions workflow. Build, test, and pack are unenforced on PR and release.
- **Fix:** Add a shared template: `dotnet build`, test, and pack on `net10.0`, plus an optional hub matrix.

## Low

### NetworkMonitor — missing Authors and license metadata

- **Location:** `NetworkMonitor/src/Maui.NetworkMonitor/Maui.NetworkMonitor.csproj`
- **Why:** No `Authors` or `PackageLicenseExpression`. NuGet.org will omit owner/license fields that every peer package sets.
- **Fix:** Add `Authors` and `PackageLicenseExpression` MIT to match the rest of the catalog.

### OfflineSync — missing Authors; Version is duplicated

- **Location:** `OfflineSync/src/Plugin.Maui.OfflineSync/Plugin.Maui.OfflineSync.csproj`
- **Why:** `Authors` is absent. Both `Version` and `PackageVersion` are set to 1.0.8, which can drift independently later.
- **Fix:** Add `Authors` and keep a single version property.

### Hub — six plugins have remotes but no upstream tracking

- **Plugins:** ApiCache, BluetoothManager, DeviceOrientation, KeyboardManager, Nfc, RetryQueue
- **Why:** `origin` exists, but `main` does not track `origin/main`. `git pull` / `git submodule foreach` fetch will not report ahead/behind for these six. Each still has a `backup/pre-author-rewrite` branch.
- **Fix:** `git -C <plugin> branch --set-upstream-to=origin/main main`

### Catalog-wide — ten plugins have no root solution file

- **Plugins:** ApiCache, ApiResilience, AppUpdate, GeoLocator, NetworkMonitor, Observability, OfflineSync, SecureSession, SecureStoragePlus. MVVMExpress uses `.slnx` only.
- **Why:** Peers ship `Plugin.Maui.*.sln`. Missing solutions make IDE open and CI matrix setup inconsistent.
- **Fix:** Add a root `.sln` matching the peer pattern.

### Catalog-wide — Authors are split between Niladri and MauiEssentials

- **Why:** NuGet owner strings are inconsistent. 24 packages use `Niladri`, 8 use `MauiEssentials` (AppHealth, BackgroundTasks, BluetoothManager, DeviceSession, GeoLocator, PermissionFlow, PushRouter, SmartUpload), 2 are missing.
- **Fix:** Pick one string (or `Niladri;MauiEssentials`) and apply it everywhere.

### Nfc, DeviceOrientation, NetworkMonitor — directory names do not match PackageId

- **Why:** Hub paths and assembly names diverge from NuGet IDs (`Nfc/` vs `Plugin.Maui.NfcPlus`, `DeviceOrientation/` vs `DeviceOrientationPlus`, `src/Maui.NetworkMonitor`). Easy to clone or reference the wrong name.
- **Fix:** Document the mapping in the hub README, or rename directories to match PackageId.

### DeviceSession — device identifiers live in unencrypted Preferences

- **Location:** `DeviceSession/src/Plugin.Maui.DeviceSession/Internal/PreferencesDeviceSessionStore.cs`
- **Why:** Install/session IDs are not secrets, but they are tamperable on rooted or jailbroken devices.
- **Fix:** Document the threat model; offer a SecureStorage-backed store for high-assurance apps.

### VoipCore, FileVault, ApiCache — swallowed errors in best-effort paths

- **Location:** VoipCore shutdown helpers, FileVault `ApplyPlatformProtection`, ApiCache `RevalidateAsync`
- **Why:** Empty catch blocks hide teardown, file-protection, and cache-revalidation failures. Encryption still applies in FileVault; stale cache can persist in ApiCache.
- **Fix:** Log at debug/warning and expose optional failure events.

## Hub git wiring

This working copy is only partly a real submodule checkout. `git config` has 27 of 36 submodule URLs.

**Uninitialized in `.git/config` (10):**

- ApiCache
- AppLock
- DeviceOrientation
- FormValidation
- KeyboardManager
- MVVMExpress
- NetworkDiagnostics
- Nfc
- Printing
- RetryQueue

**Remote present, no upstream (6):**

- ApiCache
- BluetoothManager
- DeviceOrientation
- KeyboardManager
- Nfc
- RetryQueue

CommunityToolkitPlus is the only plugin using `.git/modules/CommunityToolkitPlus`.

## Intentional, not bugs

- `FeatureNotSupported` on the shared `net10.0` TFM is by design.
- NetworkMonitor HTTP captive-portal probes are the standard `generate_204` pattern.
- SecureSession JWT `exp` parsing is for refresh scheduling only — it does not validate signatures.
- SharePlus `PreferOriginal` copies files that sit outside the FileProvider root.

## Implementation status (2 September 2026)

The items above were addressed in this working tree:

- DeepLinks fails closed unless `PermissiveMode` is set; `AllowInsecureHttp` gates `http://`.
- PushRouter navigates only through registered maps / `DefaultRoute` unless `AllowUnmappedPayloadRoutes` is set.
- FileVault always clears the master key on background lock, adds `GetStatisticsAsync`, and confines `RootDirectory` overrides.
- ApiResilience encrypts the on-disk queue (AES-256-GCM) and can redact bodies with `PersistRequestBodies = false`.
- Observability uses sibling `ProjectReference`s when the hub is present, otherwise pinned `PackageReference`s.
- Hub CI plus a reusable plugin workflow were added. NetworkMonitor and OfflineSync NuGet metadata were filled in.
- SecureSession, SmartUpload, FeatureFlags, AppLock, OfflineSync, BackgroundTasks, and DeviceSession received the review’s medium/low hardening.

Hub `git submodule init` was run for the ten previously unregistered paths. Nested `.git` directories were left as-is (converting them is a local checkout operation, not a source change).

## Suggested order of work

1. Init the 10 missing submodules and convert nested `.git` dirs to `.git/modules` checkouts.
2. Fail closed in DeepLinks and restrict PushRouter to registered route maps.
3. Never skip `ClearKey` on FileVault background lock; add `GetStatisticsAsync`.
4. Encrypt or redact ApiResilience offline queue bodies.
5. Switch Observability to pinned `PackageReference`s for standalone builds.
6. Add a shared CI template and fix NetworkMonitor / OfflineSync NuGet metadata.
