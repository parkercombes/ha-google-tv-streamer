"""Unit tests for the injectable ADB transport."""

from __future__ import annotations

from pathlib import Path

from custom_components.google_tv_streamer.transport import connect_streamer


FIXTURES = Path(__file__).parent / "fixtures"


class FakeDevice:
    """Small adb-shell stand-in used by the transport injection seam."""

    def __init__(self, responses: dict[str, str]) -> None:
        self.connected = False
        self.closed = False
        self.commands: list[str] = []
        self.responses = responses

    def connect(self, *args, **kwargs) -> bool:
        self.connected = True
        return True

    def shell(self, cmd: str) -> str:
        self.commands.append(cmd)
        return self.responses.get(cmd, "")

    def close(self) -> None:
        self.closed = True


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_connect_streamer_parses_now_playing_and_current_app() -> None:
    fake_device = FakeDevice(
        {
            "dumpsys media_session": _read_fixture("media_session_prime.txt"),
            "dumpsys activity activities": _read_fixture("activities_prime.txt"),
        }
    )

    streamer = connect_streamer(
        "streamer.local",
        device_factory=lambda host, port: fake_device,
    )

    assert fake_device.connected is True
    assert streamer.current_app() == "com.amazon.amazonvideo.livingroom"
    assert streamer.now_playing() == {
        "package": "com.amazon.amazonvideo.livingroom",
        "state": "playing",
        "position_ms": 16016,
        "actions": 1049455,
        "title": "PrimeVideo",
        "subtitle": None,
        "position_reliable": True,
    }


def test_commands_are_sent_through_injected_device() -> None:
    fake_device = FakeDevice({})
    streamer = connect_streamer(
        "192.0.2.10",
        port=5555,
        device_factory=lambda host, port: fake_device,
    )

    streamer.launch_deeplink("https://example.com/watch?id=abc")
    streamer.key_event("KEYCODE_MEDIA_PLAY_PAUSE")

    assert fake_device.commands == [
        "am start -a android.intent.action.VIEW -d 'https://example.com/watch?id=abc'",
        "input keyevent KEYCODE_MEDIA_PLAY_PAUSE",
    ]


def test_now_playing_falls_back_to_audio_owner() -> None:
    fake_device = FakeDevice(
        {
            "dumpsys media_session": _read_fixture("media_session_dropout.txt"),
            "dumpsys activity activities": _read_fixture("activities_dropout.txt"),
        }
    )

    streamer = connect_streamer("streamer.local", device_factory=lambda host, port: fake_device)

    assert streamer.current_app() == "com.collegehumor.chdropout"
    assert streamer.now_playing() == {
        "package": "com.collegehumor.chdropout",
        "state": "playing",
        "position_ms": None,
        "actions": 0,
        "title": None,
        "subtitle": None,
        "position_reliable": False,
    }
