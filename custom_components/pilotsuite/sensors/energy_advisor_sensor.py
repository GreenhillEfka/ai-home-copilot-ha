"""Energy Advisor Sensor for PilotSuite HA Integration (v6.8.0).

Displays eco-score, savings potential, and energy overview.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

_GRADE_ICONS = {
    "A+": "mdi:leaf",
    "A": "mdi:leaf",
    "B": "mdi:tree",
    "C": "mdi:flash",
    "D": "mdi:flash-alert",
    "E": "mdi:flash-alert-outline",
    "F": "mdi:lightning-bolt",
}


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return value as dict, or empty dict if not a dict."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    """Return value as list, or empty list if not a list."""
    return value if isinstance(value, list) else []


def _as_float(value: Any, default: float) -> float:
    """Return value as finite float, or default for non-numeric/bool/inf/nan."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    return value if math.isfinite(value) else default


def _as_int(value: Any, default: int) -> int:
    """Return value as int, or default for non-numeric/bool/inf/nan."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    if not math.isfinite(value):
        return default
    return int(value)


def _as_string(value: Any, default: str) -> str:
    """Return value as string, or default if not a string or blank."""
    if not isinstance(value, str):
        return default
    return value.strip() if value.strip() else default


class EnergyAdvisorSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing energy advisor eco-score and savings."""

    _attr_name = "Energy Advisor"
    _attr_icon = "mdi:leaf"
    _attr_unique_id = "pilotsuite_energy_advisor"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        import aiohttp
        try:
            url = f"{self._core_base_url()}/api/v1/hub/energy"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch energy advisor data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        # GC3: reject non-dict payloads; keep previous data on non-ok dict (silent ignore)
        if isinstance(data, dict) and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        data = _as_mapping(self._data)
        eco = _as_mapping(data.get("eco_score"))
        grade = _as_string(eco.get("grade"), "?")
        score = _as_int(eco.get("score"), 0)
        if not eco:
            return "Nicht verfügbar"
        return f"Eco-Score {grade} ({score}/100)"

    @property
    def icon(self) -> str:
        data = _as_mapping(self._data)
        eco = _as_mapping(data.get("eco_score"))
        grade = _as_string(eco.get("grade"), "C")
        return _GRADE_ICONS.get(grade, "mdi:flash")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        eco = _as_mapping(data.get("eco_score"))
        attrs: dict[str, Any] = {
            "eco_score": _as_int(eco.get("score"), 0),
            "eco_grade": _as_string(eco.get("grade"), "?"),
            "eco_trend": _as_string(eco.get("trend"), "stabil"),
            "total_daily_kwh": _as_float(data.get("total_daily_kwh"), 0.0),
            "total_monthly_kwh": _as_float(data.get("total_monthly_kwh"), 0.0),
            "total_monthly_eur": _as_float(data.get("total_monthly_eur"), 0.0),
            "savings_potential_eur": _as_float(data.get("savings_potential_eur"), 0.0),
        }

        breakdown_raw = data.get("breakdown")
        breakdown = _as_list(breakdown_raw)
        if breakdown:
            attrs["breakdown"] = [
                {
                    "category": _as_string(_as_mapping(b).get("name_de"), ""),
                    "kwh": _as_float(_as_mapping(b).get("kwh"), 0.0),
                    "pct": _as_float(_as_mapping(b).get("pct"), 0.0),
                }
                for b in breakdown
                if isinstance(b, dict)
            ]

        top_raw = data.get("top_consumers")
        top = _as_list(top_raw)
        if top:
            attrs["top_consumers"] = [
                {
                    "name": _as_string(_as_mapping(c).get("name"), ""),
                    "monthly_kwh": _as_float(_as_mapping(c).get("monthly_kwh"), 0.0),
                }
                for c in top[:5]
                if isinstance(c, dict)
            ]

        recs_raw = data.get("recommendations")
        recs = _as_list(recs_raw)
        if recs:
            attrs["recommendations"] = [
                {
                    "title": _as_string(_as_mapping(r).get("title_de"), ""),
                    "savings_eur": _as_float(_as_mapping(r).get("potential_savings_eur"), 0.0),
                    "difficulty": _as_string(_as_mapping(r).get("difficulty"), ""),
                    "applied": _as_mapping(r).get("applied"),
                }
                for r in recs[:5]
                if isinstance(r, dict)
            ]

        return attrs
