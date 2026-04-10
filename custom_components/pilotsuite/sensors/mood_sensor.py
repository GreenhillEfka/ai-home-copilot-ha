"""Mood sensor entities for PilotSuite.

Exposes the neural system's mood state to Home Assistant for visibility
and automation purposes.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# Guard helpers
# =============================================================================

def _as_mapping(val: Any) -> dict[str, Any]:
    """Reject non-dict top-level payloads."""
    if isinstance(val, dict):
        return val
    return {}


def _as_float(val: Any, default: float) -> float:
    """Accept only finite numeric values; reject bool, inf, nan."""
    if isinstance(val, bool):
        return default
    if isinstance(val, (int, float)) and math.isfinite(val):
        return float(val)
    return default


def _as_string(val: Any) -> str:
    """Accept only non-empty string values."""
    if isinstance(val, str) and val.strip():
        return val.strip()
    return ""


def _as_list(val: Any) -> list:
    """Accept only list payloads."""
    if isinstance(val, list):
        return val
    return []


# =============================================================================
# MoodSensor
# =============================================================================

class MoodSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the current mood from the neural system."""

    _attr_name = "PilotSuite Mood"
    _attr_unique_id = "pilotsuite_mood"
    _attr_icon = "mdi:robot-happy"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the mood sensor."""
        super().__init__(coordinator)
        self._attr_native_value = "unknown"

    @property
    def native_value(self) -> str:
        """Return the current mood."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "unknown"
        mood_data = _as_mapping(data.get("mood"))
        return _as_string(mood_data.get("mood")) or "unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes (including emotions for Lovelace card)."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}

        mood_data = _as_mapping(data.get("mood"))

        raw_emotions = _as_list(mood_data.get("emotions"))
        emotions = raw_emotions
        if not emotions:
            neurons = _as_list(mood_data.get("contributing_neurons"))
            emotions = [
                {"name": _as_string(n.get("name")) or "unknown", "value": _as_float(n.get("value"), 0.0)}
                for n in neurons
                if isinstance(n, dict)
            ]

        zone_moods_raw = data.get("zone_moods")
        zone_moods = _as_mapping(zone_moods_raw) if zone_moods_raw is not None else {}

        return {
            "confidence": _as_float(mood_data.get("confidence"), 0.0),
            "emotions": emotions,
            "zone": _as_string(mood_data.get("zone")) or "unknown",
            "last_updated": mood_data.get("last_update"),
            "last_update": mood_data.get("last_update"),
            "contributing_neurons": _as_list(mood_data.get("contributing_neurons")),
            "zone_moods": zone_moods,
            "zone_moods_count": len(zone_moods),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


# =============================================================================
# MoodConfidenceSensor
# =============================================================================

class MoodConfidenceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the confidence level of the current mood."""

    _attr_name = "PilotSuite Mood Confidence"
    _attr_unique_id = "pilotsuite_mood_confidence"
    _attr_icon = "mdi:gauge"
    _attr_native_unit_of_measurement = "%"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the confidence sensor."""
        super().__init__(coordinator)
        self._attr_native_value = 0

    @property
    def native_value(self) -> int:
        """Return the confidence as percentage."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return 0
        mood_data = _as_mapping(data.get("mood"))
        confidence = _as_float(mood_data.get("confidence"), 0.0)
        return int(confidence * 100)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}
        mood_data = _as_mapping(data.get("mood"))
        return {
            "mood": _as_string(mood_data.get("mood")) or "unknown",
            "factors": _as_mapping(mood_data.get("factors", {})),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


# =============================================================================
# NeuronActivitySensor
# =============================================================================

class NeuronActivitySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing active neurons count and activity grid for Lovelace card."""

    _attr_name = "PilotSuite Neuron Activity"
    _attr_unique_id = "pilotsuite_neuron_activity"
    _attr_icon = "mdi:brain"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the neuron activity sensor."""
        super().__init__(coordinator)
        self._attr_native_value = 0
        self._history: list[dict] = []
        self._history_initialized = False

    @property
    def native_value(self) -> int:
        """Return the count of active neurons."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return 0
        neurons = _as_mapping(data.get("neurons"))
        active_count = sum(
            1 for n in neurons.values()
            if isinstance(n, dict) and n.get("active", False) is True
        )
        return active_count

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return neuron details (including activity grid for Lovelace card)."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}

        neurons = _as_mapping(data.get("neurons"))

        activity = [
            {
                "name": _as_string(name),
                "active": bool(n.get("active", False)),
                "value": _as_float(n.get("value"), 0.0),
                "confidence": _as_float(n.get("confidence"), 0.0),
            }
            for name, n in neurons.items()
            if isinstance(n, dict)
        ]

        active_neurons = [a for a in activity if a["active"]]

        current_active = len(active_neurons)
        self._history.append({"value": current_active})
        if len(self._history) > 24:
            self._history = self._history[-24:]

        return {
            "activity": activity,
            "active_neurons": active_neurons,
            "total_neurons": len(neurons),
            "history": list(self._history),
        }

    async def async_added_to_hass(self) -> None:
        """Load neuron history from Core API on first add."""
        await super().async_added_to_hass()
        if not self._history_initialized:
            self._history_initialized = True
            await self._load_initial_history()

    async def _load_initial_history(self) -> None:
        """Fetch initial neuron history from Core API to survive restarts."""
        try:
            api = self.coordinator.api
            history_data = await api._safe_get(
                "/api/v1/neurons/mood/history",
                {"history": []},
                key="history",
                label="Neuron mood history",
            )
            if isinstance(history_data, list):
                self._history = [
                    {"value": _as_float(entry.get("active_count"), 0.0)}
                    for entry in history_data[-24:]
                ]
                _LOGGER.debug(
                    "Loaded %d neuron history entries from Core API",
                    len(self._history),
                )
        except Exception:
            _LOGGER.debug("Could not load neuron history from Core API")

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


# =============================================================================
# Setup
# =============================================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mood sensors from a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    sensors = [
        MoodSensor(coordinator),
        MoodConfidenceSensor(coordinator),
        NeuronActivitySensor(coordinator),
    ]

    async_add_entities(sensors)

    _LOGGER.info("Mood sensors set up for entry %s", entry.entry_id)
