"""Module Integration Sensors for PilotSuite.

Exposes integration bus health, synapse learning progress,
and cross-module pattern discovery as Home Assistant sensors.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# ─── Type guards ───────────────────────────────────────────────────────────────


def _as_mapping(value, default=None):
    """Return value only if it is a dict-like mapping, else default."""
    if isinstance(value, dict):
        return value
    return default if default is not None else {}


def _as_int(value, default=0):
    """Coerce value to int, else return default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        iv = int(value)
        if isinstance(iv, int) and not isinstance(iv, bool):
            return iv
        return default
    except (TypeError, ValueError):
        return default


def _as_float(value, default=0.0):
    """Coerce value to float, else return default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, float):
        return value
    try:
        f = float(value)
        if isinstance(f, float):
            return f
        return default
    except (TypeError, ValueError):
        return default


class ModuleHealthSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing overall module integration health."""

    _attr_name = "PilotSuite Module Health"
    _attr_unique_id = "copilot_module_health"
    _attr_icon = "mdi:heart-pulse"
    _attr_should_poll = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_native_value = "unknown"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "unavailable"
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "unavailable"
        bus = _as_mapping(data.get("bus_stats", {}))
        errors = _as_int(bus.get("errors", 0))
        if errors > 10:
            return "degraded"
        return "healthy"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.coordinator.data:
            return {}
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}
        bus = _as_mapping(data.get("bus_stats"))
        if not bus:
            return {}
        attrs = {}
        attrs["bus_events_published"] = _as_int(bus.get("events_published", 0))
        attrs["bus_events_delivered"] = _as_int(bus.get("events_delivered", 0))
        attrs["bus_errors"] = _as_int(bus.get("errors", 0))
        attrs["bus_subscribers"] = _as_int(bus.get("total_subscribers", 0))
        return attrs


class SynapseActivitySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing synapse learning activity."""

    _attr_name = "PilotSuite Synapse Activity"
    _attr_unique_id = "copilot_synapse_activity"
    _attr_icon = "mdi:transit-connection-variant"
    _attr_should_poll = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "0"
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "0"
        learning = _as_mapping(data.get("learning_stats", {}))
        return str(_as_int(learning.get("total_updates", 0)))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.coordinator.data:
            return {}
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}
        learning = _as_mapping(data.get("learning_stats", {}))
        return {
            "total_synapses": _as_int(learning.get("total_synapses", 0)),
            "learning_rate": _as_float(learning.get("learning_rate", 0)),
            "total_drift": _as_float(learning.get("total_drift", 0)),
            "max_drift_synapse": learning.get("max_drift_synapse"),
        }


class CrossPatternSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing discovered cross-module patterns."""

    _attr_name = "PilotSuite Cross Patterns"
    _attr_unique_id = "copilot_cross_patterns"
    _attr_icon = "mdi:chart-scatter-plot"
    _attr_should_poll = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "0"
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "0"
        cross = _as_mapping(data.get("cross_module_stats", {}))
        return str(_as_int(cross.get("patterns_discovered", 0)))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.coordinator.data:
            return {}
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}
        cross = _as_mapping(data.get("cross_module_stats", {}))
        return {
            "snapshots_collected": _as_int(cross.get("snapshots_collected", 0)),
            "window_size": _as_int(cross.get("window_size", 0)),
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

    entities = [
        ModuleHealthSensor(coordinator),
        SynapseActivitySensor(coordinator),
        CrossPatternSensor(coordinator),
    ]

    async_add_entities(entities)
    _LOGGER.info("Module integration sensors set up for entry %s", entry.entry_id)
