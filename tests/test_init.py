"""Tests for Google TV Streamer setup and unload."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.google_tv_streamer.const import DOMAIN, PLATFORMS


async def test_setup_and_unload_entry(hass):
    """Test setup stores runtime state, forwards platforms, and unloads cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room TV",
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 5555},
        entry_id="test-entry",
        unique_id="192.0.2.10",
    )
    entry.add_to_hass(hass)
    adb = Mock()
    adb.current_app.return_value = "com.google.android.youtube.tv"
    adb.now_playing.return_value = None

    with (
        patch("custom_components.google_tv_streamer.connect_streamer", return_value=adb) as connect,
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock(return_value=True)) as forward,
        patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)) as unload,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert hass.data[DOMAIN][entry.entry_id]["adb"] is adb
        assert "coordinator" in hass.data[DOMAIN][entry.entry_id]
        connect.assert_called_once_with("192.0.2.10", 5555)
        forward.assert_awaited_once_with(entry, [platform for platform in PLATFORMS])

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    unload.assert_awaited_once_with(entry, [platform for platform in PLATFORMS])
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
