# Google TV Streamer

Deep control of the Google TV Streamer (2024, Android TV OS 14) over network ADB.

## Features

- mDNS auto-discovery (no fixed ADB port)
- Media player for playback state and position
- Remote control: D-pad, transport, volume, power
- App launching and deep links
- On-screen overlays via TvOverlay — rendered over live playback, self-healing across display sleep

## Setup

1. Enable Developer options and Wireless debugging on the streamer.
2. Install via HACS or manually, then add the integration (it auto-discovers).
3. For overlays only: sideload the patched TvOverlay app and grant it overlay
   access on the TV — see the README's "On-screen overlays" section.

## Notes

Real in-app titles are reliably available only from YouTube; other apps withhold
or genericize them (Android media-session limitation). See the README's capability
matrix for per-app detail.

## License

Apache-2.0
