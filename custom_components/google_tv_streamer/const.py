"""Constants for the Google TV Streamer integration."""

from __future__ import annotations

DOMAIN = "google_tv_streamer"
DEFAULT_PORT = 5555

APP_PACKAGES = {
    "Netflix": "com.netflix.ninja",
    "YouTube": "com.google.android.youtube.tv",
    "HBO Max": "com.wbd.stream",
    "Max": "com.wbd.stream",
    "Dropout": "com.collegehumor.chdropout",
    "Peacock": "com.peacocktv.peacockandroid",
    "Prime Video": "com.amazon.amazonvideo.livingroom",
}

KEY_COMMANDS = {
    "up": "KEYCODE_DPAD_UP",
    "down": "KEYCODE_DPAD_DOWN",
    "left": "KEYCODE_DPAD_LEFT",
    "right": "KEYCODE_DPAD_RIGHT",
    "select": "KEYCODE_DPAD_CENTER",
    "back": "KEYCODE_BACK",
    "home": "KEYCODE_HOME",
    "play_pause": "KEYCODE_MEDIA_PLAY_PAUSE",
    "volume_up": "KEYCODE_VOLUME_UP",
    "volume_down": "KEYCODE_VOLUME_DOWN",
    "power": "KEYCODE_POWER",
}

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SERIAL = "serial"

PLATFORMS = ["media_player", "remote"]
