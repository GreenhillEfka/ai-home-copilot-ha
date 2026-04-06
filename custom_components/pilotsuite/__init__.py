"""PilotSuite Integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "pilotsuite"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PilotSuite component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up PilotSuite from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    return True