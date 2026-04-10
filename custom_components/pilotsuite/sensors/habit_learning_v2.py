"""Habit Learning v2 Sensor for PilotSuite.

Shows habit patterns and routine predictions from the ML habit predictor.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _as_mapping(value: Any) -> Dict[str, Any]:
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _is_list(value: Any) -> bool:
    """Return True only for list payloads."""
    return isinstance(value, list)


class HabitLearningSensor(SensorEntity):
    """Sensor showing learned habit patterns."""

    _attr_name = "PilotSuite Habit Learning"
    _attr_unique_id = "ai_copilot_habit_learning"
    _attr_icon = "mdi:repeat"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the habit learning sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        """Return the number of learned patterns."""
        if not self.coordinator.data:
            return "0"
        habit_summary = _as_mapping(self.coordinator.data.get("habit_summary"))
        return str(habit_summary.get("total_patterns", 0))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return habit patterns and predictions."""
        if not self.coordinator.data:
            return {}
        habit_summary = _as_mapping(self.coordinator.data.get("habit_summary"))
        return {
            "total_patterns": habit_summary.get("total_patterns", 0),
            "time_patterns": habit_summary.get("time_patterns", {}),
            "mood_patterns": habit_summary.get("mood_patterns", {}),
            "sequences": habit_summary.get("sequences", {}),
            "device_patterns": habit_summary.get("device_patterns", {}),
            "last_update": habit_summary.get("last_update"),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HabitPredictionSensor(SensorEntity):
    """Sensor showing habit predictions."""

    _attr_name = "PilotSuite Habit Predictions"
    _attr_unique_id = "ai_copilot_habit_predictions"
    _attr_icon = "mdi:forecast"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the habit prediction sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "none"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        """Return the highest confidence prediction."""
        if not self.coordinator.data:
            return "none"
        predictions = self.coordinator.data.get("predictions")
        if not _is_list(predictions):
            return "none"
        if not predictions:
            return "none"
        # Return highest confidence prediction
        best = max(predictions, key=lambda p: _as_mapping(p).get("confidence", 0))
        return _as_mapping(best).get("pattern", "unknown")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return all predictions with details."""
        if not self.coordinator.data:
            return {}
        predictions = self.coordinator.data.get("predictions")
        if not _is_list(predictions):
            return {}
        return {
            "predictions": [
                {
                    "pattern": _as_mapping(p).get("pattern", ""),
                    "confidence": _as_mapping(p).get("confidence", 0),
                    "predicted": _as_mapping(p).get("predicted", False),
                    "details": _as_mapping(p).get("details", {}),
                }
                for p in predictions
            ],
            "count": len(predictions),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SequencePredictionSensor(SensorEntity):
    """Sensor showing device sequence predictions."""

    _attr_name = "PilotSuite Sequence Predictions"
    _attr_unique_id = "ai_copilot_sequence_predictions"
    _attr_icon = "mdi:chain"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the sequence prediction sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "none"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        """Return the most common sequence."""
        if not self.coordinator.data:
            return "none"
        sequences = self.coordinator.data.get("sequences")
        if not _is_list(sequences):
            return "none"
        if not sequences:
            return "none"
        # Return most common sequence
        best = max(sequences, key=lambda s: _as_mapping(s).get("confidence", 0))
        return " → ".join(_as_mapping(best).get("sequence", []))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return all sequences with confidence."""
        if not self.coordinator.data:
            return {}
        sequences = self.coordinator.data.get("sequences")
        if not _is_list(sequences):
            return {}
        return {
            "sequences": [
                {
                    "sequence": " → ".join(_as_mapping(s).get("sequence", [])),
                    "confidence": _as_mapping(s).get("confidence", 0),
                    "occurrences": _as_mapping(s).get("occurrences", 0),
                    "predicted": _as_mapping(s).get("predicted", False),
                }
                for s in sequences
            ],
            "count": len(sequences),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up habit learning sensors from a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    sensors = [
        HabitLearningSensor(coordinator),
        HabitPredictionSensor(coordinator),
        SequencePredictionSensor(coordinator),
    ]

    async_add_entities(sensors)

    _LOGGER.info("Habit learning sensors set up for entry %s", entry.entry_id)
