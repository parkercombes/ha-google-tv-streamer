"""Config flow for Google TV Streamer."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PORT, DOMAIN


class GoogleTVStreamerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google TV Streamer."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual setup by host."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            await self.async_set_unique_id(str(host).lower())
            self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, host),
                data={CONF_HOST: host, CONF_PORT: port},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle ADB mDNS discovery."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        properties = discovery_info.properties or {}
        serial = (
            properties.get("adb_serial")
            or properties.get("serial")
            or properties.get("ro.serialno")
            or host
        )
        if isinstance(serial, bytes):
            serial = serial.decode(errors="ignore")

        await self.async_set_unique_id(str(serial).lower())
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
        self.context["title_placeholders"] = {"name": discovery_info.name or host}

        return self.async_create_entry(
            title=discovery_info.name or host,
            data={CONF_HOST: host, CONF_PORT: port},
        )
