"""Scene Intelligence Sensor for PilotSuite HA Integration (v7.0.0).

Displays active scene, suggestions, cloud status, and pattern learning info.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

_ICON_MAP = {
    "morning_routine": "mdi:weather-sunny",
    "work_focus": "mdi:head-lightbulb",
    "lunch_break": "mdi:food",
    "afternoon_relax": "mdi:sofa",
    "dinner_time": "mdi:silverware-fork-knife",
    "movie_night": "mdi:movie-open",
    "romantic_evening": "mdi:heart",
    "bedtime": "mdi:bed",
    "party": "mdi:party-popper",
    "away": "mdi:home-export-outline",
}


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        numeric_value = float(value)
        return numeric_value if math.isfinite(numeric_value) else default
    return default


def _as_string(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


class SceneIntelligenceSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing scene intelligence overview."""

    _attr_name = "Scene Intelligence"
    _attr_icon = "mdi:palette"
    _attr_unique_id = "pilotsuite_scene_intelligence"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        import aiohttp

        try:
            url = f"{self._core_base_url()}/api/v1/hub/scenes"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch scene intelligence data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        if isinstance(data, dict) and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        active = _as_mapping(self._data.get("active_scene"))
        if active:
            return _as_string(active.get("name_de"), "Aktive Szene")

        total = _as_int(self._data.get("total_scenes"), 0)
        if total == 0:
            return "Nicht verfügbar"
        return f"{total} Szenen verfügbar"

    @property
    def icon(self) -> str:
        active = _as_mapping(self._data.get("active_scene"))
        if active:
            return _ICON_MAP.get(_as_string(active.get("scene_id")), "mdi:palette")
        return "mdi:palette"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "total_scenes": _as_int(self._data.get("total_scenes"), 0),
            "learned_patterns": _as_int(self._data.get("learned_patterns"), 0),
        }

        active = _as_mapping(self._data.get("active_scene"))
        if active:
            scene_id = _as_string(active.get("scene_id"))
            scene_name = _as_string(active.get("name_de"))
            zone_id = _as_string(active.get("zone_id"))
            if scene_id:
                attrs["active_scene_id"] = scene_id
            if scene_name:
                attrs["active_scene_name"] = scene_name
            if zone_id:
                attrs["active_zone"] = zone_id

        suggestions = _as_list(self._data.get("suggestions"))
        if suggestions:
            projected_suggestions = []
            for suggestion in suggestions[:3]:
                if not isinstance(suggestion, dict):
                    continue
                projected_suggestions.append(
                    {
                        "scene": _as_string(suggestion.get("name_de")),
                        "confidence": _as_float(suggestion.get("confidence"), 0.0),
                        "reason": _as_string(suggestion.get("reason_de")),
                        "icon": _as_string(suggestion.get("icon")),
                    }
                )
            if projected_suggestions:
                attrs["suggestions"] = projected_suggestions

        cloud = _as_mapping(self._data.get("cloud_status"))
        if cloud:
            attrs["cloud_connected"] = _as_bool(cloud.get("connected"), False)
            attrs["cloud_shared_scenes"] = _as_int(cloud.get("shared_scenes"), 0)

        categories = _as_mapping(self._data.get("categories"))
        if categories:
            attrs["categories"] = categories

        return attrs
