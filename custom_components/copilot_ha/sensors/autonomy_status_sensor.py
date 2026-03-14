"""PilotSuite — Autonomy Status Sensors (v14.2.0)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


class AutonomyStatusSensor(CopilotBaseEntity, SensorEntity):
    """Overall autonomy system status."""

    _attr_icon = "mdi:robot"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Autonomie Status"
    _attr_unique_id = "copilot_ha_autonomy_status"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        autonomy = data.get("autonomy", {})

        stats = autonomy.get("stats", {})
        zones = autonomy.get("zones", {})

        active_zones = sum(1 for z in zones.values() if z.get("mode") == "autonomy")
        total_executed = stats.get("executed", 0)

        if active_zones > 0:
            self._attr_native_value = "aktiv"
        elif any(z.get("mode") == "learning" for z in zones.values()):
            self._attr_native_value = "lernend"
        else:
            self._attr_native_value = "inaktiv"

        self._attr_extra_state_attributes = {
            "active_zones": active_zones,
            "total_zones": len(zones),
            "total_executed": total_executed,
            "total_suggested": stats.get("suggested", 0),
            "total_skipped": stats.get("skipped", 0),
            "total_errors": stats.get("errors", 0),
            "total_events": stats.get("total_events", 0),
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()


class AutonomyHistorySensor(CopilotBaseEntity, SensorEntity):
    """Recent autonomy execution history."""

    _attr_icon = "mdi:history"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Autonomie Verlauf"
    _attr_unique_id = "copilot_ha_autonomy_history"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        history = data.get("autonomy_history", [])

        self._attr_native_value = len(history)
        self._attr_extra_state_attributes = {
            "recent_actions": history[:10],
            "total_count": len(history),
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()


class ZoneHealthOverviewSensor(CopilotBaseEntity, SensorEntity):
    """Zone health overview sensor."""

    _attr_icon = "mdi:shield-check"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Zonen Gesundheit"
    _attr_unique_id = "copilot_ha_zone_health_overview"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        zone_health = data.get("zone_health", {})

        summary = zone_health.get("summary", {})
        zones = zone_health.get("zones", [])

        avg_score = summary.get("avg_score", 0)
        self._attr_native_value = round(avg_score)

        zone_scores = {}
        for z in zones:
            zone_scores[z.get("zone_id", "")] = {
                "score": z.get("health_score", 0),
                "status": z.get("status", "unknown"),
                "zone_name": z.get("zone_name", ""),
            }

        self._attr_extra_state_attributes = {
            "total_zones": summary.get("total", 0),
            "healthy": summary.get("healthy", 0),
            "degraded": summary.get("degraded", 0),
            "critical": summary.get("critical", 0),
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
