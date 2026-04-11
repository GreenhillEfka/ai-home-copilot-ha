"""Weather-Aware Optimizer Sensor for Home Assistant (v5.11.0).

Exposes the 48-hour weather-aware optimization plan as an HA sensor entity.
State shows the number of optimal consumption windows found.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


def _as_mapping(value: Any) -> dict:
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    """Return list-like payloads, otherwise a safe empty list."""
    return value if isinstance(value, list) else []


def _as_int(value: Any, default: int) -> int:
    """Return integer payloads, otherwise a safe default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _as_float(value: Any, default: float) -> float:
    """Return finite numeric payloads, otherwise a safe default."""
    import math
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        numeric_value = float(value)
        return numeric_value if math.isfinite(numeric_value) else default
    return default


class WeatherOptimizerSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing weather-aware energy optimization status."""

    _attr_name = "Weather Optimizer"
    _attr_unique_id = "copilot_weather_optimizer"
    _attr_icon = "mdi:weather-sunny-alert"
    _attr_native_unit_of_measurement = "windows"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> int:
        return _as_int(self._data.get("optimal_windows_count"), 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        summary = _as_mapping(self._data.get("summary"))
        top_windows = _as_list(self._data.get("top_windows"))
        alerts = _as_list(self._data.get("alerts"))
        return {
            "total_pv_kwh": _as_float(summary.get("total_pv_kwh"), 0.0),
            "avg_price_eur_kwh": _as_float(summary.get("avg_price_eur_kwh"), 0.0),
            "best_hours": _as_list(summary.get("best_hours")),
            "worst_hours": _as_list(summary.get("worst_hours")),
            "pv_self_consumption_pct": _as_float(summary.get("pv_self_consumption_potential_pct"), 0.0),
            "alerts": alerts,
            "top_windows": top_windows[:3],
            "battery_actions": _as_int(self._data.get("battery_plan_count"), 0),
            "horizon_hours": _as_int(self._data.get("horizon_hours"), 0),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        url = f"{self._core_base_url()}/api/v1/predict/weather-optimize"
        try:
            headers = self._core_headers()
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and data.get("ok"):
                        self._data = data
                        self._data["optimal_windows_count"] = _as_int(
                            _as_mapping(data.get("summary")).get("optimal_windows_count"), 0
                        )
                else:
                    _LOGGER.warning("Weather optimizer API returned %s", resp.status)
        except Exception as exc:
            _LOGGER.error("Failed to fetch weather optimizer data: %s", exc)
