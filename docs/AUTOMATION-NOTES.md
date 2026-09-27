# Driving the streamer from automations — gotchas

Learned while building a voice "movie scene" automation. It turns the lights down, closes
the curtains and plays a specific Netflix title.

## Waking and launching

- **The streamer sleeps.** Send `KEYCODE_WAKEUP` first. `send_key` passes raw
  `KEYCODE_*` names straight through. Waking the streamer also powers the TV on over HDMI-CEC.
- **Waking races the launcher.** For about 6 seconds after wake,
  `com.google.android.apps.tv.launcherx/.coreservices.bootmode.DispatchActivity` holds the
  foreground, and an app launched in that window gets bumped. Wait about 10 seconds before launching.
- **Blind key presses depend on state.** DPAD_CENTER plays on a details page but toggles
  pause inside the player, and `KEYCODE_MEDIA_PLAY` also toggles.

## Netflix specifically

- **Deep links don't auto-play.** `https://www.netflix.com/watch/<id>` opens the title page,
  so a Play press (`select`) is needed afterwards.
- **Deep links only work on a cold start.** If Netflix's task already exists, `am start`
  delivers to the running instance and ignores the link, even with NEW_TASK|CLEAR_TOP or
  after HOME.
- **The profile picker drops the pending deep link.** A cold start with a link still lands
  on the chosen profile's *home* screen after the "Who's watching?" selection. **Unsolved.**
  Ideas still to try:
  - select the profile faster (about 5 s);
  - use `/title/<id>` instead of `/watch/<id>`;
  - use the `nflx://` scheme or intent extras;
  - route through the Google TV Assistant search intent instead.
- **Netflix is fully FLAG_SECURE.** `screencap` returns 0 bytes for the whole app, and
  `uiautomator dump` has no labels, so navigation is blind and a human has to confirm what's on screen.
- **The media session gives a false signal:** the Netflix home screen auto-plays a trailer that
  reports `PLAYING`. A "playing" session doesn't prove the chosen title is playing.
- **There's no force-stop service.** A deterministic cold start would need a new service,
  which means a code change and a full-restart redeploy.
