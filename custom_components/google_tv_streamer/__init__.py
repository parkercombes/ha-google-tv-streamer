"""Google TV Streamer integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import APP_PACKAGES, CONF_HOST, CONF_PORT, DOMAIN, KEY_COMMANDS, PLATFORMS
from .coordinator import GoogleTVStreamerDataUpdateCoordinator
from .transport import connect_streamer

PLATFORM_TYPES = [Platform(platform) for platform in PLATFORMS]

LAUNCH_APP_SCHEMA = vol.Schema(
    {
        vol.Optional("name"): cv.string,
        vol.Optional("url"): cv.string,
    }
)

SEND_KEY_SCHEMA = vol.Schema({vol.Required("key"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google TV Streamer from a config entry."""
    adb = await hass.async_add_executor_job(
        connect_streamer,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT),
    )
    coordinator = GoogleTVStreamerDataUpdateCoordinator(hass, adb, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "adb": adb,
        "coordinator": coordinator,
    }

    async def async_launch_app(call: ServiceCall) -> None:
        name = call.data.get("name")
        url = call.data.get("url")
        target = url or APP_PACKAGES.get(name or "", name)
        if target:
            await hass.async_add_executor_job(adb.launch_deeplink, target)

    async def async_send_key(call: ServiceCall) -> None:
        key = call.data["key"]
        keycode = KEY_COMMANDS.get(key, key)
        await hass.async_add_executor_job(adb.key_event, keycode)

    hass.services.async_register(DOMAIN, "launch_app", async_launch_app, schema=LAUNCH_APP_SCHEMA)
    hass.services.async_register(DOMAIN, "send_key", async_send_key, schema=SEND_KEY_SCHEMA)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM_TYPES)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Google TV Streamer config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORM_TYPES)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "launch_app")
            hass.services.async_remove(DOMAIN, "send_key")
    return unloaded
