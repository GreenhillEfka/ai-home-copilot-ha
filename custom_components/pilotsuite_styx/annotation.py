"""PilotSuite Styx Annotation — HA-303.

Auto-Sync Core: /api/v1/annotations/*
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


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup annotation sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL)
    async_add_entities([CoreAnnotationSensor(core_url, config_entry.entry_id)])


class CoreAnnotationSensor(SensorEntity):
    """Sensor for Core annotations count and latest."""

    _attr_icon = "mdi:annotation"
    _attr_state_class = "measurement"

    def __init__(self, core_url: str, entry_id: str):
        self._core_url = core_url
        self._entry_id = entry_id
        self._attr_name = "PilotSuite Annotations"
        self._attr_unique_id = f"{DOMAIN}_annotations"
        self._attr_native_value = 0
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update from Core annotations endpoint."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._core_url}/api/v1/annotations/list",
                    params={"limit": 5},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    annotations = data.get("annotations", [])
                    self._attr_native_value = len(annotations)
                    self._extra_state_attributes = {
                        "total_count": data.get("total_count", len(annotations)),
                        "latest_annotation": (
                            annotations[0].get("text") if annotations else None
                        ),
                        "core_url": self._core_url,
                        "last_update": utcnow().isoformat(),
                    }
                else:
                    self._extra_state_attributes = {
                        "error": f"HTTP {resp.status_code}",
                        "last_update": utcnow().isoformat(),
                    }
        except Exception as exc:
            _LOGGER.warning("Annotation update failed: %s", exc)
            self._extra_state_attributes = {
                "error": str(exc),
                "last_update": utcnow().isoformat(),
            }
