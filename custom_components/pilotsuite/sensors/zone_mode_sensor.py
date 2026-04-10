"""Zone Mode Sensor for PilotSuite HA Integration (v6.6.0).

Displays active zone modes with quick-toggle overview.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

_ICON_MAP = {
    "party": "mdi:party-popper",
    "kids_sleep": "mdi:baby-face-outline",
    "movie": "mdi:movie-open",
    "guest": "mdi:account-group",
    "focus": "mdi:head-lightbulb",
    "away": "mdi:home-export-outline",
    "night": "mdi:weather-night",
    "romantic": "mdi:heart",
}


def _as_list(value: Any, default: list[Any] | None = None) -> list[Any]:
    """Return value as list, falling back to default if not a list."""
    if isinstance(value, list):
        return value
    return default if default is not None else []


class ZoneModeSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing active zone modes overview."""

    _attr_name = "Zone Modes"
    _attr_icon = "mdi:toggle-switch"
    _attr_unique_id = "pilotsuite_zone_modes"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        import aiohttp
        try:
            url = f"{self._core_base_url()}/api/v1/hub/modes"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch zone modes data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        if not self._data or not self._data.get("ok"):
            return "Keine aktiven Modi"
        active = _as_list(self._data.get("active_modes"))
        if not active:
            return "Keine aktiven Modi"
        if len(active) == 1:
            return active[0].get("mode_name_de", active[0].get("mode_id", "Aktiv"))
        return f"{len(active)} Modi aktiv"

    @property
    def icon(self) -> str:
        if not self._data:
            return "mdi:toggle-switch-off"
        active = _as_list(self._data.get("active_modes"))
        if not active:
            return "mdi:toggle-switch-off"
        if len(active) == 1:
            mode_id = active[0].get("mode_id", "")
            return _ICON_MAP.get(mode_id, active[0].get("icon", "mdi:toggle-switch"))
        return "mdi:toggle-switch-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self._data:
            return {"active_count": 0, "available_count": 0, "total_zones_with_modes": 0}
        raw_active = _as_list(self._data.get("active_modes"))
        raw_available = _as_list(self._data.get("available_modes"))
        recent = _as_list(self._data.get("recent_events"))

        active = [m for m in raw_active if isinstance(m, dict)]
        available = [m for m in raw_available if isinstance(m, dict)]

        attrs: dict[str, Any] = {
            "active_count": len(active),
            "available_count": len(available),
            "total_zones_with_modes": self._data.get("total_zones_with_modes", 0) or 0,
        }

        if active:
            attrs["active_modes"] = [
                {
                    "zone": m.get("zone_id"),
                    "mode": m.get("mode_id"),
                    "name_de": m.get("mode_name_de"),
                    "remaining_min": m.get("remaining_min"),
                    "activated_by": m.get("activated_by"),
                }
                for m in active
            ]

        if available:
            attrs["available_modes"] = [
                {
                    "mode_id": m.get("mode_id"),
                    "name_de": m.get("name_de"),
                    "icon": m.get("icon"),
                    "duration_min": m.get("default_duration_min"),
                }
                for m in available
            ]

        if recent:
            attrs["recent_events"] = recent[:10]

        return attrs
