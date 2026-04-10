"""Battery Optimizer Sensor for Home Assistant (v5.23.0).

Exposes battery charge/discharge strategy as an HA sensor.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

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


def _as_int(val: Any, default: int) -> int:
    """Accept only finite integer-valued floats or ints; reject bool, inf, nan."""
    if isinstance(val, bool):
        return default
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, float) and math.isfinite(val) and val == int(val):
        return int(val)
    return default


def _as_string(val: Any, default: str) -> str:
    """Accept only non-empty strings."""
    if isinstance(val, str) and val:
        return val
    return default


# =============================================================================
# BatteryOptimizerSensor
# =============================================================================


class BatteryOptimizerSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing battery optimization strategy and status."""

    _attr_name = "Battery Strategy"
    _attr_unique_id = "copilot_battery_strategy"
    _attr_icon = "mdi:battery-charging"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._status: dict[str, Any] = {}
        self._schedule: dict[str, Any] = {}

    @property
    def native_value(self) -> float | None:
        status = _as_mapping(self._status)
        return _as_float(status.get("soc_pct"), None)

    @property
    def icon(self) -> str:
        status = _as_mapping(self._status)
        soc = _as_float(status.get("soc_pct"), 50)
        action = _as_string(status.get("current_action"), "hold")
        if action in ("charge", "charge_solar"):
            return "mdi:battery-charging"
        elif action == "discharge":
            return "mdi:battery-arrow-down"
        elif soc >= 80:
            return "mdi:battery-high"
        elif soc >= 30:
            return "mdi:battery-medium"
        return "mdi:battery-low"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = _as_mapping(self._status)
        schedule = _as_mapping(self._schedule)
        attrs = {
            "soc_pct": _as_float(status.get("soc_pct"), 0.0),
            "soc_kwh": _as_float(status.get("soc_kwh"), 0.0),
            "capacity_kwh": _as_float(status.get("capacity_kwh"), 0.0),
            "current_action": _as_string(status.get("current_action"), "hold"),
            "current_power_kw": _as_float(status.get("current_power_kw"), 0.0),
            "strategy": _as_string(status.get("strategy"), "none"),
            "cycles_today": _as_int(status.get("cycles_today"), 0),
            "next_charge_at": _as_string(status.get("next_charge_at"), ""),
            "next_discharge_at": _as_string(status.get("next_discharge_at"), ""),
            "health_pct": _as_int(status.get("health_pct"), 100),
        }
        if schedule:
            attrs["estimated_savings_eur"] = _as_float(schedule.get("estimated_savings_eur"), 0.0)
            attrs["total_charge_kwh"] = _as_float(schedule.get("total_charge_kwh"), 0.0)
            attrs["total_discharge_kwh"] = _as_float(schedule.get("total_discharge_kwh"), 0.0)
            attrs["total_solar_charge_kwh"] = _as_float(schedule.get("total_solar_charge_kwh"), 0.0)
            attrs["estimated_cycles"] = _as_float(schedule.get("estimated_cycles"), 0.0)
            attrs["avg_charge_price_ct"] = _as_float(schedule.get("avg_charge_price_ct"), 0.0)
            attrs["avg_discharge_price_ct"] = _as_float(schedule.get("avg_discharge_price_ct"), 0.0)
        return attrs

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/regional"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/battery/status", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._status = data

            async with session.get(
                f"{base}/battery/schedule", headers=headers, timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._schedule = data
        except Exception as exc:
            _LOGGER.debug("Failed to fetch battery data: %s", exc)
