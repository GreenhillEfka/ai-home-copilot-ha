"""PilotSuite — Autonomy Status Sensors (v14.2.0)."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# Guard helpers
# =============================================================================

def _as_mapping(value: Any) -> dict:
    """Return value as a dict, or empty dict if not a mapping."""
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: Any) -> list:
    """Return value as a list, or empty list if not a list."""
    if isinstance(value, list):
        return value
    return []


def _as_int(value: Any, default: int = 0) -> int:
    """Return value as int, or default if not a finite numeric int."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    """Return value as float, or default if not a finite numeric value."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
    return default


def _as_string(value: Any, default: str = "") -> str:
    """Return value as string, or default if not a non-empty string."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


# =============================================================================
# AutonomyStatusSensor
# =============================================================================

class AutonomyStatusSensor(CopilotBaseEntity, SensorEntity):
    """Overall autonomy system status."""

    _attr_icon = "mdi:robot"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Autonomie Status"
    _attr_unique_id = "pilotsuite_autonomy_status"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = _as_mapping(self.coordinator.data)
        autonomy = _as_mapping(data.get("autonomy"))
        zones = _as_mapping(autonomy.get("zones"))
        stats = _as_mapping(autonomy.get("stats"))

        # Guard zone iteration against non-dict zone items
        active_zones = 0
        for z in zones.values():
            if isinstance(z, dict) and z.get("mode") == "autonomy":
                active_zones += 1

        if active_zones > 0:
            self._attr_native_value = "aktiv"
        elif any(
            isinstance(z, dict) and z.get("mode") == "learning"
            for z in zones.values()
        ):
            self._attr_native_value = "lernend"
        else:
            self._attr_native_value = "inaktiv"

        # Extract per-zone module states from dashboard data
        zone_modules: dict[str, Any] = {}
        for zone_id, zone_data in zones.items():
            if isinstance(zone_data, dict):
                ms = zone_data.get("module_states")
                if ms and isinstance(ms, dict):
                    zone_modules[zone_id] = ms

        self._attr_extra_state_attributes = {
            "active_zones": active_zones,
            "total_zones": _as_int(len(zones)),
            "total_executed": _as_int(stats.get("executed")),
            "total_suggested": _as_int(stats.get("suggested")),
            "total_skipped": _as_int(stats.get("skipped")),
            "total_errors": _as_int(stats.get("errors")),
            "total_events": _as_int(stats.get("total_events")),
            "zone_modules": zone_modules,
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()


# =============================================================================
# AutonomyHistorySensor
# =============================================================================

class AutonomyHistorySensor(CopilotBaseEntity, SensorEntity):
    """Recent autonomy execution history."""

    _attr_icon = "mdi:history"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Autonomie Verlauf"
    _attr_unique_id = "pilotsuite_autonomy_history"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = _as_mapping(self.coordinator.data)
        history = _as_list(data.get("autonomy_history"))

        self._attr_native_value = _as_int(len(history))
        self._attr_extra_state_attributes = {
            "recent_actions": history[:10],
            "total_count": _as_int(len(history)),
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()


# =============================================================================
# ZoneHealthOverviewSensor
# =============================================================================

class ZoneHealthOverviewSensor(CopilotBaseEntity, SensorEntity):
    """Zone health overview sensor."""

    _attr_icon = "mdi:shield-check"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Zonen Gesundheit"
    _attr_unique_id = "pilotsuite_zone_health_overview"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = _as_mapping(self.coordinator.data)
        zone_health = _as_mapping(data.get("zone_health"))
        summary = _as_mapping(zone_health.get("summary"))
        zones = _as_list(zone_health.get("zones"))

        avg_score = _as_float(summary.get("avg_score"))
        self._attr_native_value = round(avg_score)

        zone_scores = {}
        for z in zones:
            if isinstance(z, dict):
                zone_scores[_as_string(z.get("zone_id"))] = {
                    "score": _as_int(z.get("health_score")),
                    "status": _as_string(z.get("status"), "unknown"),
                    "zone_name": _as_string(z.get("zone_name")),
                }

        self._attr_extra_state_attributes = {
            "total_zones": _as_int(summary.get("total_zones")),
            "healthy": _as_int(summary.get("healthy")),
            "degraded": _as_int(summary.get("degraded")),
            "critical": _as_int(summary.get("critical")),
            "avg_score": avg_score,
            "zones": zone_scores,
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()


AUTONOMY_SENSORS = [
    AutonomyStatusSensor,
    AutonomyHistorySensor,
    ZoneHealthOverviewSensor,
]
