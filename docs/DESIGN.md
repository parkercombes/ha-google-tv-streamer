# Design — how it works and why

## Form factor

This is a single Python HACS integration over **network ADB**, with no companion Android
app to maintain. The one thing that genuinely needs on-device code is on-screen overlays.
The existing **TvOverlay** app already handles that, and the integration drives it over HTTP.
The differentiator versus the official Cast / `androidtv_remote` integrations is
**real in-app now-playing state**.

## Device facts (verified on hardware, 2026-08/09)

- **Device:** model `Google_TV_Streamer`, codename `kirkwood`, Android TV OS 14 (SDK 34).
- **Enabling ADB:** go to Settings → System → About and tap "Android TV OS build" 7× to unlock
  Developer options. Then turn on USB debugging and Wireless debugging.
- **Two ADB surfaces:**
  - mDNS advertises `_adb-tls-connect._tcp`, which is **ADB-over-TLS** on a port that is
    randomized on reboot. `adb-shell` can't speak TLS; it fails on `STLS`.
  - **Plain adbd on 5555** exists once wireless debugging is authorized. The integration uses 5555
    with its own adbkey.
- **HA's key needs authorizing:** HA generates its own adbkey, and the on-TV "Allow wireless
  debugging" prompt must be accepted. `transport.py` therefore uses `auth_timeout_s=30`.

## Modules

| Module | Role |
|---|---|
| `adb.py` | Pure parsers + `GoogleTVStreamerADB(shell_runner)`: `parse_resumed_activity`, `parse_active_media_session`, `parse_audio_owner`, `now_playing()`, `restart_overlay_app()` |
| `transport.py` | `AdbTransport` / `connect_streamer(host, port=5555, …)` over `adb-shell`; injectable `device_factory` |
| `overlay.py` | `TvOverlayClient` for the TvOverlay REST API (port 5001); injectable `poster`; `recover` seam |
| `config_flow.py` | Manual host/port only; `cannot_connect` on failure (never crash the dialog) |
| `coordinator.py`, `media_player.py`, `remote.py` | HA entities |
| `__init__.py` | Services: `launch_app`, `send_key`, `show_overlay`, `show_fixed_notification`, `clear_fixed_notification`, `set_overlay` |

## Detection rules (each one learned from a real-device bug)

1. **Foreground app:** use `dumpsys activity activities` → `ResumedActivity`. Don't use
   `dumpsys window` → `mCurrentFocus`, which lies for apps like Dropout that play
   full-screen without taking window focus.
2. **Playback state:** read the session named by `Media button session is <pkg>`, then
   the foreground app's session, and honor its real `PlaybackState` **regardless of the
   `active` flag**. On hardware a session is `active=false` whenever it's stopped, asleep
   or backgrounded, yet it lingers in the dump. (Fixed in v0.1.1.)
3. **Audio-owner fallback** applies only to apps with *no* session block, such as Dropout. It
   fires only when the foreground package is itself in the `Audio playback …` owner list
   and isn't a launcher. It never guesses `owners[0]`. The home-screen launcher lingers in
   that list historically. (Fixed in v0.1.2.)
   - **Watch:** the screensaver `com.google.android.apps.tv.dreamx` isn't
     launcher-excluded. If it ever shows up in the owner list, false "playing" returns.

## Capability matrix (measured on device)

| App | Package | Detect | Play/pause | Position | Transport | Real title |
|---|---|---|---|---|---|---|
| YouTube | `com.google.android.youtube.tv` | ✅ | ✅ | ✅ | full | ✅ title + uploader |
| HBO Max / Max | `com.wbd.stream` | ✅ | ✅ | ✅ | full | ✅ episode (series in subtitle) |
| Netflix | `com.netflix.ninja` | ✅ | ✅ | ✅ | full | ❌ withheld |
| Prime Video | `com.amazon.amazonvideo.livingroom` | ✅ | ✅ | ✅ | full | ⚠️ generic "PrimeVideo" |
| Peacock | `com.peacocktv.peacockandroid` | ✅ | ✅ | ⚠️ bogus | limited | ❌ |
| Dropout | `com.collegehumor.chdropout` | ✅ | ❌ no MediaSession | ❌ | keys only | ❌ |

## Overlays (TvOverlay)

- **HTTP only, never ADB:** port `5001` on the device, no auth. The endpoints are `/notify`,
  `/notify_fixed` (clear with `visible:false`) and `/set/overlay`, and the client maps
  snake_case fields to TvOverlay's camelCase.
- **Overlays render over live playback** without changing the foreground app.
- **The stock APK is dead on Android 14:** there's no `foregroundServiceType`, so `startForeground` throws.
  A manifest-only patch fixes it (`specialUse`). The patched package is
  `com.tabdeveloper.tvoverlay`. Recipe: `tools/tvoverlay-patched/REBUILD.md`.
- **One manual step:** the on-TV "grant overlay access" prompt needs a physical remote
  click. `appops SYSTEM_ALERT_WINDOW allow` alone isn't enough.
- **Sleep:** the :5001 server dies when the display sleeps, because Android reclaims the
  foreground service. Two defences:
  - The app is whitelisted from doze: `dumpsys deviceidle whitelist +com.tabdeveloper.tvoverlay`.
  - The client self-heals. On an `OSError` it foregrounds TvOverlay over ADB, presses **BACK**,
    and retries once.

  The first version pressed HOME, which ejected the viewer from their show. That's the lesson:
  don't build disruptive auto-recovery before the base capability is proven.
- **Probing the listener:** it binds tcp6 `::`, so check `/proc/net/tcp6` (hex port `1389`) as
  well as `/proc/net/tcp`. A `curl` to :5001 is the authoritative check.
