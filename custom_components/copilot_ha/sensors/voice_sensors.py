"""Voice Command History Sensor for Home Assistant.

Tracks last N voice commands with transcript, response, intent, and timestamp.
Used by Voice-Feedback Cards for history display.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_MAX_HISTORY = 20


class VoiceCommandHistorySensor(SensorEntity):
    """Stores last N voice commands for UI history display."""

    _attr_name = "PilotSuite Voice Command History"
    _attr_unique_id = "pilotsuite_voice_command_history"
    _attr_icon = "mdi:history"
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        hass: HomeAssistant,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._commands: list[dict[str, Any]] = []

    @property
    def native_value(self) -> str:
        return str(len(self._commands))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"commands": self._commands[-_MAX_HISTORY:]}

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class VoiceSTTStatusSensor(SensorEntity):
    """Shows STT engine status."""

    _attr_name = "PilotSuite Voice STT Status"
    _attr_unique_id = "pilotsuite_voice_stt_status"
    _attr_icon = "mdi:mic"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self._hass = hass

    @property
    def native_value(self) -> str:
        from .voice_pipeline import _pipeline
        if _pipeline and _pipeline._running:
            return f"whisper_local ({_pipeline._config.whisper_model})"
        return "offline"


class VoiceCommandsTodaySensor(SensorEntity):
    """Counts voice commands today."""

    _attr_name = "PilotSuite Voice Commands Today"
    _attr_unique_id = "pilotsuite_voice_commands_today"
    _attr_icon = "mdi:counter"
    _attr_state_class = "total"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self._hass = hass
        self._count = 0

    @property
    def native_value(self) -> int:
        return self._count

    def increment(self) -> None:
        self._count += 1
        self.async_write_ha_state()


class VoiceLastCommandSensor(SensorEntity):
    """Shows the last voice command transcript."""

    _attr_name = "PilotSuite Voice Last Command"
    _attr_unique_id = "pilotsuite_voice_last_command"
    _attr_icon = "mdi:message-text"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self._hass = hass
        self._last: dict[str, Any] = {}

    @property
    def native_value(self) -> str:
        return self._last.get("transcript", "")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._last

    def update_from_pipeline_result(self, result: dict[str, Any]) -> None:
        self._last = result
        self.async_write_ha_state()
