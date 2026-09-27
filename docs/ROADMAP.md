# Roadmap

## Done
- **v0.1.0:**
  - ADB parsers, transport, HA wiring, TvOverlay client + self-heal.
  - Verified the Android 14 TvOverlay patch recipe.
  - Proved all four pillars (launch, now-playing, remote, overlays) live.
- **Config flow hardened on real HA:** zeroconf removed (TLS port), `cannot_connect`
  handling, and a 30 s auth window.
- **v0.1.1:** now-playing honors `PlaybackState` even when `active=false`.
- **v0.1.2:** the home-screen launcher is no longer reported as `playing`. Deployed and live-verified.

## Open
1. **Netflix deep-link through the profile gate** so a scene can play a specific title.
   See AUTOMATION-NOTES.md for the ideas still to try. A force-stop service may be needed.
2. **Voice acceptance test** of the movie-scene automation once item 1 is solved.
3. **Live-verify the BACK-based overlay revive** after a natural display sleep. This was
   deferred because it interrupts viewing.
4. **Auto-discovery:** support ADB-over-TLS, or add a discover-then-confirm-on-5555 flow.
5. **Restore the real `ZeroconfServiceInfo` type hint** if discovery returns. It's cosmetic.
6. **Register in the HACS default repository** when ready.
7. **Watch the screensaver package** (`dreamx`) in case it ever appears in the audio-owner list.
