"""PilotSuite Styx Sensors — HA-186.

Sync mit Core API: /api/v1/metrics/*, /api/v1/analytics/*
"""
from __future__ import annotations

import logging
from datetime import datetime

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
    """Setup sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL)
    entities = [
        CoreHealthSensor(core_url, config_entry.entry_id),
        CoreMetricsSensor(core_url, config_entry.entry_id),
    ]
    async_add_entities(entities)


class CoreHealthSensor(SensorEntity):
    """Sensor for Core API health."""

    _attr_icon = "mdi:heart-pulse"
    _attr_state_class = None

    def __init__(self, core_url: str, entry_id: str):
        self._core_url = core_url
        self._entry_id = entry_id
        self._attr_name = "PilotSuite Core Health"
        self._attr_unique_id = f"{DOMAIN}_core_health"
        self._attr_native_value = "unknown"
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update from Core health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._core_url}/api/v1/health/status")
                if resp.status_code == 200:
                    data = resp.json()
                    self._attr_native_value = data.get("status", "healthy")
                    self._extra_state_attributes = {
                        "core_url": self._core_url,
                        "last_check": utcnow().isoformat(),
                        "version": data.get("version"),
                        "uptime_seconds": data.get("uptime_seconds"),
                    }
                else:
                    self._attr_native_value = "unreachable"
                    self._extra_state_attributes = {
                        "core_url": self._core_url,
                        "last_check": utcnow().isoformat(),
                        "error": f"HTTP {resp.status_code}",
                    }
        except Exception as exc:
            _LOGGER.warning("Core health check failed: %s", exc)
            self._attr_native_value = "error"
            self._extra_state_attributes = {
                "core_url": self._core_url,
                "last_check": utcnow().isoformat(),
                "error": str(exc),
            }


class CoreMetricsSensor(SensorEntity):
    """Sensor for Core API metrics."""

    _attr_icon = "mdi:chart-line"
    _attr_state_class = "measurement"

    def __init__(self, core_url: str, entry_id: str):
        self._core_url = core_url
        self._entry_id = entry_id
        self._attr_name = "PilotSuite Core Metrics"
        self._attr_unique_id = f"{DOMAIN}_core_metrics"
        self._attr_native_value = "active"
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Async update from Core metrics endpoint."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._core_url}/api/v1/metrics/summary")
                if resp.status_code == 200:
                    data = resp.json()
                    self._attr_native_value = data.get("active_count", 0)
                    self._extra_state_attributes = {
                        "total_requests": data.get("total_requests"),
                        "error_count": data.get("error_count"),
                        "avg_latency_ms": data.get("avg_latency_ms"),
                        "last_update": utcnow().isoformat(),
                    }
                else:
                    self._attr_native_value = 0
                    self._extra_state_attributes = {
                        "error": f"HTTP {resp.status_code}",
                        "last_update": utcnow().isoformat(),
                    }
        except Exception as exc:
            _LOGGER.warning("Core metrics check failed: %s", exc)
            self._extra_state_attributes = {
                "error": str(exc),
                "last_update": utcnow().isoformat(),
            }
