"""ADB parsing and command helpers for Google TV Streamer integrations."""

from __future__ import annotations

import re
import shlex
from collections.abc import Callable


_STATE_MAP = {
    "PLAYING": "playing",
    "PAUSED": "paused",
    "STOPPED": "stopped",
    "BUFFERING": "buffering",
    "NONE": "none",
    "ERROR": "none",
}

_UNRELIABLE_POSITION_THRESHOLD_MS = 86_400_000
TVOVERLAY_PACKAGE = "com.tabdeveloper.tvoverlay"
TVOVERLAY_SETUP_ACTIVITY = f"{TVOVERLAY_PACKAGE}/.SetupActivity"


def _none_if_null(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value == "" or value == "null":
        return None
    return value


def _session_blocks(text: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"(?m)^    \S.*\(userId=\d+\)\s*$", text)]
    blocks: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        blocks.append(text[start:end])
    return blocks


def parse_active_media_session(text: str) -> dict | None:
    """Return the active, real media-app session parsed from dumpsys media_session.

    Bluetooth and inactive sessions are ignored. The result is intentionally
    limited to fields that are present in the raw media session dump.
    """

    for block in _session_blocks(text):
        package_match = re.search(r"(?m)^\s+package=([^\s]+)\s*$", block)
        if not package_match:
            continue
        package = package_match.group(1)
        if package == "com.google.android.bluetooth":
            continue
        if not re.search(r"(?m)^\s+active=true\s*$", block):
            continue

        state_match = re.search(
            r"state=PlaybackState \{state=([A-Z]+)\(\d+\), position=(-?\d+), .*?actions=(\d+)",
            block,
        )
        if not state_match:
            continue

        raw_state, raw_position, raw_actions = state_match.groups()
        position_ms = int(raw_position)
        title: str | None = None
        subtitle: str | None = None

        metadata_match = re.search(r"(?m)^\s+metadata:\s*(.*)$", block)
        if metadata_match:
            metadata = metadata_match.group(1).strip()
            if metadata != "null":
                description_match = re.search(r"description=(.*)$", metadata)
                if description_match:
                    fields = [field.strip() for field in description_match.group(1).split(",")]
                    if fields:
                        title = _none_if_null(fields[0])
                    if len(fields) > 1:
                        subtitle = _none_if_null(fields[1])

        return {
            "package": package,
            "state": _STATE_MAP.get(raw_state, "none"),
            "position_ms": position_ms,
            "actions": int(raw_actions),
            "title": title,
            "subtitle": subtitle,
            "position_reliable": position_ms <= _UNRELIABLE_POSITION_THRESHOLD_MS,
        }

    return None


def parse_audio_owner(text: str) -> list[str]:
    """Return packages from the Audio playback section, current owner first."""

    marker = "Audio playback (lastly played comes first)"
    _, separator, section = text.partition(marker)
    if not separator:
        return []

    owners: list[str] = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = re.search(r"\bpackages=([^\s]+)", line)
        if match:
            owners.extend(package for package in match.group(1).split(",") if package)
    return owners


def parse_resumed_activity(text: str) -> str | None:
    """Return the foreground package from dumpsys activity activities.

    ResumedActivity is the reliable foreground signal; dumpsys window
    mCurrentFocus is unreliable because some full-screen players, including
    Dropout, do not hold window focus.
    """

    match = re.search(r"(?m)^\s*ResumedActivity:.*?\s([A-Za-z0-9_.]+(?:\.[A-Za-z0-9_]+)+)/", text)
    if not match:
        return None
    return match.group(1)


class GoogleTVStreamerADB:
    """Thin ADB shell-command wrapper with injectable transport.

    The class builds Android shell commands and parses their output. It does
    not know how a device is connected; callers provide a shell_runner that
    accepts a command string and returns stdout text.
    """

    def __init__(self, shell_runner: Callable[[str], str] | None = None) -> None:
        """Create a client using shell_runner for command execution."""

        self._shell_runner = shell_runner

    def _run(self, cmd: str) -> str:
        if self._shell_runner is None:
            raise RuntimeError("GoogleTVStreamerADB requires an injected shell_runner")
        return self._shell_runner(cmd)

    def current_app(self) -> str | None:
        """Return the package name of the resumed foreground activity."""

        return parse_resumed_activity(self._run("dumpsys activity activities"))

    def now_playing(self) -> dict | None:
        """Return active media session data, falling back to audio ownership.

        Apps such as Dropout may play audio without exposing a media session.
        In that case, the current audio owner is returned with unknown session
        fields rather than inventing playback metadata.
        """

        output = self._run("dumpsys media_session")
        session = parse_active_media_session(output)
        if session is not None:
            return session

        owners = parse_audio_owner(output)
        if not owners:
            return None
        return {
            "package": owners[0],
            "state": "playing",
            "position_ms": None,
            "actions": 0,
            "title": None,
            "subtitle": None,
            "position_reliable": False,
        }

    def launch_deeplink(self, url: str) -> str:
        """Open a deep link URL through Android's VIEW intent."""

        cmd = f"am start -a android.intent.action.VIEW -d {shlex.quote(url)}"
        return self._run(cmd)

    def key_event(self, keycode: str) -> str:
        """Send an Android input keyevent by keycode or key name."""

        return self._run(f"input keyevent {shlex.quote(keycode)}")

    def restart_overlay_app(self) -> None:
        """Bring TvOverlay foreground briefly so Android restarts its HTTP server.

        Uses BACK (not HOME) to dismiss the setup screen so the device returns to
        whatever was in front — the show the user was watching — rather than
        dropping them on the launcher. This only runs as a fallback when the
        server is found down (e.g. after the display slept); in normal use the
        server stays up and overlays render over live content untouched.
        """

        self._run(f"am start -n {shlex.quote(TVOVERLAY_SETUP_ACTIVITY)}")
        self._run("input keyevent KEYCODE_BACK")
