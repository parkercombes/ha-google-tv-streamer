"""Tests for the Google TV Streamer config flow."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.google_tv_streamer.const import DEFAULT_PORT, DOMAIN


async def test_user_step_creates_entry(hass):
    """Test a user flow creates a config entry after validation."""
    with patch(
        "custom_components.google_tv_streamer.config_flow.connect_streamer",
        return_value=object(),
    ) as connect:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.0.2.10", CONF_PORT: 5555, CONF_NAME: "Living Room TV"},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "Living Room TV"
    assert result["data"] == {CONF_HOST: "192.0.2.10", CONF_PORT: 5555}
    connect.assert_called_once_with("192.0.2.10", 5555)


async def test_user_step_duplicate_host_aborts(hass):
    """Test a user flow aborts when the host is already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 5555},
        unique_id="192.0.2.10",
    ).add_to_hass(hass)

    with patch("custom_components.google_tv_streamer.config_flow.connect_streamer") as connect:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.0.2.10", CONF_PORT: 5555},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    connect.assert_not_called()


async def test_zeroconf_step_creates_entry(hass):
    """Test mDNS discovery creates a config entry after validation."""
    discovery_info = SimpleNamespace(
        host="192.0.2.20",
        port=DEFAULT_PORT,
        properties={"adb_serial": "ABC123"},
        name="Bedroom TV",
    )

    with patch(
        "custom_components.google_tv_streamer.config_flow.connect_streamer",
        return_value=object(),
    ) as connect:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "Bedroom TV"
    assert result["data"] == {CONF_HOST: "192.0.2.20", CONF_PORT: DEFAULT_PORT, "serial": "ABC123"}
    connect.assert_called_once_with("192.0.2.20", DEFAULT_PORT)


async def test_zeroconf_step_duplicate_serial_aborts(hass):
    """Test mDNS discovery aborts when the serial is already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.20", CONF_PORT: DEFAULT_PORT, "serial": "ABC123"},
        unique_id="abc123",
    ).add_to_hass(hass)
    discovery_info = SimpleNamespace(
        host="192.0.2.21",
        port=DEFAULT_PORT,
        properties={"adb_serial": "ABC123"},
        name="Bedroom TV",
    )

    with patch("custom_components.google_tv_streamer.config_flow.connect_streamer") as connect:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    connect.assert_not_called()
