"""Agent Status Sensor for Home Assistant (v5.21.0).

Exposes Styx agent health, connectivity, and capabilities as an HA sensor.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


# ─── Payload Guard Helpers ────────────────────────────────────────────────────

def _as_mapping(val: Any, default: dict | None = None) -> dict:
    if isinstance(val, dict) and val:
        return val
    return default if default is not None else {}


def _as_list(val: Any, default: list | None = None) -> list:
    if isinstance(val, list):
        return val
    return default if default is not None else []


def _as_string(val: Any, default: str = "") -> str:
    if isinstance(val, str):
        normalized = val.strip()
        if normalized:
            return normalized
    return default


def _as_float(val: Any, default: float = 0.0) -> float:
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return float(val)
    return default


def _as_bool(val: Any, default: bool = False) -> bool:
    return bool(val) if isinstance(val, bool) else default


class AgentStatusSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing Styx agent status and health."""

    _attr_name = "Styx Agent Status"
    _attr_unique_id = "copilot_agent_status"
    _attr_icon = "mdi:robot"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> str | None:
        data = _as_mapping(self._data)
        status = _as_string(data.get("status"), "offline")
        agent_name = _as_string(data.get("agent_name"), "Styx")
        return f"{agent_name}: {status}"

    @property
    def icon(self) -> str:
        data = _as_mapping(self._data)
        status = _as_string(data.get("status"), "offline")
        if status == "ready":
            return "mdi:robot-happy"
        elif status == "degraded":
            return "mdi:robot-confused"
        return "mdi:robot-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        # Scalar fields
        agent_name = _as_string(data.get("agent_name"), "Styx")
        agent_version = _as_string(data.get("agent_version"), "")
        status = _as_string(data.get("status"), "offline")
        uptime_seconds = _as_float(data.get("uptime_seconds"), 0.0)
        llm_model = _as_string(data.get("llm_model"), "")
        llm_backend = _as_string(data.get("llm_backend"), "")
        character = _as_string(data.get("character"), "")
        last_health_check = _as_string(data.get("last_health_check"), "")
        # Bool fields
        conversation_ready = _as_bool(data.get("conversation_ready"), False)
        llm_available = _as_bool(data.get("llm_available"), False)
        # List fields — guard and filter to strings
        features_raw = _as_list(data.get("features"), [])
        features = [_as_string(f) for f in features_raw]
        features = [f for f in features if f]
        supported_languages_raw = _as_list(data.get("supported_languages"), [])
        supported_languages = [_as_string(l) for l in supported_languages_raw]
        supported_languages = [l for l in supported_languages if l]
        return {
            "agent_name": agent_name,
            "agent_version": agent_version,
            "status": status,
            "uptime_seconds": uptime_seconds,
            "conversation_ready": conversation_ready,
            "llm_available": llm_available,
            "llm_model": llm_model,
            "llm_backend": llm_backend,
            "character": character,
            "features": features,
            "supported_languages": supported_languages,
            "last_health_check": last_health_check,
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/agent"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/status", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        self._data = data
                else:
                    self._data["status"] = "offline"
        except Exception as exc:
            _LOGGER.debug("Failed to fetch agent status: %s", exc)
            self._data["status"] = "offline"
