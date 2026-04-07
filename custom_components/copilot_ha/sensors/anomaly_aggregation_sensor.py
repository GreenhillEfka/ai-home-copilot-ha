"""Anomaly Aggregation Sensor for Dashboard Widget — HA-155.

Aggregates all anomaly data from UnifiedAnomalyFramework into a single
dashboard-friendly sensor for the Anomaly Widget in the Lovelace UI.

Provides:
- Anomaly level distribution (normal/low/medium/high/critical counts)
- List of critical sensor IDs
- Most recent anomaly alerts
- Trend indicators
- Overall system health score

Slice HA-155 — 168h Massive Iteration (Wiring-Run RC1)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from ..anomaly_framework import (
    get_framework,
    AnomalyAlert,
    AnomalyLevel,
    UnifiedAnomalyFramework,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


class AnomalyAggregationSensor(RestoreEntity, SensorEntity):
    """Aggregated anomaly sensor for dashboard widget.

    Shows:
    - Overall health score (0-100)
    - Anomaly level counts
    - Critical sensor list
    - Recent alerts (last 10)
    - Trend (increasing/stable/decreasing)
    """

    _attr_name = "PilotSuite Anomaly Health"
    _attr_unique_id = "pilotsuite_anomaly_aggregation"
    _attr_icon = "mdi:shield-check"
    _attr_native_unit_of_measurement = "%"
    _attr_should_poll = True
    _attr_polling_interval = 60  # seconds

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the aggregation sensor."""
        super().__init__()
        self._hass = hass
        self._framework: Optional[UnifiedAnomalyFramework] = None
        self._health_score: float = 100.0
        self._level_counts: Dict[str, int] = {
            "normal": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }
        self._critical_sensors: List[str] = []
        self._recent_alerts: List[Dict[str, Any]] = []
        self._trend: str = "stable"
        self._last_update: Optional[datetime] = None

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.attributes:
            self._health_score = float(state.attributes.get("health_score", 100.0))
            self._level_counts = state.attributes.get("level_counts", self._level_counts)
            self._critical_sensors = state.attributes.get("critical_sensors", [])
            self._recent_alerts = state.attributes.get("recent_alerts", [])

    @property
    def native_value(self) -> float:
        """Return health score as state (0-100)."""
        return round(self._health_score, 1)

    @property
    def icon(self) -> str:
        """Return icon based on health score."""
        if self._health_score >= 90:
            return "mdi:shield-check"
        elif self._health_score >= 70:
            return "mdi:shield-sync"
        elif self._health_score >= 50:
            return "mdi:shield-alert"
        else:
            return "mdi:shield-warning"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return aggregated anomaly data for dashboard."""
        return {
            "health_score": round(self._health_score, 1),
            "level_counts": self._level_counts,
            "critical_sensors": self._critical_sensors,
            "critical_count": len(self._critical_sensors),
            "recent_alerts": self._recent_alerts,
            "trend": self._trend,
            "total_monitored": sum(self._level_counts.values()),
            "last_update": self._last_update.isoformat() if self._last_update else None,
        }

    async def async_update(self) -> None:
        """Update aggregation from framework."""
        try:
            if self._framework is None:
                self._framework = get_framework()

            summary = self._framework.get_summary()

            # Update level counts
            alerts = summary.get("alerts", [])
            self._level_counts = {
                "normal": 0,
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0,
            }

            critical_ids = []
            recent = []

            for alert in alerts:
                level_name = alert.level.value if isinstance(alert.level, AnomalyLevel) else str(alert.level)
                if level_name in self._level_counts:
                    self._level_counts[level_name] += 1

                if alert.level == AnomalyLevel.CRITICAL:
                    critical_ids.append(alert.sensor_id)

                recent.append({
                    "sensor_id": alert.sensor_id,
                    "metric": alert.metric,
                    "level": level_name,
                    "sigma": alert.deviation_sigma,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
                })

            # Sort recent by timestamp (newest first)
            recent.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
            self._recent_alerts = recent[:10]

            self._critical_sensors = critical_ids

            # Calculate health score
            # Weights: critical=-25, high=-15, medium=-8, low=-3, normal=+0
            total = len(alerts) if alerts else 1
            weighted_sum = (
                self._level_counts["critical"] * -25 +
                self._level_counts["high"] * -15 +
                self._level_counts["medium"] * -8 +
                self._level_counts["low"] * -3 +
                self._level_counts["normal"] * 0
            )
            self._health_score = max(0.0, min(100.0, 100.0 + weighted_sum / total))

            # Calculate trend (based on recent critical count change)
            prev_critical = len([a for a in self._recent_alerts if a.get("level") == "critical"])
            if len(critical_ids) > prev_critical:
                self._trend = "increasing"
            elif len(critical_ids) < prev_critical:
                self._trend = "decreasing"
            else:
                self._trend = "stable"

            self._last_update = datetime.now()

        except Exception as exc:
            _LOGGER.error("Failed to update anomaly aggregation: %s", exc)
            self._health_score = max(0.0, self._health_score - 1)  # Slowly degrade on error


# ─── Individual Anomaly Level Sensors ───────────────────────────────────────


class AnomalyCriticalCountSensor(SensorEntity):
    """Sensor showing count of critical anomalies."""

    _attr_name = "PilotSuite Anomaly Critical Count"
    _attr_unique_id = "pilotsuite_anomaly_critical_count"
    _attr_icon = "mdi:alert-octagon"
    _attr_native_unit_of_measurement = "alerts"

    def __init__(self, framework: UnifiedAnomalyFramework) -> None:
        super().__init__()
        self._framework = framework

    @property
    def native_value(self) -> int:
        summary = self._framework.get_summary()
        return sum(1 for a in summary.get("alerts", []) if a.level == AnomalyLevel.CRITICAL)


class AnomalyHighCountSensor(SensorEntity):
    """Sensor showing count of high anomalies."""

    _attr_name = "PilotSuite Anomaly High Count"
    _attr_unique_id = "pilotsuite_anomaly_high_count"
    _attr_icon = "mdi:alert"
    _attr_native_unit_of_measurement = "alerts"

    def __init__(self, framework: UnifiedAnomalyFramework) -> None:
        super().__init__()
        self._framework = framework

    @property
    def native_value(self) -> int:
        summary = self._framework.get_summary()
        return sum(1 for a in summary.get("alerts", []) if a.level == AnomalyLevel.HIGH)


class AnomalyMediumCountSensor(SensorEntity):
    """Sensor showing count of medium anomalies."""

    _attr_name = "PilotSuite Anomaly Medium Count"
    _attr_unique_id = "pilotsuite_anomaly_medium_count"
    _attr_icon = "mdi:alert-circle"
    _attr_native_unit_of_measurement = "alerts"

    def __init__(self, framework: UnifiedAnomalyFramework) -> None:
        super().__init__()
        self._framework = framework

    @property
    def native_value(self) -> int:
        summary = self._framework.get_summary()
        return sum(1 for a in summary.get("alerts", []) if a.level == AnomalyLevel.MEDIUM)


class AnomalyHealthScoreSensor(SensorEntity):
    """Sensor showing overall system health score (0-100)."""

    _attr_name = "PilotSuite System Health Score"
    _attr_unique_id = "pilotsuite_system_health_score"
    _attr_icon = "mdi:heart-pulse"
    _attr_native_unit_of_measurement = "%"
    _attr_should_poll = True
    _attr_polling_interval = 60

    def __init__(self, framework: UnifiedAnomalyFramework) -> None:
        super().__init__()
        self._framework = framework

    @property
    def native_value(self) -> float:
        summary = self._framework.get_summary()
        alerts = summary.get("alerts", [])
        if not alerts:
            return 100.0

        total = len(alerts)
        critical = sum(1 for a in alerts if a.level == AnomalyLevel.CRITICAL)
        high = sum(1 for a in alerts if a.level == AnomalyLevel.HIGH)
        medium = sum(1 for a in alerts if a.level == AnomalyLevel.MEDIUM)
        low = sum(1 for a in alerts if a.level == AnomalyLevel.LOW)

        weighted_sum = critical * -25 + high * -15 + medium * -8 + low * -3
        return max(0.0, min(100.0, 100.0 + weighted_sum / total))


class AnomalyCriticalListSensor(SensorEntity):
    """Sensor showing list of critical sensor IDs as JSON."""

    _attr_name = "PilotSuite Critical Sensors"
    _attr_unique_id = "pilotsuite_critical_sensors"
    _attr_icon = "mdi:alert-octagon"

    def __init__(self, framework: UnifiedAnomalyFramework) -> None:
        super().__init__()
        self._framework = framework

    @property
    def native_value(self) -> str:
        summary = self._framework.get_summary()
        critical_ids = [a.sensor_id for a in summary.get("alerts", []) if a.level == AnomalyLevel.CRITICAL]
        return ", ".join(critical_ids) if critical_ids else "None"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        summary = self._framework.get_summary()
        return {
            "critical_count": sum(1 for a in summary.get("alerts", []) if a.level == AnomalyLevel.CRITICAL),
            "critical_sensors": [a.sensor_id for a in summary.get("alerts", []) if a.level == AnomalyLevel.CRITICAL],
        }


# ─── Registry ────────────────────────────────────────────────────────────────


async def async_setup_anomaly_sensors(hass: HomeAssistant) -> None:
    """Set up all anomaly aggregation sensors.

    Call from __init__.py async_setup_entry.
    """
    framework = get_framework()

    sensors = [
        AnomalyAggregationSensor(hass),
        AnomalyHealthScoreSensor(framework),
        AnomalyCriticalCountSensor(framework),
        AnomalyHighCountSensor(framework),
        AnomalyMediumCountSensor(framework),
        AnomalyCriticalListSensor(framework),
    ]

    for sensor in sensors:
        hass.async_add_entity(sensor)

    _LOGGER.info("Anomaly aggregation sensors registered: %d", len(sensors))
