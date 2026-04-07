"""PilotSuite Styx Configuration Info — HA-277.

Sync mit Core API: /api/v1/config/*
"""
from __future__ import annotations

import logging

import httpx
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow

from .const import CONF_CORE_URL, DEFAULT_CORE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup configuration sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL)
    async_add_entities([CoreConfigSensor(core_url, config_entry.entry_id)])


class CoreConfigSensor(SensorEntity):
    """Sensor for Core configuration with rich attributes."""

    _attr_icon = "mdi:cog"
    _attr_state_class = None

    def __init__(self, core_url: str, entry_id: str):
        self._core_url = core_url
        self._entry_id = entry_id
        self._attr_name = "PilotSuite Config"
        self._attr_unique_id = f"{DOMAIN}_config"
        self._attr_native_value = "unknown"
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update configuration info from Core."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._core_url}/api/v1/config/status")
                if resp.status_code == 200:
                    data = resp.json()
                    self._attr_native_value = data.get("environment", "unknown")
                    self._extra_state_attributes = {
                        "debug_mode": data.get("debug_mode"),
                        "log_level": data.get("log_level"),
                        "max_connections": data.get("max_connections"),
                        "feature_flags": data.get("feature_flags", []),
                        "core_url": self._core_url,
                        "last_update": utcnow().isoformat(),
                    }
                else:
                    self._extra_state_attributes = {
                        "error": f"HTTP {resp.status_code}",
                        "last_update": utcnow().isoformat(),
                    }
        except Exception as exc:
            _LOGGER.warning("Config update failed: %s", exc)
            self._extra_state_attributes = {
                "error": str(exc),
                "last_update": utcnow().isoformat(),
            }
