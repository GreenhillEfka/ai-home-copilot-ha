"""Anomaly Alert Sensor for PilotSuite.

Shows real-time anomaly detection status from Core anomaly detection engine.
Uses CoordinatorEntity pattern for automatic updates via coordinator.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class AnomalyAlertSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current anomaly detection status."""

    _attr_name = "PilotSuite Anomaly Alert"
    _attr_unique_id = "ai_copilot_anomaly_alert"
    _attr_icon = "mdi:alert-octagon"

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the anomaly alert sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self) -> str:
        """Return the current alert status."""
        if not self.coordinator.data:
            return "idle"

        anomaly_status = self.coordinator.data.get("anomaly_status", {})

        if anomaly_status.get("status") == "active":
            summary = anomaly_status.get("summary", {})
            if summary.get("count", 0) > 0:
                return "active"
            return "healthy"

        return "idle"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return anomaly detection details."""
        if not self.coordinator.data:
            return {}

        anomaly_status = self.coordinator.data.get("anomaly_status", {})

        return {
            "status": anomaly_status.get("status", "unknown"),
            "features": anomaly_status.get("features", []),
            "last_anomaly": anomaly_status.get("summary", {}).get("last_anomaly"),
            "peak_score": anomaly_status.get("summary", {}).get("peak_score", 0),
            "anomaly_count": anomaly_status.get("summary", {}).get("count", 0),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class AlertHistorySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing recent alert history."""

    _attr_name = "PilotSuite Alert History"
    _attr_unique_id = "ai_copilot_alert_history"
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the alert history sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self) -> str:
        """Return the count of recent alerts."""
        if not self.coordinator.data:
            return "0"

        alert_history = self.coordinator.data.get("alert_history", [])
        return str(len(alert_history))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return recent alert history."""
        if not self.coordinator.data:
            return {}

        alert_history = self.coordinator.data.get("alert_history", [])

        return {
            "alerts": [
                {
                    "timestamp": a.get("timestamp", a.get("detected_at", 0)),
                    "score": a.get("score", 0),
                    "is_anomaly": a.get("is_anomaly", True),
                    "device_id": a.get("device_id", a.get("entity_id", "")),
                    "severity": a.get("severity", "info"),
                    "anomaly_type": a.get("anomaly_type", ""),
                }
                for a in alert_history[-50:]
            ],
            "count": len(alert_history),
            "recent_anomalies": len(alert_history),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up anomaly alert sensors from a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    sensors = [
        AnomalyAlertSensor(coordinator),
        AlertHistorySensor(coordinator),
    ]

    async_add_entities(sensors)

    _LOGGER.info("Anomaly alert sensors set up for entry %s", entry.entry_id)
