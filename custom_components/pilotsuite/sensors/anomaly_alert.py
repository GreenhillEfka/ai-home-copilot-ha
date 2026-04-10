"""Anomaly Alert Sensor for PilotSuite.

Shows real-time anomaly detection status from Core anomaly detection engine.
Uses CoordinatorEntity pattern for automatic updates via coordinator.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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


def _as_list(val: Any) -> list:
    """Accept only list payloads."""
    if isinstance(val, list):
        return val
    return []


# =============================================================================
# AnomalyAlertSensor
# =============================================================================

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
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "idle"

        anomaly_status = _as_mapping(data.get("anomaly_status", {}))
        status = anomaly_status.get("status")

        if status == "active":
            summary = _as_mapping(anomaly_status.get("summary", {}))
            count = summary.get("count", 0)
            if isinstance(count, (int, float)) and count > 0:
                return "active"
            return "healthy"

        return "idle"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return anomaly detection details."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}

        anomaly_status = _as_mapping(data.get("anomaly_status", {}))
        summary = _as_mapping(anomaly_status.get("summary", {}))

        features_raw = anomaly_status.get("features")
        features = _as_list(features_raw) if features_raw is not None else []

        return {
            "status": anomaly_status.get("status", "unknown"),
            "features": features,
            "last_anomaly": summary.get("last_anomaly"),
            "peak_score": summary.get("peak_score", 0),
            "anomaly_count": summary.get("count", 0),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


# =============================================================================
# AlertHistorySensor
# =============================================================================

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
        data = _as_mapping(self.coordinator.data)
        if not data:
            return "0"

        alert_history = _as_list(data.get("alert_history", []))
        return str(len(alert_history))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return recent alert history."""
        data = _as_mapping(self.coordinator.data)
        if not data:
            return {}

        alert_history = _as_list(data.get("alert_history", []))

        def _guard_item(a: Any) -> dict:
            if not isinstance(a, dict):
                return {
                    "timestamp": 0,
                    "score": 0,
                    "is_anomaly": True,
                    "device_id": "",
                    "severity": "info",
                    "anomaly_type": "",
                }
            ts = a.get("timestamp") if a.get("timestamp") is not None else a.get("detected_at", 0)
            return {
                "timestamp": ts if isinstance(ts, (int, float)) else 0,
                "score": a.get("score", 0) if isinstance(a.get("score"), (int, float)) else 0,
                "is_anomaly": bool(a.get("is_anomaly")) if a.get("is_anomaly") is not None else True,
                "device_id": a.get("device_id", a.get("entity_id", "")) if isinstance(a.get("device_id", a.get("entity_id", "")), str) else "",
                "severity": a.get("severity", "info") if isinstance(a.get("severity", "info"), str) else "info",
                "anomaly_type": a.get("anomaly_type", "") if isinstance(a.get("anomaly_type", ""), str) else "",
            }

        return {
            "alerts": [_guard_item(a) for a in alert_history[-50:]],
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
