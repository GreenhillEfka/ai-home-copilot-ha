"""Module Integration Sensors for PilotSuite.

Exposes integration bus health, synapse learning progress,
and cross-module pattern discovery as Home Assistant sensors.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


class ModuleHealthSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing overall module integration health."""

    _attr_name = "PilotSuite Module Health"
    _attr_unique_id = "copilot_module_health"
    _attr_icon = "mdi:heart-pulse"
    _attr_should_poll = False

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "unavailable"
        bus = self.coordinator.data.get("bus_stats", {})
        errors = bus.get("errors", 0)
        if errors > 10:
            return "degraded"
        return "healthy"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        attrs: dict[str, Any] = {}
        bus = self.coordinator.data.get("bus_stats")
        if bus:
            attrs["bus_events_published"] = bus.get("events_published", 0)
            attrs["bus_events_delivered"] = bus.get("events_delivered", 0)
            attrs["bus_errors"] = bus.get("errors", 0)
            attrs["bus_subscribers"] = bus.get("total_subscribers", 0)
        return attrs


class SynapseActivitySensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing synapse learning activity."""

    _attr_name = "PilotSuite Synapse Activity"
    _attr_unique_id = "copilot_synapse_activity"
    _attr_icon = "mdi:transit-connection-variant"
    _attr_should_poll = False

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "0"
        learning = self.coordinator.data.get("learning_stats", {})
        return str(learning.get("total_updates", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        learning = self.coordinator.data.get("learning_stats", {})
        return {
            "total_synapses": learning.get("total_synapses", 0),
            "learning_rate": learning.get("learning_rate", 0),
            "total_drift": learning.get("total_drift", 0),
            "max_drift_synapse": learning.get("max_drift_synapse"),
        }


class CrossPatternSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing discovered cross-module patterns."""

    _attr_name = "PilotSuite Cross Patterns"
    _attr_unique_id = "copilot_cross_patterns"
    _attr_icon = "mdi:chart-scatter-plot"
    _attr_should_poll = False

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "0"
        cross = self.coordinator.data.get("cross_module_stats", {})
        return str(cross.get("patterns_discovered", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        cross = self.coordinator.data.get("cross_module_stats", {})
        return {
            "snapshots_collected": cross.get("snapshots_collected", 0),
            "window_size": cross.get("window_size", 0),
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up module integration sensors."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    async_add_entities([
        ModuleHealthSensor(coordinator),
        SynapseActivitySensor(coordinator),
        CrossPatternSensor(coordinator),
    ])
