"""PilotSuite Styx Diagnostics — HA-240.

Sync mit Core API: /api/v1/health/*, /api/v1/diagnostics/*
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
    """Setup diagnostics sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL)
    async_add_entities([CoreDiagnosticsSensor(core_url, config_entry.entry_id)])


class CoreDiagnosticsSensor(SensorEntity):
    """Sensor for Core diagnostics info with rich attributes."""

    _attr_icon = "mdi:stethoscope"
    _attr_state_class = None

    def __init__(self, core_url: str, entry_id: str):
        self._core_url = core_url
        self._entry_id = entry_id
        self._attr_name = "PilotSuite Diagnostics"
        self._attr_unique_id = f"{DOMAIN}_diagnostics"
        self._attr_native_value = "unknown"
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update diagnostics from Core."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._core_url}/api/v1/diagnostics/full")
                if resp.status_code == 200:
                    data = resp.json()
                    self._attr_native_value = data.get("overall_status", "ok")
                    self._extra_state_attributes = {
                        "core_version": data.get("core_version"),
                        "python_version": data.get("python_version"),
                        "database_connected": data.get("database_connected"),
                        "api_latency_ms": data.get("api_latency_ms"),
                        "memory_mb": data.get("memory_mb"),
                        "core_url": self._core_url,
                        "last_check": utcnow().isoformat(),
                    }
                else:
                    self._attr_native_value = "unavailable"
                    self._extra_state_attributes = {
                        "error": f"HTTP {resp.status_code}",
                        "last_check": utcnow().isoformat(),
                    }
        except Exception as exc:
            _LOGGER.warning("Diagnostics update failed: %s", exc)
            self._attr_native_value = "error"
            self._extra_state_attributes = {
                "error": str(exc),
                "last_check": utcnow().isoformat(),
            }
