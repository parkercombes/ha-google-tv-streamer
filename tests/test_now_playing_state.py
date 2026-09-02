"""Regression tests for real-device now-playing playback states."""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.google_tv_streamer.adb import GoogleTVStreamerADB


FIXTURES = Path(__file__).parent / "fixtures"
NETFLIX_ACTIVITY = "  ResumedActivity: ActivityRecord{123 u0 com.netflix.ninja/.MainActivity t1}\n"
LAUNCHER_ACTIVITY = (
    "  ResumedActivity: ActivityRecord{123 u0 "
    "com.google.android.apps.tv.launcherx/.MainActivity t1}\n"
)


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("fixture_name", "expected_state"),
    [
        ("media_session_netflix_device_playing.txt", "playing"),
        ("media_session_netflix_device_paused.txt", "paused"),
        ("media_session_netflix_device_stopped.txt", "stopped"),
    ],
)
def test_now_playing_reports_real_netflix_device_playback_state(
    fixture_name: str,
    expected_state: str,
) -> None:
    def shell_runner(cmd: str) -> str:
        if cmd == "dumpsys media_session":
            return _read_fixture(fixture_name)
        if cmd == "dumpsys activity activities":
            return NETFLIX_ACTIVITY
        return ""

    streamer = GoogleTVStreamerADB(shell_runner=shell_runner)

    assert streamer.now_playing()["state"] == expected_state


def test_now_playing_does_not_report_launcher_home_stale_audio_as_playing() -> None:
    def shell_runner(cmd: str) -> str:
        if cmd == "dumpsys media_session":
            return _read_fixture("media_session_launcher_home_stale.txt")
        if cmd == "dumpsys activity activities":
            return LAUNCHER_ACTIVITY
        return ""

    streamer = GoogleTVStreamerADB(shell_runner=shell_runner)
    now_playing = streamer.now_playing()

    assert now_playing is None or now_playing["state"] != "playing"
