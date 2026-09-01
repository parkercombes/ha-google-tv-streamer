# Patched TvOverlay APK (Android 14 fix)

On-screen overlays in this integration are rendered by the third-party
**TvOverlay** app (github.com/gugutab/TvOverlay), which runs *on* the Google TV
Streamer and exposes an HTTP REST API on port 5001. This integration only talks
to that API — it does not bundle or ship the app.

## Why a patch is needed

The only released TvOverlay build — **v1.0.3 (versionCode 10030)**, from October
2023 — is **broken on Android 14 / Google TV OS 14**. Its `OverlayService`
declares no `android:foregroundServiceType`, so on `targetSdk 34` the very first
`startForeground()` call throws:

```
java.lang.RuntimeException: Unable to create service
  com.tabdeveloper.tvoverlay.OverlayService:
  android.app.MissingForegroundServiceTypeException: Starting FGS without a type
```

The service dies on creation and the REST server never starts. Foreground
service types became mandatory in Android 14
(https://developer.android.com/about/versions/14/changes/fgs-types-required).

## The fix (manifest-only — no code/smali changes)

Android 14's two-argument `startForeground(id, notification)` reads the type from
the manifest, so declaring it there is sufficient. Three additive edits to
`AndroidManifest.xml`:

1. Add the permission:
   `<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>`
2. On the `com.tabdeveloper.tvoverlay.OverlayService` `<service>` element add:
   `android:foregroundServiceType="specialUse"`
3. Nest a property inside that same `<service>` element (satisfies Play/OEM
   validation; runtime does not require it):
   `<property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="overlay_http_server"/>`

Package name, versionCode, versionName, and all components are unchanged.

## Checksums

| File | SHA-256 |
|------|---------|
| Original `10030.apk` (from GitHub releases) | `1df7f5d0f8141e0b736c481ce8399b2888729b778074b09c28f04e922db994f1` |
| `TvOverlay-patched-signed.apk` (this dir)   | `18dd3df8fe25f955813b1880a26219a22e391eea8bab1a046d05e4b770164de7` |

The patched APK is signed with a throwaway debug key (v1+v2+v3), which is fine
for sideloading to your own device.

## How to rebuild from scratch

Requires: `apktool` (3.0.3 used here), a JDK, and
[`uber-apk-signer`](https://github.com/patrickfav/uber-apk-signer).

```bash
# 1. Get the original
curl -fL -o TvOverlay-10030.apk \
  https://github.com/gugutab/TvOverlay/releases/download/TvOverlay/10030.apk

# 2. Decompile (use a local framework dir to avoid ~/Library writes)
apktool d -f -p ./apktool-framework -o ./src TvOverlay-10030.apk

# 3. Apply the three manifest edits above to ./src/AndroidManifest.xml

# 4. Rebuild
apktool b -p ./apktool-framework ./src -o ./patched-unsigned.apk

# 5. Zipalign + sign (auto debug key, v1+v2+v3)
java -jar uber-apk-signer.jar -a ./patched-unsigned.apk --allowResign --overwrite
cp ./patched-unsigned.apk TvOverlay-patched-signed.apk   # signer overwrites in place
```

## Install on the Streamer

```bash
adb connect 192.168.1.189:5555
adb uninstall com.tabdeveloper.tvoverlay            # if the broken original is present
adb install TvOverlay-patched-signed.apk
adb shell appops set com.tabdeveloper.tvoverlay SYSTEM_ALERT_WINDOW allow
adb shell am start -n com.tabdeveloper.tvoverlay/.SetupActivity
```

**Manual step (cannot be automated over the network):** on the TV, open
TvOverlay once and approve its on-screen **"grant overlay access"** prompt with
the remote. After that the REST server listens on `http://<ip>:5001`.

> Note: the server is torn down when the display sleeps and comes back when the
> app is next foregrounded. This integration self-heals that by re-launching the
> app over ADB and retrying the overlay call.
