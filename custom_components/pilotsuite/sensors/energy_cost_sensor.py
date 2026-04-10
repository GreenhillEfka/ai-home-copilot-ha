"""Energy Cost Sensor for PilotSuite (v5.10.0).

Exposes energy cost data as a HA sensor with daily cost, budget status,
and period comparison in attributes.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# Guard helpers
# =============================================================================


def _as_mapping(val: Any) -> dict[str, Any]:
    """Reject non-dict payloads."""
    if isinstance(val, dict):
        return val
    return {}


def _as_float(val: Any, default: float | None) -> float | None:
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
    if isinstance(val, int):
        return val
    if isinstance(val, float) and math.isfinite(val) and val == int(val):
        return int(val)
    return default


def _as_string(val: Any, default: str | None) -> str | None:
    """Accept only non-empty strings."""
    if isinstance(val, str) and val.strip():
        return val.strip()
    return default


def _as_bool(val: Any, default: bool) -> bool:
    """Accept only bool values."""
    if isinstance(val, bool):
        return val
    return default


class EnergyCostSensor(CopilotBaseEntity):
    """Sensor exposing energy cost tracking from Core."""

    _attr_name = "Energy Cost"
    _attr_icon = "mdi:currency-eur"
    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "copilot_energy_cost"
        self._summary_data: dict[str, Any] | None = None
        self._budget_data: dict[str, Any] | None = None

    @property
    def native_value(self) -> float | None:
        """Return weekly cost as state."""
        summary = _as_mapping(self._summary_data)
        if summary and summary.get("ok"):
            return _as_float(summary.get("total_cost_eur"), None)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return cost details."""
        attrs: dict[str, Any] = {
            "costs_url": f"{self._core_base_url()}/api/v1/energy/costs",
            "budget_url": f"{self._core_base_url()}/api/v1/energy/costs/budget",
        }

        summary = _as_mapping(self._summary_data)
        if summary and summary.get("ok"):
            attrs["period"] = _as_string(summary.get("period"), None)
            attrs["avg_daily_cost_eur"] = _as_float(summary.get("avg_daily_cost_eur"), 0.0)
            attrs["total_consumption_kwh"] = _as_float(summary.get("total_consumption_kwh"), 0.0)
            attrs["total_savings_eur"] = _as_float(summary.get("total_savings_eur"), 0.0)
            attrs["days_count"] = _as_int(summary.get("days_count"), 0)

        budget = _as_mapping(self._budget_data)
        if budget and budget.get("ok"):
            attrs["budget_eur"] = _as_float(budget.get("budget_eur"), 0.0)
            attrs["budget_spent_eur"] = _as_float(budget.get("spent_eur"), 0.0)
            attrs["budget_remaining_eur"] = _as_float(budget.get("remaining_eur"), 0.0)
            attrs["budget_percent_used"] = _as_float(budget.get("percent_used"), 0.0)
            attrs["budget_on_track"] = _as_bool(budget.get("on_track"), False)
            attrs["budget_projected_eur"] = _as_float(budget.get("projected_total_eur"), 0.0)

        return attrs

    async def async_update(self) -> None:
        """Fetch cost data from Core API."""
        try:
            session = self.coordinator._session
            if session is None:
                return

            headers = self._core_headers()
            base = f"{self._core_base_url()}"

            async with session.get(
                f"{base}/api/v1/energy/costs/summary?period=weekly",
                headers=headers,
                timeout=10,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._summary_data = _as_mapping(data)

            async with session.get(
                f"{base}/api/v1/energy/costs/budget",
                headers=headers,
                timeout=10,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._budget_data = _as_mapping(data)

        except Exception as e:
            _LOGGER.debug("Failed to fetch cost data: %s", e)
