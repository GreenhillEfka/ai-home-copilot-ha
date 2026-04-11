"""Presence Intelligence Sensor for PilotSuite HA Integration (v7.1.0).

Displays household presence, room occupancy, and person tracking.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)


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


def _as_string(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


class PresenceIntelligenceSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing presence intelligence overview."""

    _attr_name = "Presence Intelligence"
    _attr_icon = "mdi:account-group"
    _attr_unique_id = "pilotsuite_presence_intelligence"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        import aiohttp

        try:
            url = f"{self._core_base_url()}/api/v1/hub/presence"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch presence intelligence data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        if isinstance(data, dict) and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        data = _as_mapping(self._data)
        total = _as_int(data.get("total_persons"), 0)
        home = _as_int(data.get("persons_home"), 0)
        status = _as_string(data.get("household_status"), "unknown")
        if total == 0:
            return "Nicht verfügbar"
        status_map = {
            "home": "Alle zu Hause",
            "away": "Alle abwesend",
            "partial": f"{home}/{total} zu Hause",
            "unknown": "Unbekannt",
        }
        return status_map.get(status, f"{home}/{total} zu Hause")

    @property
    def icon(self) -> str:
        data = _as_mapping(self._data)
        status = _as_string(data.get("household_status"), "unknown")
        if status == "home":
            return "mdi:home-account"
        if status == "away":
            return "mdi:home-export-outline"
        if status == "partial":
            return "mdi:home-clock"
        return "mdi:account-group"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        attrs: dict[str, Any] = {
            "total_persons": _as_int(data.get("total_persons"), 0),
            "persons_home": _as_int(data.get("persons_home"), 0),
            "persons_away": _as_int(data.get("persons_away"), 0),
            "household_status": _as_string(data.get("household_status"), "unknown"),
            "total_rooms": _as_int(data.get("total_rooms"), 0),
            "occupied_rooms": _as_int(data.get("occupied_rooms"), 0),
            "active_triggers": _as_int(data.get("active_triggers"), 0),
        }

        rooms = _as_list(data.get("room_occupancy"))
        if rooms:
            projected_rooms = []
            for room in rooms:
                room_data = _as_mapping(room)
                if not room_data:
                    continue
                current_count = _as_int(room_data.get("current_count"), 0)
                if current_count <= 0:
                    continue
                projected_rooms.append(
                    {
                        "room": _as_string(room_data.get("room_name"))
                        or _as_string(room_data.get("room_id"))
                        or "unbekannt",
                        "count": current_count,
                        "persons": [
                            person
                            for person in (_as_string(item) for item in _as_list(room_data.get("persons")))
                            if person
                        ],
                    }
                )
            attrs["rooms"] = projected_rooms

        transitions = _as_list(data.get("recent_transitions"))
        if transitions:
            projected_transitions = []
            for transition in transitions[:5]:
                transition_data = _as_mapping(transition)
                if not transition_data:
                    continue
                projected_transitions.append(
                    {
                        "person": _as_string(transition_data.get("person_id")) or None,
                        "from": _as_string(transition_data.get("from_room")) or None,
                        "to": _as_string(transition_data.get("to_room")) or None,
                    }
                )
            attrs["recent_transitions"] = projected_transitions

        return attrs
