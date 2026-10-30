"""Position anchors must be projected with Android's monotonic clock."""

import pytest
from custom_components.google_tv_streamer.adb import GoogleTVStreamerADB


def session(state="PLAYING", position=10000, speed=1.0, updated=90000, uptime="100.0"):
    return f"""{uptime} 100.0
  Media button session is com.amazon.amazonvideo.livingroom/x
    com.amazon.amazonvideo.livingroom x (userId=0)
      package=com.amazon.amazonvideo.livingroom
      active=true
      state=PlaybackState {{state={state}(3), position={position}, buffered position=0, speed={speed}, updated={updated}, actions=1049455}}
      metadata: size=7, description=PrimeVideo, null, null
"""


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, 20000),
        ({"state": "PAUSED", "speed": 0.0}, 10000),
        ({"updated": 110000}, 10000),
        ({"updated": 0}, 10000),
        ({"speed": 2.0}, 30000),
        ({"uptime": "invalid"}, 10000),
        ({"position": -1}, -1),
    ],
)
def test_position_anchor(options, expected):
    player = GoogleTVStreamerADB(shell_runner=lambda cmd: session(**options))
    result = player.now_playing()
    assert result["position_ms"] == expected
    assert result["position_reliable"] == (expected >= 0)


def test_advances_then_resynchronizes_on_pause_and_seek():
    snapshots = iter(
        [
            session(),
            session(uptime="105.0"),
            session(state="PAUSED", position=25000, updated=105000, uptime="110.0"),
            session(position=60000, updated=110000, uptime="111.0"),
        ]
    )
    player = GoogleTVStreamerADB(shell_runner=lambda cmd: next(snapshots))
    assert [player.now_playing()["position_ms"] for _ in range(4)] == [
        20000,
        25000,
        25000,
        61000,
    ]


def test_entity_exposes_matching_sample_timestamp():
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from custom_components.google_tv_streamer.media_player import (
        GoogleTVStreamerMediaPlayer,
    )

    sampled_at = datetime(2026, 10, 30, tzinfo=timezone.utc)
    entity = GoogleTVStreamerMediaPlayer.__new__(GoogleTVStreamerMediaPlayer)
    entity.coordinator = SimpleNamespace(
        data={
            "now_playing": {"position_ms": 20000, "position_reliable": True},
            "position_updated_at": sampled_at,
        }
    )
    assert entity.media_position == 20
    assert entity.media_position_updated_at == sampled_at
    entity.coordinator.data["now_playing"]["position_reliable"] = False
    assert entity.media_position is None
    assert entity.media_position_updated_at is None
