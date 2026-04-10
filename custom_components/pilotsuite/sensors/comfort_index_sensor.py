"""Comfort Index Sensor for PilotSuite (v5.7.0).

Exposes a composite comfort score (0-100) and lighting suggestions
as a Home Assistant sensor with rich attributes.
"""
from __future__ import annotations

import logging
from typing import Any

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


def _as_mapping(value, default=None):
    """Return value as dict, or default if not a dict-like."""
    if isinstance(value, dict):
        return value
    return default if default is not None else {}


def _as_list(value, default=None):
    """Return value as list, or default if not list-like."""
    if isinstance(value, list):
        return value
    return default if default is not None else []


def _as_string(value, default=""):
    """Return value as string, stripped, or default."""
    if isinstance(value, str):
        return value.strip()
    return default


def _as_float(value, default=None):
    """Return value as float, or default."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
        if v != v or v == float("inf") or v == float("-inf"):  # nan or inf
            return default
        return v
    return default


GRADE_ICONS = {
    "A": "mdi:emoticon-happy",
    "B": "mdi:emoticon",
    "C": "mdi:emoticon-neutral",
    "D": "mdi:emoticon-sad",
    "F": "mdi:emoticon-dead",
}


class ComfortIndexSensor(CopilotBaseEntity):
    """Sensor exposing comfort index from Core."""

    _attr_name = "Comfort Index"
    _attr_icon = "mdi:home-thermometer"
    _attr_native_unit_of_measurement = "points"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "copilot_comfort_index"
        self._comfort_data: dict[str, Any] | None = None

    @property
    def native_value(self) -> float | None:
        """Return comfort score as state."""
        if not self._comfort_data:
            return None
        data = _as_mapping(self._comfort_data)
        if not data.get("ok"):
            return None
        return _as_float(data.get("score"))

    @property
    def icon(self) -> str:
        """Return icon based on comfort grade."""
        if not self._comfort_data:
            return "mdi:home-thermometer"
        data = _as_mapping(self._comfort_data)
        if not data.get("ok"):
            return "mdi:home-thermometer"
        grade = _as_string(data.get("grade"), "")
        return GRADE_ICONS.get(grade, "mdi:home-thermometer")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return comfort details."""
        attrs: dict[str, Any] = {
            "comfort_url": (
                f"{self._core_base_url()}/api/v1/comfort"
            ),
            "lighting_url": (
                f"{self._core_base_url()}/api/v1/comfort/lighting"
            ),
        }

        if not self._comfort_data:
            return attrs
        data = _as_mapping(self._comfort_data)
        if not data.get("ok"):
            return attrs

        grade = _as_string(data.get("grade"), "")
        if grade:
            attrs["grade"] = grade
        zone_id = _as_string(data.get("zone_id"), "")
        if zone_id:
            attrs["zone_id"] = zone_id

        if "suggestions" in data and isinstance(data.get("suggestions"), list):
            attrs["suggestions"] = _as_list(data.get("suggestions"))

        readings = _as_list(data.get("readings"), [])
        for reading in readings:
            r = _as_mapping(reading, None)
            if r is None:
                continue
            factor = _as_string(r.get("factor"), "")
            if not factor:
                continue
            score = _as_float(r.get("score"))
            if score is not None:
                attrs[f"{factor}_score"] = score
            status = _as_string(r.get("status"), "")
            if status:
                attrs[f"{factor}_status"] = status
            raw = r.get("raw_value")
            if raw is not None and not isinstance(raw, dict):
                attrs[f"{factor}_value"] = raw

        return attrs

    async def async_update(self) -> None:
        """Fetch comfort index from Core API."""
        try:
            session = self.coordinator._session
            if session is None:
                return

            url = f"{self._core_base_url()}/api/v1/comfort"
            headers = self._core_headers()

            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    self._comfort_data = await resp.json()
                else:
                    _LOGGER.debug("Comfort API returned %s", resp.status)
        except Exception as e:
            _LOGGER.debug("Failed to fetch comfort data: %s", e)
