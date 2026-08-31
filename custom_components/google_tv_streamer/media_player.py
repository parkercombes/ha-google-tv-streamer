"""Media player platform for Google TV Streamer."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_PACKAGES, DOMAIN, KEY_COMMANDS
from .coordinator import GoogleTVStreamerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Google TV Streamer media player."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    adb = hass.data[DOMAIN][entry.entry_id]["adb"]
    async_add_entities([GoogleTVStreamerMediaPlayer(coordinator, adb, entry)])


class GoogleTVStreamerMediaPlayer(
    CoordinatorEntity[GoogleTVStreamerDataUpdateCoordinator], MediaPlayerEntity
):
    """Media player entity backed by Google TV Streamer ADB state."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self,
        coordinator: GoogleTVStreamerDataUpdateCoordinator,
        adb: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.adb = adb
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Google",
            "model": "Google TV Streamer (2024)",
        }
        self._attr_available = True
        self._host = entry.data.get(CONF_HOST)

    @property
    def state(self) -> MediaPlayerState | None:
        """Return playback state."""
        media = self._media
        if not media:
            return MediaPlayerState.IDLE
        state = str(media.get("state", "")).lower()
        if state in {"playing", "play"}:
            return MediaPlayerState.PLAYING
        if state in {"paused", "pause"}:
            return MediaPlayerState.PAUSED
        if state in {"stopped", "stop"}:
            return MediaPlayerState.IDLE
        return MediaPlayerState.ON

    @property
    def source(self) -> str | None:
        """Return the active app package."""
        media = self._media
        if media and media.get("package"):
            return media["package"]
        return self.coordinator.data.get("current_app")

    @property
    def source_list(self) -> list[str]:
        """Return selectable app names."""
        return list(APP_PACKAGES)

    @property
    def media_title(self) -> str | None:
        """Return the current media title."""
        media = self._media
        return None if not media else media.get("title")

    @property
    def media_artist(self) -> str | None:
        """Return the current media subtitle."""
        media = self._media
        return None if not media else media.get("subtitle")

    @property
    def media_position(self) -> float | None:
        """Return the current position in seconds."""
        media = self._media
        if not media or not media.get("position_reliable"):
            return None
        position_ms = media.get("position_ms")
        return None if position_ms is None else position_ms / 1000

    async def async_media_play(self) -> None:
        """Send play/pause key event."""
        await self.hass.async_add_executor_job(self.adb.key_event, KEY_COMMANDS["play_pause"])

    async def async_media_pause(self) -> None:
        """Send play/pause key event."""
        await self.hass.async_add_executor_job(self.adb.key_event, KEY_COMMANDS["play_pause"])

    async def async_media_stop(self) -> None:
        """Send stop key event."""
        await self.hass.async_add_executor_job(self.adb.key_event, "KEYCODE_MEDIA_STOP")

    async def async_select_source(self, source: str) -> None:
        """Launch a known app by friendly name or package id."""
        target = APP_PACKAGES.get(source, source)
        await self.hass.async_add_executor_job(self.adb.launch_deeplink, target)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return integration-specific attributes."""
        return {
            "host": self._host,
            "current_app": self.coordinator.data.get("current_app"),
            "actions": (self._media or {}).get("actions"),
            "package": (self._media or {}).get("package"),
        }

    @property
    def _media(self) -> dict[str, Any] | None:
        """Return now playing data."""
        return (self.coordinator.data or {}).get("now_playing")
