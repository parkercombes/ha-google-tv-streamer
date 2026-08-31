# Google TV Streamer Integration

Home Assistant integration for deep control of the Google TV Streamer (2024, Android TV OS 14) over network ADB.

## Features

- mDNS auto-discovery of the Google TV Streamer (no fixed ADB port needed)
- Media player entity for playback state and position
- Remote control via keyevents
- App launching via deep links
- On-screen notifications via TvOverlay integration
- Honest per-app capability matrix (see below)

## Requirements

- Home Assistant Core 2023.1 or later
- Google TV Streamer (2024 model) with Android TV OS 14
- Developer options enabled on the device (USB debugging and Wireless debugging)
- HACS (for easy installation) or manual copy

## Capability Matrix

Capabilities are app-dependent. The table below reflects measured results on a real device (2026-08-31).

| App | Detect app | Play/Pause state | Position | Transport | Real title |
|-----|------------|------------------|----------|-----------|------------|
| YouTube (com.google.android.youtube.tv) | YES | YES | YES | full | YES (title + uploader) |
| Netflix (com.netflix.ninja) | YES | YES | YES | full | NO |
| Prime Video (com.amazon.amazonvideo.livingroom) | YES | YES | YES | full | NO (generic 'PrimeVideo') |
| Peacock (com.peacocktv.peacockandroid) | YES | YES | UNRELIABLE | limited | NO |
| Dropout (com.collegehumor.chdropout) | YES (via resumed-activity + audio-owner) | NO | NO | keyevents only | NO |
| HBO Max / Max (com.wbd.stream) | Listed | Pending | Pending | Pending | Pending |

**Note:** Real in-app content titles are the exception; only YouTube reliably provides them. Other apps may withhold or genericize the title.

## Installation

### Via HACS (Recommended)
1. Add this repository as a custom repository in HACS:
   - Category: Integration
   - Repository URL: `<your-repository-url>`
2. Install the "Google TV Streamer" integration from HACS.
3. Restart Home Assistant.

### Manual Install
1. Copy the `custom_components/google_tv_streamer` directory to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Enabling ADB on the Google TV Streamer

1. Go to **Settings > System > About**.
2. Scroll to **Android TV OS build** and tap it 7 times to enable Developer options.
3. Go back to **Settings > System > Developer options**.
4. Enable **USB debugging** and **Wireless debugging**.
5. On first connect, approve the on-screen "Allow USB debugging" prompt.

## Configuration

The integration uses mDNS auto-discovery to find the Google TV Streamer. No manual configuration is required for discovery.

To manually add by host:
1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for "Google TV Streamer".
3. Enter the host IP address (or leave blank for auto-discovery).
4. Submit.

## Entities

- `media_player.<device_name>`: Provides playback state, position, and media control.
- `remote.<device_name>`: Sends keyevents to the device.

## Services

- `google_tv_streamer.launch_app`: Launch an app by its package name.
  - Data: `entity_id` (optional), `app_package` (required)
- `google_tv_streamer.send_key`: Send a keyevent to the device.
  - Data: `entity_id` (optional), `key` (required, e.g., "HOME", "BACK", "DPAD_UP")
- `google_tv_streamer.notify`: Send an on-screen notification via TvOverlay.
  - Requires the TvOverlay app installed and configured on the device.
  - Data: `entity_id` (optional), `title`, `message`, `timeout` (optional, seconds)

## Limitations / Why Some Apps Show No Title

- The integration relies on Android's media session API for playback state and position.
- Real-time in-app content titles are only available when the app exposes them via the media session metadata.
- YouTube is the only app tested that reliably provides title and uploader.
- Netflix, Prime Video, Peacock, and Dropout either withhold the title or provide only a generic string.
- Position reporting may be unreliable in some apps (e.g., Peacock) due to incomplete media session updates.
- Transport controls vary by app; some apps only accept keyevents (limited transport).

## License

This integration is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.