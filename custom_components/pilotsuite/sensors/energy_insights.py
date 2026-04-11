"""Energy Insights Sensor for PilotSuite.

Shows energy consumption insights and optimization recommendations.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _as_mapping(value: Any) -> Dict[str, Any]:
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    """Return list payloads, otherwise a safe empty list."""
    return value if isinstance(value, list) else []


def _as_number(value: Any, default: int | float) -> int | float:
    """Return finite numeric payloads, otherwise a safe default."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        return default
    return value if isinstance(value, int) else numeric_value


def _as_string(value: Any, default: str) -> str:
    """Return string payloads, otherwise a safe default."""
    return value if isinstance(value, str) and value else default


def _project_recommendation(value: Any) -> Dict[str, Any]:
    """Project one recommendation payload into a safe HA attribute shape."""
    recommendation = _as_mapping(value)
    if not recommendation:
        return {}
    return {
        "title": _as_string(recommendation.get("title"), ""),
        "priority": _as_string(recommendation.get("priority"), "low"),
        "description": _as_string(recommendation.get("description"), ""),
        "savings_potential_wh": _as_number(recommendation.get("savings_potential_wh"), 0),
    }


class EnergyInsightSensor(SensorEntity):
    """Sensor showing current energy insights."""

    _attr_name = "PilotSuite Energy Insights"
    _attr_unique_id = "pilotsuite_energy_insights"
    _attr_icon = "mdi:lightning-bolt"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kWh"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the energy insight sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = 0.0
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> float:
        """Return the total energy consumption."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return 0.0

        energy_summary = _as_mapping(coordinator_data.get("energy_summary"))
        total_kwh = _as_number(energy_summary.get("total_kwh"), 0.0)
        return round(float(total_kwh), 3)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return energy insights and recommendations."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return {}

        energy_summary = _as_mapping(coordinator_data.get("energy_summary"))
        recommendations = [
            projected
            for item in _as_list(coordinator_data.get("energy_recommendations"))
            if (projected := _project_recommendation(item))
        ]

        return {
            "total_kwh": _as_number(energy_summary.get("total_kwh"), 0.0),
            "device_consumption": _as_mapping(energy_summary.get("device_consumption")),
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "hours": _as_number(energy_summary.get("hours"), 24),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class EnergyRecommendationSensor(SensorEntity):
    """Sensor showing active energy recommendations."""

    _attr_name = "PilotSuite Energy Recommendations"
    _attr_unique_id = "pilotsuite_energy_recommendations"
    _attr_icon = "mdi:idea"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the energy recommendation sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "none"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        """Return the number of active recommendations."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return "none"

        recommendations = [
            projected
            for item in _as_list(coordinator_data.get("energy_recommendations"))
            if (projected := _project_recommendation(item))
        ]
        if not recommendations:
            return "none"

        best = max(recommendations, key=lambda recommendation: recommendation.get("priority", "low"))
        return _as_string(best.get("title"), "unknown")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return all recommendations."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return {}

        recommendations = [
            projected
            for item in _as_list(coordinator_data.get("energy_recommendations"))
            if (projected := _project_recommendation(item))
        ]

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up energy insights sensors from a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    sensors = [
        EnergyInsightSensor(coordinator),
        EnergyRecommendationSensor(coordinator),
    ]

    async_add_entities(sensors)

    _LOGGER.info("Energy insights sensors set up for entry %s", entry.entry_id)
