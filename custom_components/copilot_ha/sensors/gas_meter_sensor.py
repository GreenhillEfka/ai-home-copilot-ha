"""Gas Meter Sensor for Home Assistant (v6.4.0).

Uses UnifiedAnomalyFramework for sigma-deviation based anomaly detection.
Tracks gas consumption against learned 7-day baseline.
"""

from __future__ import annotations

import logging
from typing import Any

from ..entity import CopilotBaseEntity
from ..anomaly_framework import get_framework, AnomalyLevel

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 60


class GasMeterSensor(CopilotBaseEntity):
    """Sensor showing gas consumption and costs with anomaly detection."""

    _attr_icon = "mdi:meter-gas"
    _attr_name = "PilotSuite Gaszähler"
    _attr_unique_id = "pilotsuite_gas_meter"
    _attr_native_unit_of_measurement = "m³"
    _attr_device_class = "gas"
    _attr_state_class = "total_increasing"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._gas_data: dict[str, Any] = {}

    @property
    def state(self) -> float | None:
        return self._gas_data.get("current_meter_m3")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        today = self._gas_data.get("today", {})
        month = self._gas_data.get("month", {})
        forecast = self._gas_data.get("forecast_month", {})
        attrs = {
            "total_impulses": self._gas_data.get("total_impulses", 0),
            "today_m3": today.get("consumption_m3", 0),
            "today_kwh": today.get("consumption_kwh", 0),
            "today_cost_eur": today.get("cost_eur", 0),
            "month_m3": month.get("consumption_m3", 0),
            "month_kwh": month.get("consumption_kwh", 0),
            "month_cost_eur": month.get("cost_eur", 0),
            "forecast_month_eur": forecast.get("estimated_cost_eur", 0),
            "forecast_trend": forecast.get("trend", "stabil"),
            "gas_price_ct_kwh": self._gas_data.get("gas_price_ct_kwh", 0),
            "gas_price_eur_m3": self._gas_data.get("gas_price_eur_m3", 0),
            "calorific_value": self._gas_data.get("calorific_value", 0),
            # Anomaly framework integration
            "anomaly_framework_active": True,
        }

        # Add anomaly detection results
        framework = get_framework(self.hass)
        summary = framework.get_summary()
        gas_alerts = [a for a in framework._alerts if a.sensor_type == "gas"]
        if gas_alerts:
            latest = gas_alerts[-1]
            attrs.update({
                "gas_anomaly_level": latest.level.value,
                "gas_deviation_sigma": round(latest.deviation_sigma, 2),
                "gas_confidence": latest.confidence,
                "gas_failure_48h": latest.predicted_48h,
            })
        else:
            attrs["gas_anomaly_level"] = "normal"

        return attrs

    async def async_update(self) -> None:
        data = await self._fetch("/api/v1/regional/gas")
        if data:
            self._gas_data = data

            # Feed consumption into anomaly framework
            framework = get_framework(self.hass)
            today_m3 = data.get("today", {}).get("consumption_m3", 0)
            if today_m3:
                alert = framework.record(
                    sensor_type="gas",
                    sensor_id="gas_meter",
                    metric="consumption_m3_daily",
                    value=float(today_m3),
                )
                if alert:
                    logger.info(
                        "Gas anomaly detected: %.1fσ deviation, confidence %.0f%%, 48h预测: %s",
                        alert.deviation_sigma, alert.confidence, alert.predicted_48h
                    )


class GasAnomalySensor(CopilotBaseEntity):
    """Sensor showing gas consumption anomaly level."""

    _attr_icon = "mdi:alert-decagram"
    _attr_name = "PilotSuite Gas Anomaly"
    _attr_unique_id = "pilotsuite_gas_anomaly"
    _attr_state_class = "measurement"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._level = "normal"

    @property
    def state(self) -> str:
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
        framework = get_framework(self.hass)
        gas_alerts = [a for a in framework._alerts if a.sensor_type == "gas"]
        if gas_alerts:
            latest = gas_alerts[-1]
            return {
                "confidence": latest.confidence,
                "deviation_sigma": latest.deviation_sigma,
                "failure_prediction_48h": latest.predicted_48h,
                "baseline_mean": latest.baseline_mean,
                "current_value": latest.current_value,
                "message": latest.message,
            }
        return {"confidence": 0, "deviation_sigma": 0}

    async def async_update(self) -> None:
        framework = get_framework(self.hass)
        gas_alerts = [a for a in framework._alerts if a.sensor_type == "gas"]
        if gas_alerts:
            self._level = gas_alerts[-1].level.value
        else:
            self._level = "normal"
