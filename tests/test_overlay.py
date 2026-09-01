"""Tests for the TvOverlay REST client."""

from __future__ import annotations

from typing import Any

from custom_components.google_tv_streamer.overlay import TvOverlayClient


SNAKE_CASE_KEYS = {
    "large_icon",
    "small_icon",
    "small_icon_color",
    "message_color",
    "icon_color",
    "border_color",
    "background_color",
    "clock_overlay_visibility",
    "overlay_visibility",
    "hot_corner",
}


class FakePoster:
    """Record injected POST calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def __call__(self, url: str, payload: dict[str, Any]) -> int:
        self.calls.append((url, payload))
        return 204


class SequencePoster:
    """Return or raise configured outcomes for each POST call."""

    def __init__(self, outcomes: list[int | BaseException]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def __call__(self, url: str, payload: dict[str, Any]) -> int:
        self.calls.append((url, payload))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class RecoverSpy:
    """Record recover calls."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self) -> None:
        self.calls += 1


def assert_no_snake_case_or_none(payload: dict[str, Any]) -> None:
    """Assert TvOverlay payloads use only API field names with no null values."""

    assert not (set(payload) & SNAKE_CASE_KEYS)
    assert all(value is not None for value in payload.values())


async def test_notify_posts_camel_case_payload_without_nulls() -> None:
    """Notify posts to /notify with TvOverlay camelCase keys."""

    poster = FakePoster()
    client = TvOverlayClient("192.0.2.10", poster=poster)

    status = await client.notify(
        "Door opened",
        title="Front Door",
        small_icon_color="#FF00AA",
        small_icon=None,
    )

    assert status == 204
    assert poster.calls == [
        (
            "http://192.0.2.10:5001/notify",
            {
                "title": "Front Door",
                "message": "Door opened",
                "smallIconColor": "#FF00AA",
            },
        )
    ]
    assert_no_snake_case_or_none(poster.calls[0][1])


async def test_notify_fixed_posts_camel_case_payload_with_visible() -> None:
    """Fixed notifications always include visible and omit null fields."""

    poster = FakePoster()
    client = TvOverlayClient("192.0.2.10", port=5010, poster=poster)

    status = await client.notify_fixed(
        id="badge-1",
        background_color="#66000000",
        border_color="#FFFFFF",
        icon=None,
    )

    assert status == 204
    assert poster.calls == [
        (
            "http://192.0.2.10:5010/notify_fixed",
            {
                "id": "badge-1",
                "visible": True,
                "borderColor": "#FFFFFF",
                "backgroundColor": "#66000000",
            },
        )
    ]
    assert_no_snake_case_or_none(poster.calls[0][1])


async def test_clear_fixed_posts_visible_false_with_id() -> None:
    """Clearing a fixed notification posts visible false for the id."""

    poster = FakePoster()
    client = TvOverlayClient("192.0.2.10", poster=poster)

    status = await client.clear_fixed("badge-1")

    assert status == 204
    assert poster.calls == [
        (
            "http://192.0.2.10:5001/notify_fixed",
            {"id": "badge-1", "visible": False},
        )
    ]
    assert_no_snake_case_or_none(poster.calls[0][1])


async def test_set_overlay_posts_camel_case_payload_without_nulls() -> None:
    """Overlay settings post to /set/overlay with TvOverlay camelCase keys."""

    poster = FakePoster()
    client = TvOverlayClient("192.0.2.10", poster=poster)

    status = await client.set_overlay(overlay_visibility=80, hot_corner=None)

    assert status == 204
    assert poster.calls == [
        (
            "http://192.0.2.10:5001/set/overlay",
            {"overlayVisibility": 80},
        )
    ]
    assert_no_snake_case_or_none(poster.calls[0][1])


async def test_connection_failure_recovers_once_then_retries_successfully() -> None:
    """A connection failure revives TvOverlay and retries the POST once."""

    poster = SequencePoster([ConnectionError("refused"), 200])
    recover = RecoverSpy()
    client = TvOverlayClient("192.0.2.10", poster=poster, recover=recover)

    status = await client.notify("Door opened")

    assert status == 200
    assert recover.calls == 1
    assert len(poster.calls) == 2


async def test_healthy_post_does_not_recover() -> None:
    """A successful POST does not run the recovery callback."""

    poster = SequencePoster([200])
    recover = RecoverSpy()
    client = TvOverlayClient("192.0.2.10", poster=poster, recover=recover)

    status = await client.notify("Door opened")

    assert status == 200
    assert recover.calls == 0
    assert len(poster.calls) == 1


async def test_repeated_connection_failure_recovers_at_most_once() -> None:
    """Repeated connection failures surface after one recovery attempt."""

    poster = SequencePoster([ConnectionError("refused"), ConnectionError("still refused")])
    recover = RecoverSpy()
    client = TvOverlayClient("192.0.2.10", poster=poster, recover=recover)

    try:
        await client.notify("Door opened")
    except ConnectionError as err:
        assert str(err) == "still refused"
    else:
        raise AssertionError("ConnectionError was not raised")

    assert recover.calls == 1
    assert len(poster.calls) == 2
