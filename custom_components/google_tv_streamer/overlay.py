"""TvOverlay REST client for Google TV Streamer devices."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

Poster = Callable[[str, dict[str, Any]], Awaitable[int]]


class TvOverlayClient:
    """Async client for the TvOverlay HTTP API."""

    def __init__(
        self,
        host: str,
        port: int = 5001,
        session: Any | None = None,
        poster: Poster | None = None,
    ) -> None:
        """Create a TvOverlay client for host:port."""

        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session = session
        self._poster = poster
        self._owns_session = False

    async def notify(
        self,
        message: str,
        *,
        title: str | None = None,
        source: str | None = None,
        id: str | None = None,
        duration: int | None = None,
        image: str | None = None,
        video: str | None = None,
        large_icon: str | None = None,
        small_icon: str | None = None,
        small_icon_color: str | None = None,
        corner: str | None = None,
    ) -> int:
        """Show a transient TvOverlay notification."""

        payload = self._payload(
            {
                "id": id,
                "title": title,
                "message": message,
                "source": source,
                "duration": duration,
                "image": image,
                "video": video,
                "largeIcon": large_icon,
                "smallIcon": small_icon,
                "smallIconColor": small_icon_color,
                "corner": corner,
            }
        )
        return await self._post("/notify", payload)

    async def notify_fixed(
        self,
        *,
        id: str | None = None,
        message: str | None = None,
        icon: str | None = None,
        visible: bool = True,
        message_color: str | None = None,
        icon_color: str | None = None,
        border_color: str | None = None,
        background_color: str | None = None,
        shape: str | None = None,
        expiration: int | None = None,
    ) -> int:
        """Show or update a persistent TvOverlay corner badge."""

        payload = self._payload(
            {
                "id": id,
                "visible": visible,
                "icon": icon,
                "message": message,
                "messageColor": message_color,
                "iconColor": icon_color,
                "borderColor": border_color,
                "backgroundColor": background_color,
                "shape": shape,
                "expiration": expiration,
            }
        )
        return await self._post("/notify_fixed", payload)

    async def clear_fixed(self, id: str) -> int:
        """Clear a persistent TvOverlay badge by id."""

        return await self._post("/notify_fixed", {"id": id, "visible": False})

    async def set_overlay(
        self,
        *,
        clock_overlay_visibility: int | None = None,
        overlay_visibility: int | None = None,
        hot_corner: str | None = None,
    ) -> int:
        """Update TvOverlay overlay-level visibility settings."""

        payload = self._payload(
            {
                "clockOverlayVisibility": clock_overlay_visibility,
                "overlayVisibility": overlay_visibility,
                "hotCorner": hot_corner,
            }
        )
        return await self._post("/set/overlay", payload)

    async def close(self) -> None:
        """Close an aiohttp session owned by this client."""

        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._owns_session = False

    async def _post(self, path: str, payload: dict[str, Any]) -> int:
        """POST JSON to TvOverlay and return the HTTP status."""

        url = f"{self.base_url}{path}"
        if self._poster is not None:
            return await self._poster(url, payload)

        session = self._session
        if session is None:
            from aiohttp import ClientSession

            session = ClientSession()
            self._session = session
            self._owns_session = True

        async with session.post(url, json=payload) as response:
            return response.status

    @staticmethod
    def _payload(values: dict[str, Any]) -> dict[str, Any]:
        """Return a payload without null fields."""

        return {key: value for key, value in values.items() if value is not None}
