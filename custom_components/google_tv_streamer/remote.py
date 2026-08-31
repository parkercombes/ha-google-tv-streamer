"""Remote platform for Google TV Streamer."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, KEY_COMMANDS
from .coordinator import GoogleTVStreamerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Google TV Streamer remote."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    adb = hass.data[DOMAIN][entry.entry_id]["adb"]
    async_add_entities([GoogleTVStreamerRemote(coordinator, adb, entry)])


class GoogleTVStreamerRemote(
    CoordinatorEntity[GoogleTVStreamerDataUpdateCoordinator], RemoteEntity
):
    """Remote entity backed by ADB key events."""

    _attr_has_entity_name = True
    _attr_name = "Remote"
    _attr_is_on = True

    def __init__(
        self,
        coordinator: GoogleTVStreamerDataUpdateCoordinator,
        adb: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the remote."""
        super().__init__(coordinator)
        self.adb = adb
        self._attr_unique_id = f"{entry.entry_id}_remote"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Google",
            "model": "Google TV Streamer (2024)",
        }

    async def async_send_command(
        self,
        command: Iterable[str] | str,
        **kwargs: Any,
    ) -> None:
        """Send one or more remote commands."""
        commands = [command] if isinstance(command, str) else list(command)
        for item in commands:
            keycode = KEY_COMMANDS.get(item, item)
            await self.hass.async_add_executor_job(self.adb.key_event, keycode)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wake or power-toggle the device."""
        await self.hass.async_add_executor_job(self.adb.key_event, KEY_COMMANDS["power"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Sleep or power-toggle the device."""
        await self.hass.async_add_executor_job(self.adb.key_event, KEY_COMMANDS["power"])
