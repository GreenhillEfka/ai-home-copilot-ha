"""Habit Learning v2 Sensor for PilotSuite (v6.2.0).

Uses UnifiedAnomalyFramework for sigma-deviation based habit anomaly detection.
Tracks habit pattern deviations against learned 7-day baseline.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator
from ..anomaly_framework import get_framework, AnomalyLevel

_LOGGER = logging.getLogger(__name__)


class HabitLearningSensor(SensorEntity):
    """Sensor showing learned habit patterns with anomaly scoring."""

    _attr_name = "PilotSuite Habit Learning"
    _attr_unique_id = "ai_copilot_habit_learning"
    _attr_icon = "mdi:repeat"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "idle"
        habit_summary = self.coordinator.data.get("habit_summary", {})
        total = habit_summary.get("total_patterns", 0)
        return str(total)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        habit_summary = self.coordinator.data.get("habit_summary", {})
        attrs = {
            "total_patterns": habit_summary.get("total_patterns", 0),
            "time_patterns": habit_summary.get("time_patterns", {}),
            "mood_patterns": habit_summary.get("mood_patterns", {}),
            "sequences": habit_summary.get("sequences", {}),
            "device_patterns": habit_summary.get("device_patterns", {}),
            "last_update": habit_summary.get("last_update"),
            "anomaly_framework_active": True,
        }

        # Add habit anomaly info from framework
        framework = get_framework(self.coordinator.hass)
        habit_alerts = [a for a in framework._alerts if a.sensor_type == "habit"]
        if habit_alerts:
            latest = habit_alerts[-1]
            attrs.update({
                "habit_anomaly_level": latest.level.value,
                "habit_deviation_sigma": round(latest.deviation_sigma, 2),
                "habit_confidence": latest.confidence,
            })
        else:
            attrs["habit_anomaly_level"] = "normal"

        return attrs

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class HabitPredictionSensor(SensorEntity):
    """Sensor showing habit predictions with failure forecasting."""

    _attr_name = "PilotSuite Habit Predictions"
    _attr_unique_id = "ai_copilot_habit_predictions"
    _attr_icon = "mdi:forecast"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "none"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "none"
        predictions = self.coordinator.data.get("predictions", [])
        if not predictions:
            return "none"
        best = max(predictions, key=lambda p: p.get("confidence", 0))
        return best.get("pattern", "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        predictions = self.coordinator.data.get("predictions", [])
        return {
            "predictions": [
                {
                    "pattern": p.get("pattern", ""),
                    "confidence": p.get("confidence", 0),
                    "predicted": p.get("predicted", False),
                    "details": p.get("details", {}),
                }
                for p in predictions
            ],
            "count": len(predictions),
        }

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class HabitAnomalySensor(SensorEntity):
    """Sensor showing habit pattern anomaly level."""

    _attr_name = "PilotSuite Habit Anomaly"
    _attr_unique_id = "ai_copilot_habit_anomaly"
    _attr_icon = "mdi:alert-decagram"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._level = "normal"

    @property
    def native_value(self) -> str:
        return self._level

    @property
    def icon(self) -> str:
        return {
            "critical": "mdi:alert-octagon",
            "high": "mdi:alert",
            "medium": "mdi:alert-circle-outline",
            "low": "mdi:information",
            "normal": "mdi:check-decagram",
        }.get(self._level, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        framework = get_framework(self.coordinator.hass)
        habit_alerts = [a for a in framework._alerts if a.sensor_type == "habit"]
        if habit_alerts:
            latest = habit_alerts[-1]
            return {
                "confidence": latest.confidence,
                "deviation_sigma": latest.deviation_sigma,
                "failure_prediction_48h": latest.predicted_48h,
                "baseline_mean": latest.baseline_mean,
                "current_value": latest.current_value,
                "message": latest.message,
                "baseline_window_days": 7,
            }
        return {"confidence": 0, "deviation_sigma": 0, "baseline_window_days": 7}

    def _handle_coordinator_update(self) -> None:
        framework = get_framework(self.coordinator.hass)
        habit_alerts = [a for a in framework._alerts if a.sensor_type == "habit"]
        if habit_alerts:
            self._level = habit_alerts[-1].level.value
        else:
            self._level = "normal"
        self.async_write_ha_state()


class HabitEfficiencySensor(SensorEntity):
    """Sensor showing HVAC efficiency trend vs learned baseline."""

    _attr_name = "PilotSuite Habit Efficiency"
    _attr_unique_id = "ai_copilot_habit_efficiency"
    _attr_icon = "mdi:thermometer"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_native_value = "unknown"

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "unknown"
        habit_summary = self.coordinator.data.get("habit_summary", {})
        time_patterns = habit_summary.get("time_patterns", {})
        # Use HVAC runtime as efficiency proxy
        hvac = time_patterns.get("hvac_runtime_24h", {})
        baseline = time_patterns.get("hvac_runtime_7d_avg", 0)
        current = hvac.get("value", 0) if isinstance(hvac, dict) and hvac else 0
        if baseline > 0 and current > 0 and current > baseline * 1.4:
            return "Efficiency Degradation Detected"
        elif baseline > 0 and current > 0 and current < baseline * 0.6:
            return "Unusually Efficient"
        return "Normal"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"anomaly_framework": "sigma_deviation"}
        framework = get_framework(self.coordinator.hass)
        if self.coordinator.data:
            habit_summary = self.coordinator.data.get("habit_summary", {})
            time_patterns = habit_summary.get("time_patterns", {})
            hvac = time_patterns.get("hvac_runtime_24h", {})
            current = hvac.get("value", 0) if isinstance(hvac, dict) else 0
            if current and self.coordinator.hass:
                alert = framework.record(
                    sensor_type="habit",
                    sensor_id="hvac_efficiency",
                    metric="runtime_minutes",
                    value=float(current),
                )
                if alert:
                    attrs.update({
                        "confidence": alert.confidence,
                        "deviation_sigma": round(alert.deviation_sigma, 2),
                        "failure_prediction_48h": alert.predicted_48h,
                        "baseline_mean": round(alert.baseline_mean, 1),
                    })
        return attrs

    def _handle_coordinator_update(self) -> None:
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
        HabitAnomalySensor(coordinator),
        HabitEfficiencySensor(coordinator),
    ]

    async_add_entities(sensors)

    _LOGGER.info("Habit learning sensors set up for entry %s", entry.entry_id)
