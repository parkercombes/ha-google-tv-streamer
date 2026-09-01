# Google TV Streamer — Home Assistant Integration

Deep control of the **Google TV Streamer (2024, Android TV OS 14)** from Home
Assistant over network ADB: now-playing state, a full remote, app launching /
deep links, and — via the on-device TvOverlay app — real on-screen overlays
that render **over whatever you're watching** without interrupting playback.

> Status: all four capability pillars have been verified on real hardware
> (launch/deep-link, now-playing, remote/power over ADB, and overlays over live
> content). The integration loads cleanly under Home Assistant 2024.3.3.

## Features

- **mDNS auto-discovery** of the streamer (no fixed ADB port to hunt for)
- **Media player entity** — playback state and position where the app exposes it
- **Remote entity** — D-pad, back/home, transport, volume, and power keyevents
- **App launching** by friendly name/package, or any deep-link URL
- **On-screen overlays** via TvOverlay: transient toasts, persistent corner
  badges, and overlay-visibility control — rendered over live playback
- **Self-healing overlays** across display sleep (see
  [On-screen overlays](#on-screen-overlays-tvoverlay))
- An **honest per-app capability matrix** — no overclaiming what an app won't give

## Requirements

- Home Assistant Core **2024.3.3 or later** (validated); earlier 2024.x likely works
- Google TV Streamer (2024 model), Android TV OS 14
- Developer options enabled on the device (Wireless debugging)
- The integration installs its Python dependency automatically (`adb-shell[async]`)
- **Overlays only:** the [TvOverlay](https://github.com/gugutab/TvOverlay) app,
  sideloaded on the streamer (see below). Everything else works without it.

## Capability Matrix

Capabilities are **app-dependent** — Android only surfaces what each app chooses
to expose. The table reflects measured results on a real device (2026-08-31).

| App | Detect app | Play/Pause state | Position | Transport | Real title |
|-----|:---:|:---:|:---:|:---:|:---:|
| YouTube (`com.google.android.youtube.tv`) | ✅ | ✅ | ✅ | full | ✅ title + uploader |
| Netflix (`com.netflix.ninja`) | ✅ | ✅ | ✅ | full | ❌ |
| Prime Video (`com.amazon.amazonvideo.livingroom`) | ✅ | ✅ | ✅ | full | ❌ generic `PrimeVideo` |
| Peacock (`com.peacocktv.peacockandroid`) | ✅ | ✅ | ⚠️ unreliable | limited | ❌ |
| Dropout (`com.collegehumor.chdropout`) | ✅ via resumed-activity + audio-owner | ❌ | ❌ | keyevents only | ❌ |
| HBO Max / Max (`com.wbd.stream`) | ✅ | ✅ | ✅ | full | ✅ episode title (series in subtitle) |

**Titles are the exception, not the rule.** Only **YouTube** and **HBO Max/Max**
reliably provide real in-app content titles (HBO Max also exposes the series name
in the subtitle field); Netflix, Prime Video, Peacock, and Dropout withhold or
genericize them. This is an Android media-session limitation, not something the
integration can work around.

## Installation

### Via HACS (recommended)

1. In HACS → **Integrations** → ⋮ → **Custom repositories**, add:
   - Repository: `https://github.com/parkercombes/ha-google-tv-streamer`
   - Category: **Integration**
2. Install **Google TV Streamer** from HACS.
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/google_tv_streamer/` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Enabling ADB on the Google TV Streamer

1. **Settings → System → About**.
2. Scroll to **Android TV OS build** and click it **7 times** to unlock
   Developer options.
3. **Settings → System → Developer options** → enable **Wireless debugging**.
4. On first connect, approve the on-screen **"Allow wireless debugging"** prompt
   (check *Always allow from this network*).

## Configuration

The integration auto-discovers the streamer over mDNS — usually it just appears
under **Settings → Devices & Services** as a discovered device.

To add it by hand:

1. **Settings → Devices & Services → Add Integration**.
2. Search **Google TV Streamer**.
3. Enter the device's host/IP (leave blank to rely on discovery) and submit.

## On-screen overlays (TvOverlay)

Overlays are rendered by the third-party **[TvOverlay](https://github.com/gugutab/TvOverlay)**
app running *on* the streamer, which exposes an HTTP REST API on port `5001`.
This integration only talks to that API — **it does not bundle or ship the app.**

### Why a patched build is needed

The only released TvOverlay build (v1.0.3 / versionCode 10030, Oct 2023) **crashes
on Android 14**: its foreground service declares no `foregroundServiceType`, which
is mandatory as of Android 14, so the REST server never starts. A **manifest-only**
patch (no code changes) fixes it. The full rationale, checksums, and a
reproducible rebuild recipe are in
**[`tools/tvoverlay-patched/REBUILD.md`](tools/tvoverlay-patched/REBUILD.md)**.

> The patched APK is for **your own device only** and is intentionally **not**
> committed to this repo. Build it yourself from the recipe, or patch a copy you
> obtained from TvOverlay's own releases.

### Install (one time)

```bash
adb connect <streamer-ip>:5555
adb uninstall com.tabdeveloper.tvoverlay        # only if the broken original is present
adb install TvOverlay-patched-signed.apk
adb shell appops set com.tabdeveloper.tvoverlay SYSTEM_ALERT_WINDOW allow
adb shell am start -n com.tabdeveloper.tvoverlay/.SetupActivity
```

**Manual step you can't automate over the network:** on the TV, open TvOverlay
once and approve its on-screen **"grant overlay access"** prompt with the remote.
After that the server listens on `http://<streamer-ip>:5001` and overlays render
over live content.

**Recommended:** whitelist TvOverlay from battery optimization so its server
survives display sleep:

```bash
adb shell dumpsys deviceidle whitelist +com.tabdeveloper.tvoverlay
```

### Sleep behavior & self-healing

When the display **sleeps**, Android tears down TvOverlay's foreground service and
its REST server stops listening; it comes back when the app is next foregrounded.
The integration **self-heals** this: on a connection failure it re-launches
TvOverlay over the ADB channel it already owns (returning you to your show with
**BACK**, never HOME), waits briefly, and retries the overlay call **once** — no
retry loops, and normal overlays over live playback are untouched. The
battery-optimization whitelist above makes the recovery path rarely fire at all.

## Entities

- `media_player.<device>` — playback state, position, and media info where the
  foreground app exposes a media session.
- `remote.<device>` — sends keyevents (D-pad, back/home, transport, volume, power).

## Services

| Service | What it does | Key fields |
|---|---|---|
| `google_tv_streamer.launch_app` | Launch an app by friendly name/package, or open a deep-link URL | `name` *or* `url` |
| `google_tv_streamer.send_key` | Send a remote key | `key` (friendly name or `KEYCODE_*`) |
| `google_tv_streamer.show_overlay` | Transient on-screen notification | `message` (req), `title`, `source`, `duration`, `image`, `corner`, `small_icon`, `small_icon_color` |
| `google_tv_streamer.show_fixed_notification` | Show/update a persistent corner badge | `id` (req), `message`, `icon`, `border_color`, `background_color`, `shape` |
| `google_tv_streamer.clear_fixed_notification` | Clear a persistent badge | `id` (req) |
| `google_tv_streamer.set_overlay` | Overlay-level visibility settings | `overlay_visibility` (0–95), `clock_overlay_visibility` (0–95), `hot_corner` |

The overlay services require TvOverlay installed and granted as above.

### Example automation

```yaml
# Flash a doorbell alert over whatever's playing on the TV
automation:
  - alias: "Doorbell → TV overlay"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_bell
        to: "on"
    action:
      - service: google_tv_streamer.show_overlay
        data:
          title: "Front door"
          message: "Someone's at the door"
          corner: top_end
          duration: 8
```

## Limitations

- **Titles/position are app-controlled.** Real in-app titles are reliable only
  on YouTube; position can be unreliable (e.g. Peacock). This is an Android
  media-session constraint — see the [capability matrix](#capability-matrix).
- **Overlays need TvOverlay** sideloaded and granted (above). Core control
  (remote, launch, now-playing) works without it.
- **HBO Max / Max** now-playing metadata is not yet characterized (pending).

## Development

The integration ships with tests that run under the HA test harness:

```bash
python -m pytest tests/
```

Overlay and ADB logic are split behind dependency-injection seams (an injectable
poster for the overlay HTTP client, an injectable shell runner for ADB) so the
core parsers and overlay retry/recover logic are unit-tested without a device.

## Credits

- On-screen overlays are powered by **[TvOverlay](https://github.com/gugutab/TvOverlay)**
  by gugutab. This project only calls its REST API; all overlay rendering is its work.

## License

Apache-2.0 — see [LICENSE](LICENSE).
