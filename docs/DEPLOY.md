# Release and deploy

## Release

1. Fix the problem on a branch and add a **real-device** regression fixture or test. Open a PR and merge it.
2. Bump `version` in `custom_components/google_tv_streamer/manifest.json`.
3. Tag the merge commit: `git tag -a vX.Y.Z <commit> -m "..."`, then push the branch and tag.
   HACS tracks the default branch (there's no `zip_release`), so the tag records the
   version rather than gating the install. Creating a GitHub Release object isn't
   required.

## Deploy to a running Home Assistant

1. In **HACS → Google TV Streamer → ⋮ → Redownload**, pick the latest version. Only the UI
   forces the re-scan; `update_entity` and a HACS reload don't pull new code.
2. **Fully restart Home Assistant.** `homeassistant.reload_config_entry` is *not* enough,
   because Python keeps the old module cached and the entry re-sets-up on stale code.
3. After the restart, wait about 25 seconds before polling `/api/`. An early check can hit
   the old process that is still up and report a false "back already".
4. **Verify against the device:** run a live `dumpsys` through the repo's `adb.py` and compare
   the result with what the `media_player` entity reports. The two must match. For example,
   with the streamer on the screensaver the entity must read `idle`, not `playing`.

## First install

Add the repo to HACS as a custom repository, download it, restart HA and add the
integration by host on port 5555 (see the README). Then accept the "Allow wireless debugging"
prompt on the TV.
