"""Brain Activity Sensor for PilotSuite HA Integration (v7.5.0).

Displays brain state (active/idle/sleeping), pulse count, and chat activity.
Frontend uses this to animate the brain visualization.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

_STATE_LABELS = {
    "active": "Aktiv — pulsierend",
    "idle": "Wach — bereit",
    "sleeping": "Schlafend",
}

_STATE_ICONS = {
    "active": "mdi:head-lightbulb",
    "idle": "mdi:brain",
    "sleeping": "mdi:power-sleep",
}


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}



def _as_list(value: Any) -> list[Any]:
    """Return list payloads, otherwise a safe empty list."""
    return value if isinstance(value, list) else []



def _as_string(value: Any, default: str = "") -> str:
    """Return string payloads, otherwise a safe default."""
    return value if isinstance(value, str) else default


class BrainActivitySensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing brain activity state for dashboard animation."""

    _attr_name = "Brain Activity"
    _attr_icon = "mdi:brain"
    _attr_unique_id = "pilotsuite_brain_activity"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        try:
            url = f"{self._core_base_url()}/api/v1/hub/brain/activity"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch brain activity data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        state = self._data.get("state", "idle")
        return _STATE_LABELS.get(state, state)

    @property
    def icon(self) -> str:
        state = self._data.get("state", "idle")
        return _STATE_ICONS.get(state, "mdi:brain")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        attrs: dict[str, Any] = {
            "state": data.get("state", "idle"),
            "total_pulses": data.get("total_pulses", 0),
            "total_chat_messages": data.get("total_chat_messages", 0),
            "uptime_seconds": data.get("uptime_seconds", 0),
            "sleep_seconds": data.get("sleep_seconds", 0),
            "idle_timeout_seconds": data.get("idle_timeout_seconds", 300),
            "sleep_timeout_seconds": data.get("sleep_timeout_seconds", 1800),
            "last_active": data.get("last_active", ""),
        }

        recent_pulses = _as_list(data.get("recent_pulses", []))
        if recent_pulses:
            attrs["recent_pulses"] = [
                {"reason": pulse.get("reason"), "duration_ms": pulse.get("duration_ms")}
                for pulse in recent_pulses[:3]
                if isinstance(pulse, dict)
            ]

        recent_chat = _as_list(data.get("recent_chat", []))
        if recent_chat:
            attrs["recent_chat"] = [
                {"role": message.get("role"), "content": _as_string(message.get("content"))[:100]}
                for message in recent_chat[:3]
                if isinstance(message, dict)
            ]

        # Webhook-pushed intelligence data from coordinator
        coord_data = _as_mapping(self.coordinator.data)

        neurons_fired = _as_list(coord_data.get("neurons_fired", []))
        attrs["neurons_fired_count"] = len(neurons_fired)
        if neurons_fired:
            last = _as_mapping(neurons_fired[-1])
            attrs["last_neuron_fired"] = last.get("neuron_id", last.get("name", "unknown"))
            attrs["last_neuron_fired_at"] = last.get("fired_at", last.get("timestamp", ""))

        brain_insights = _as_list(coord_data.get("brain_insights", []))
        attrs["brain_insights_count"] = len(brain_insights)
        if brain_insights:
            last_insight = _as_mapping(brain_insights[-1])
            attrs["last_brain_insight"] = last_insight.get("insight_type", last_insight.get("type", "unknown"))
            attrs["last_brain_insight_summary"] = _as_string(
                last_insight.get("summary", last_insight.get("description", ""))
            )[:200]

        return attrs
