"""EV Charging Sensor for Home Assistant (v5.25.0).

Exposes EV charging planner state as an HA sensor.
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
# Type-safe payload helpers
# =============================================================================


def _as_mapping(value: Any) -> dict:
    """Return value as a dict, or empty dict if not a dict."""
    if isinstance(value, dict):
        return value
    return {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Coerce value to a finite float, falling back to default."""
    try:
        result = float(value)
        if math.isfinite(result):
            return result
    except (TypeError, ValueError):
        pass
    return default


def _safe_string(value: Any, default: str = "") -> str:
    """Coerce value to a trimmed string, falling back to default if blank."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


class EVChargingSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing EV charging status and schedule."""

    _attr_name = "EV Charging"
    _attr_unique_id = "copilot_ev_charging"
    _attr_icon = "mdi:ev-station"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._status: dict[str, Any] = {}
        self._schedule: dict[str, Any] = {}

    @property
    def native_value(self) -> float | None:
        status = _as_mapping(self._status)
        return _safe_float(status.get("current_soc_pct"), default=None)

    @property
    def icon(self) -> str:
        status = _as_mapping(self._status)
        action = _safe_string(status.get("current_action"), default="idle")
        if action == "charge":
            return "mdi:ev-station"
        elif action == "solar_charge":
            return "mdi:solar-power-variant"
        elif status.get("departure_ready"):
            return "mdi:car-electric"
        return "mdi:car-electric-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = _as_mapping(self._status)
        attrs = {
            "vehicle_name": _safe_string(status.get("vehicle_name"), default="EV"),
            "connector_type": _safe_string(status.get("connector_type"), default="type2"),
            "current_soc_pct": _safe_float(status.get("current_soc_pct"), default=0.0),
            "target_soc_pct": _safe_float(status.get("target_soc_pct"), default=80.0),
            "current_action": _safe_string(status.get("current_action"), default="idle"),
            "current_power_kw": _safe_float(status.get("current_power_kw"), default=0.0),
            "energy_charged_kwh": _safe_float(status.get("energy_charged_kwh"), default=0.0),
            "cost_so_far_eur": _safe_float(status.get("cost_so_far_eur"), default=0.0),
            "estimated_range_km": _safe_float(status.get("estimated_range_km"), default=0.0),
            "time_to_target_h": _safe_float(status.get("time_to_target_h"), default=0.0),
            "next_departure": _safe_string(status.get("next_departure"), default=""),
            "departure_ready": bool(status.get("departure_ready")),
            "strategy": _safe_string(status.get("strategy"), default="cost_optimized"),
        }

        schedule = _as_mapping(self._schedule)
        if schedule:
            attrs["total_energy_kwh"] = _safe_float(schedule.get("total_energy_kwh"), default=0.0)
            attrs["total_cost_eur"] = _safe_float(schedule.get("total_cost_eur"), default=0.0)
            attrs["solar_energy_kwh"] = _safe_float(schedule.get("solar_energy_kwh"), default=0.0)
            attrs["grid_energy_kwh"] = _safe_float(schedule.get("grid_energy_kwh"), default=0.0)
            attrs["solar_share_pct"] = _safe_float(schedule.get("solar_share_pct"), default=0.0)
            attrs["avg_price_ct"] = _safe_float(schedule.get("avg_price_ct"), default=0.0)
            attrs["charge_hours"] = _safe_float(schedule.get("charge_hours"), default=0.0)

        return attrs

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/regional"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/ev/status", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._status = data

            async with session.get(
                f"{base}/ev/schedule", headers=headers, timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._schedule = data
        except Exception as exc:
            _LOGGER.debug("Failed to fetch EV charging data: %s", exc)
