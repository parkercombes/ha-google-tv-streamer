# ha-google-tv-streamer — Claude working rules

A HACS custom integration for deep control of the Google TV Streamer (2024) over plain
network ADB. It covers the foreground app, real now-playing state, deep-link launch and
remote keys, plus on-screen overlays driven through the TvOverlay app's HTTP API.
The repo is **public** (github.com/parkercombes/ha-google-tv-streamer), and Bill's HA consumes it through HACS.

Read first: [docs/DESIGN.md](docs/DESIGN.md) (how it works and why) ·
[docs/DEPLOY.md](docs/DEPLOY.md) (release + deploy) ·
[docs/AUTOMATION-NOTES.md](docs/AUTOMATION-NOTES.md) (driving the streamer from automations) ·
[docs/ROADMAP.md](docs/ROADMAP.md) (open items) ·
[tools/tvoverlay-patched/REBUILD.md](tools/tvoverlay-patched/REBUILD.md) (the APK patch).

## Hard rules
- **Public repo: no private data.** No LAN IPs, tokens, device_ids, or household names.
  Use `<streamer-ip>` in examples.
- **Never commit or redistribute the TvOverlay APK.** `*.apk` is gitignored, and only the rebuild
  recipe is public.
- **Mocked tests are not proof.** Config-flow and now-playing bugs twice passed the mocked
  harness and failed on hardware. Every behavior change needs a real-device fixture or a
  live check. Capture fixtures from the real device (`dumpsys media_session`, `dumpsys activity`).
- **Never press HOME in automatic recovery.** It throws the viewer out of their show.
  Recovery uses BACK.
- **Don't guess app package names.** Test-launch each one. The confirmed IDs are in DESIGN.md.
- **Disruptive live tests need Bill's OK.** Anything that interrupts what's on the TV counts:
  force-stop, sleep, launch.

## Dev
- Tests: `python -m pytest tests/` needs the HA 2024.3.3 test deps from `requirements_test.txt`.
  Those deps aren't installed globally on the Mac, so use a venv.
- Ringer-built. Route multi-step changes through Ringer and add a regression test with each fix.
- A version bump goes in `custom_components/google_tv_streamer/manifest.json`, followed by an
  annotated tag `vX.Y.Z` on the merge commit.
- **Deploying new code needs a full HA restart.** Reloading the config entry keeps the
  stale Python module loaded. See DEPLOY.md.
