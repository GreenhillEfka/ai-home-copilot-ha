"""Demand Response Sensor for Home Assistant (v5.14.0).

Exposes demand response status as an HA sensor.
State shows current grid signal level.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

SIGNAL_LABELS = {0: "Normal", 1: "Advisory", 2: "Moderate", 3: "Critical"}
SIGNAL_ICONS = {
    0: "mdi:transmission-tower",
    1: "mdi:alert-circle-outline",
    2: "mdi:alert",
    3: "mdi:alert-octagon",
}


def _safe_int(value: Any, default: int = 0, upper: int | None = None) -> int:
    """Guard an integer read against non-numeric or non-finite payloads.

    Args:
        value: the value to coerce
        default: fallback when coercion fails or constraints fail
        upper: optional upper bound (values above are clamped to this)
    """
    try:
        v = float(value)
        if v != int(v) or v < 0:
            return default
        result = int(v)
        if upper is not None and result > upper:
            return default
        return result
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Guard a float read against non-numeric payloads."""
    try:
        f = float(value)
        if f < 0:
            return default
        return f
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    """Guard a bool read against non-bool payloads."""
    if isinstance(value, bool):
        return value
    return default


def _safe_signal(value: Any, default: int = 0) -> int:
    """Guard signal level against non-integer or out-of-range values.

    Valid signal levels are 0–3.
    """
    try:
        v = float(value)
        if v != int(v) or v < 0 or v > 3:
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


class DemandResponseSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing demand response status."""

    _attr_name = "Demand Response"
    _attr_unique_id = "copilot_demand_response"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}
        self._signal_level = 0

    @property
    def native_value(self) -> str:
        return SIGNAL_LABELS.get(self._signal_level, "Unknown")

    @property
    def icon(self) -> str:
        return SIGNAL_ICONS.get(self._signal_level, "mdi:transmission-tower")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "signal_level": self._signal_level,
            "active_signals": _safe_int(self._data.get("active_signals")),
            "managed_devices": _safe_int(self._data.get("managed_devices")),
            "curtailed_devices": _safe_int(self._data.get("curtailed_devices")),
            "total_reduction_watts": _safe_float(self._data.get("total_reduction_watts")),
            "response_active": _safe_bool(self._data.get("response_active")),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        url = f"{self._core_base_url()}/api/v1/energy/demand-response/status"
        headers = self._core_headers()
        try:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        self._data = data
                        self._signal_level = _safe_signal(data.get("current_signal"), default=0)
                else:
                    _LOGGER.warning("Demand response API returned %s", resp.status)
        except Exception as exc:
            _LOGGER.error("Failed to fetch demand response status: %s", exc)
