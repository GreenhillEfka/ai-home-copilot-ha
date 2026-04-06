"""Predictive Maintenance Sensor for Home Assistant (v6.2.0).

Uses UnifiedAnomalyFramework for sigma-deviation based anomaly detection
with rolling 7-day baseline learning per device.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity
from ..anomaly_framework import get_framework, AnomalyLevel

_LOGGER = logging.getLogger(__name__)


class PredictiveMaintenanceSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing predictive maintenance summary with confidence scoring."""

    _attr_name = "Device Health"
    _attr_unique_id = "copilot_device_health"
    _attr_icon = "mdi:wrench-cog"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._summary: dict[str, Any] = {}
        self._framework = None

    @property
    def native_value(self) -> float | None:
        return self._summary.get("avg_health_score")

    @property
    def icon(self) -> str:
        critical = self._summary.get("critical", 0)
        warning = self._summary.get("warning", 0)
        if critical > 0:
            return "mdi:wrench-clock"
        elif warning > 0:
            return "mdi:wrench-cog"
        return "mdi:check-decagram"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {
            "total_devices": self._summary.get("total_devices", 0),
            "healthy": self._summary.get("healthy", 0),
            "degraded": self._summary.get("degraded", 0),
            "warning": self._summary.get("warning", 0),
            "critical": self._summary.get("critical", 0),
            "avg_health_score": self._summary.get("avg_health_score", 100),
            "devices_needing_attention": self._summary.get("devices_needing_attention", []),
            "upcoming_maintenance": self._summary.get("upcoming_maintenance", []),
            # New: failure predictions
            "failure_predictions_48h": self._get_failure_predictions(),
            "maintenance_confidence": self._get_confidence_score(),
        }

        # Add per-device breakdown with sigma-deviation info
        devices = self._summary.get("devices_needing_attention", [])
        if devices and self._framework:
            device_breakdown = []
            for device in devices[:10]:
                dev_id = device.get("entity_id", "")
                if dev_id and self._framework:
                    dev_alerts = [
                        a for a in self._framework._alerts
                        if a.sensor_id == dev_id and a.sensor_type == "maintenance"
                    ]
                    if dev_alerts:
                        latest = dev_alerts[-1]
                        device_breakdown.append({
                            "entity_id": dev_id,
                            "confidence": latest.confidence,
                            "level": latest.level.value,
                            "deviation_sigma": latest.deviation_sigma,
                            "failure_48h": latest.predicted_48h,
                        })
            attrs["device_anomaly_details"] = device_breakdown

        return attrs

    def _get_failure_predictions(self) -> list[str]:
        if not self._framework:
            return []
        return self._framework.get_summary().get("failure_prediction_48h", [])

    def _get_confidence_score(self) -> float:
        """Overall confidence 0-100 based on alert levels."""
        if not self._framework:
            return 0.0
        summary = self._framework.get_summary()
        # Weight critical alerts higher
        score = summary["critical"] * 30 + summary["high"] * 20
        score += summary["medium"] * 10 + summary["low"] * 5
        return min(100.0, score)

    async def async_update(self) -> None:
        # Get framework for failure predictions
        self._framework = get_framework(self.hass)

        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/hub"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/maintenance", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        self._summary = data

                        # Feed maintenance data into anomaly framework
                        devices = data.get("devices_needing_attention", [])
                        for device in devices:
                            energy = device.get("energy_delta_pct", 0)
                            if energy:
                                self._framework.record(
                                    sensor_type="maintenance",
                                    sensor_id=device.get("entity_id", "unknown"),
                                    metric="energy_delta_pct",
                                    value=float(energy),
                                )
        except Exception as exc:
            _LOGGER.debug("Failed to fetch maintenance data: %s", exc)


class MaintenanceConfidenceSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing maintenance confidence score 0-100."""

    _attr_name = "PilotSuite Maintenance Confidence"
    _attr_unique_id = "pilotsuite_maintenance_confidence"
    _attr_icon = "mdi:gauge"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._confidence = 0.0

    @property
    def native_value(self) -> float:
        return round(self._confidence, 1)

    async def async_update(self) -> None:
        framework = get_framework(self.hass)
        summary = framework.get_summary()
        self._confidence = min(100.0,
            summary["critical"] * 30 + summary["high"] * 20 +
            summary["medium"] * 10 + summary["low"] * 5
        )
