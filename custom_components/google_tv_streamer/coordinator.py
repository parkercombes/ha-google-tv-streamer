"""Data coordinator for Google TV Streamer."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .adb import GoogleTVStreamerADB
from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=10)


class GoogleTVStreamerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll Google TV Streamer state over ADB."""

    def __init__(
        self,
        hass: HomeAssistant,
        adb: GoogleTVStreamerADB,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=None,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=SCAN_INTERVAL,
        )
        self.adb = adb
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest streamer state."""
        current_app = await self.hass.async_add_executor_job(self.adb.current_app)
        now_playing = await self.hass.async_add_executor_job(self.adb.now_playing)
        return {
            "current_app": current_app,
            "now_playing": now_playing,
        }
