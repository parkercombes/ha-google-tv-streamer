"""Google TV Streamer integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    APP_PACKAGES,
    CONF_HOST,
    CONF_OVERLAY_PORT,
    CONF_PORT,
    DEFAULT_OVERLAY_PORT,
    DOMAIN,
    KEY_COMMANDS,
    PLATFORMS,
)
from .coordinator import GoogleTVStreamerDataUpdateCoordinator
from .overlay import TvOverlayClient
from .transport import connect_streamer

PLATFORM_TYPES = [Platform(platform) for platform in PLATFORMS]

LAUNCH_APP_SCHEMA = vol.Schema(
    {
        vol.Optional("name"): cv.string,
        vol.Optional("url"): cv.string,
    }
)

SEND_KEY_SCHEMA = vol.Schema({vol.Required("key"): cv.string})

SHOW_OVERLAY_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("source"): cv.string,
        vol.Optional("duration"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("image"): cv.string,
        vol.Optional("corner"): vol.In(["bottom_start", "bottom_end", "top_start", "top_end"]),
        vol.Optional("small_icon"): cv.string,
        vol.Optional("small_icon_color"): cv.string,
    }
)

SHOW_FIXED_NOTIFICATION_SCHEMA = vol.Schema(
    {
        vol.Required("id"): cv.string,
        vol.Optional("message"): cv.string,
        vol.Optional("icon"): cv.string,
        vol.Optional("border_color"): cv.string,
        vol.Optional("background_color"): cv.string,
        vol.Optional("shape"): vol.In(["circle", "rounded", "rectangular"]),
    }
)

CLEAR_FIXED_NOTIFICATION_SCHEMA = vol.Schema({vol.Required("id"): cv.string})

SET_OVERLAY_SCHEMA = vol.Schema(
    {
        vol.Optional("overlay_visibility"): vol.All(vol.Coerce(int), vol.Range(min=0, max=95)),
        vol.Optional("clock_overlay_visibility"): vol.All(vol.Coerce(int), vol.Range(min=0, max=95)),
        vol.Optional("hot_corner"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google TV Streamer from a config entry."""
    adb = await hass.async_add_executor_job(
        connect_streamer,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT),
    )
    coordinator = GoogleTVStreamerDataUpdateCoordinator(hass, adb, entry)
    await coordinator.async_config_entry_first_refresh()
    overlay = TvOverlayClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_OVERLAY_PORT, DEFAULT_OVERLAY_PORT),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "adb": adb,
        "coordinator": coordinator,
        "overlay": overlay,
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

    async def async_show_overlay(call: ServiceCall) -> None:
        await overlay.notify(
            call.data["message"],
            title=call.data.get("title"),
            source=call.data.get("source"),
            duration=call.data.get("duration"),
            image=call.data.get("image"),
            corner=call.data.get("corner"),
            small_icon=call.data.get("small_icon"),
            small_icon_color=call.data.get("small_icon_color"),
        )

    async def async_show_fixed_notification(call: ServiceCall) -> None:
        await overlay.notify_fixed(
            id=call.data["id"],
            message=call.data.get("message"),
            icon=call.data.get("icon"),
            border_color=call.data.get("border_color"),
            background_color=call.data.get("background_color"),
            shape=call.data.get("shape"),
        )

    async def async_clear_fixed_notification(call: ServiceCall) -> None:
        await overlay.clear_fixed(call.data["id"])

    async def async_set_overlay(call: ServiceCall) -> None:
        await overlay.set_overlay(
            overlay_visibility=call.data.get("overlay_visibility"),
            clock_overlay_visibility=call.data.get("clock_overlay_visibility"),
            hot_corner=call.data.get("hot_corner"),
        )

    hass.services.async_register(DOMAIN, "launch_app", async_launch_app, schema=LAUNCH_APP_SCHEMA)
    hass.services.async_register(DOMAIN, "send_key", async_send_key, schema=SEND_KEY_SCHEMA)
    hass.services.async_register(DOMAIN, "show_overlay", async_show_overlay, schema=SHOW_OVERLAY_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        "show_fixed_notification",
        async_show_fixed_notification,
        schema=SHOW_FIXED_NOTIFICATION_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "clear_fixed_notification",
        async_clear_fixed_notification,
        schema=CLEAR_FIXED_NOTIFICATION_SCHEMA,
    )
    hass.services.async_register(DOMAIN, "set_overlay", async_set_overlay, schema=SET_OVERLAY_SCHEMA)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM_TYPES)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Google TV Streamer config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORM_TYPES)
    if unloaded:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        overlay = entry_data.get("overlay")
        if overlay is not None:
            await overlay.close()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "launch_app")
            hass.services.async_remove(DOMAIN, "send_key")
            hass.services.async_remove(DOMAIN, "show_overlay")
            hass.services.async_remove(DOMAIN, "show_fixed_notification")
            hass.services.async_remove(DOMAIN, "clear_fixed_notification")
            hass.services.async_remove(DOMAIN, "set_overlay")
    return unloaded
