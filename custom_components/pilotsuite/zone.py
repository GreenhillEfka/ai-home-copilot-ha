"""PilotSuite Styx Zone — HA-235.

Sync mit Core API: /api/v1/zones/*, /api/v1/areas/*
"""
from __future__ import annotations

import logging

import httpx
from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Setup zone entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL)
    entities = [
        CoreZoneSensor(core_url, "Living Room", "living_room", config_entry.entry_id),
    ]
    async_add_entities(entities)


class CoreZoneSensor(BinarySensorEntity):
    """Binary sensor for zone occupancy with extra attributes."""

    def __init__(self, core_url: str, name: str, zone_id: str, entry_id: str):
        self._core_url = core_url
        self._zone_id = zone_id
        self._entry_id = entry_id
        self._attr_name = f"PilotSuite {name} Zone"
        self._attr_unique_id = f"{DOMAIN}_zone_{zone_id}"
        self._attr_is_on = False
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update zone state from Core."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._core_url}/api/v1/zones/state")
                if resp.status_code == 200:
                    data = resp.json()
                    occupied = data.get("occupied", [])
                    self._attr_is_on = f"{DOMAIN}_zone_{self._zone_id}" in occupied
                    self._extra_state_attributes = {
                        "zone_id": self._zone_id,
                        "occupied_zones": occupied,
                        "last_update": utcnow().isoformat(),
                        "core_url": self._core_url,
                    }
                else:
                    self._extra_state_attributes = {
                        "zone_id": self._zone_id,
                        "error": f"HTTP {resp.status_code}",
                        "last_update": utcnow().isoformat(),
                    }
        except Exception as exc:
            _LOGGER.warning("Zone update failed: %s", exc)
            self._extra_state_attributes = {
                "zone_id": self._zone_id,
                "error": str(exc),
                "last_update": utcnow().isoformat(),
            }
