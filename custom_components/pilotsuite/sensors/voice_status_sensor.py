"""Voice status readiness sensor for Home Assistant.

Projects the bounded Core `/api/v1/styx/voice/status` truth into one HA-visible
readiness/status sensor without adding local voice semantics.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


def _as_mapping(val: Any, default: dict | None = None) -> dict:
    if isinstance(val, dict):
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


def _as_bool(val: Any, default: bool = False) -> bool:
    return bool(val) if isinstance(val, bool) else default


class VoiceStatusSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing bounded Core voice readiness truth."""

    _attr_name = "PilotSuite Voice Status"
    _attr_unique_id = "pilotsuite_voice_status"
    _attr_icon = "mdi:microphone-message"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> str:
        data = _as_mapping(self._data)
        stt = _as_mapping(data.get("stt"))
        tts = _as_mapping(data.get("tts"))
        stt_available = _as_bool(stt.get("available"), False)
        tts_available = _as_bool(tts.get("available"), False)
        if stt_available and tts_available:
            return "ready"
        if stt_available or tts_available:
            return "degraded"
        return "offline"

    @property
    def icon(self) -> str:
        status = self.native_value
        if status == "ready":
            return "mdi:microphone-message"
        if status == "degraded":
            return "mdi:microphone-message-off"
        return "mdi:microphone-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        stt = _as_mapping(data.get("stt"))
        tts = _as_mapping(data.get("tts"))
        supported_languages = [_as_string(v) for v in _as_list(data.get("supported_languages"), [])]
        supported_languages = [v for v in supported_languages if v]
        return {
            "ok": _as_bool(data.get("ok"), False),
            "stt_available": _as_bool(stt.get("available"), False),
            "tts_available": _as_bool(tts.get("available"), False),
            "stt_engine": _as_string(stt.get("engine"), _as_string(stt.get("backend"), _as_string(stt.get("provider"), ""))),
            "stt_model": _as_string(stt.get("model"), ""),
            "tts_engine": _as_string(tts.get("engine"), _as_string(tts.get("backend"), _as_string(tts.get("provider"), ""))),
            "tts_voice": _as_string(tts.get("voice"), ""),
            "supported_languages": supported_languages,
        }

    async def async_update(self) -> None:
        try:
            data = await self.coordinator.api.async_voice_status()
            self._data = _as_mapping(data)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Failed to fetch voice status: %s", exc)
            self._data = {"ok": False, "stt": {"available": False}, "tts": {"available": False}}
