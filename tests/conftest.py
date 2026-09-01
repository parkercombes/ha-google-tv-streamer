"""Fixtures for Google TV Streamer tests."""

from __future__ import annotations

import pytest


def pytest_configure(config):
    """Run pytest-asyncio in auto mode for Home Assistant's async fixtures."""
    config.option.asyncio_mode = "auto"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test."""
    def _enabled_fixture():
        if enable_custom_integrations is not None:
            yield from enable_custom_integrations
        else:
            yield

    yield from _enabled_fixture()
