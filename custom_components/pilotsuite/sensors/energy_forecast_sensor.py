"""Energy Forecast Sensor for Home Assistant (v5.20.0).

Exposes 48h energy forecast with PV, prices, and recommendations
as an HA sensor for dashboard integration.
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
# Module-level type guards — mirror pattern from HA-176..HA-356
# =============================================================================


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return value as dict, or empty dict if not a mapping."""
    if isinstance(value, dict):
        return value
    return {}


def _as_float(value: Any, default: float = 0.0) -> float:
    """Coerce value to finite float, rejecting bools and non-finite numbers."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return default


def _as_int(value: Any, default: int = 0) -> int:
    """Coerce value to int, rejecting bools and non-integer floats."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return int(value)
        return default
    return default


def _as_list(value: Any) -> list[Any]:
    """Return value as list, or empty list if not a list."""
    if isinstance(value, list):
        return value
    return []


def _as_str(value: Any, default: str = "") -> str:
    """Coerce value to non-blank string."""
    if isinstance(value, str):
        s = value.strip()
        if s:
            return s
    return default


# =============================================================================
# Energy Forecast Sensor
# =============================================================================


class EnergyForecastSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing 48h energy forecast summary."""

    _attr_name = "Energy Forecast"
    _attr_unique_id = "pilotsuite_energy_forecast"
    _attr_icon = "mdi:chart-timeline-variant"
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> float | None:
        summary = _as_mapping(self._data.get("summary"))
        return _as_float(summary.get("total_pv_kwh_estimated"), default=0.0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = _as_mapping(self._data.get("summary"))
        cards = _as_list(self._data.get("cards"))

        return {
            "total_hours": _as_int(summary.get("total_hours"), 0),
            "avg_price_ct_kwh": _as_float(summary.get("avg_price_ct"), 0.0),
            "min_price_ct_kwh": _as_float(summary.get("min_price_ct"), 0.0),
            "max_price_ct_kwh": _as_float(summary.get("max_price_ct"), 0.0),
            "cheapest_hour": _as_str(summary.get("cheapest_hour"), ""),
            "most_expensive_hour": _as_str(summary.get("most_expensive_hour"), ""),
            "daylight_hours": _as_int(summary.get("daylight_hours"), 0),
            "avg_pv_factor": _as_float(summary.get("avg_pv_factor"), 0.0),
            "best_charge_window": _as_str(summary.get("best_charge_window"), ""),
            "best_consume_window": _as_str(summary.get("best_consume_window"), ""),
            "weather_impacted_hours": _as_int(summary.get("weather_impacted_hours"), 0),
            "card_count": len(cards),
            "generated_at": _as_str(self._data.get("generated_at"), ""),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/regional"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/forecast/dashboard", headers=headers, timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._data = data
        except Exception as exc:
            _LOGGER.error("Failed to fetch energy forecast: %s", exc)
