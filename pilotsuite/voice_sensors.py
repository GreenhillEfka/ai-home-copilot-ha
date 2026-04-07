"""Voice Sensors for HA — Slice 165.

Provides HA sensors for voice pipeline monitoring:
- VoiceCommandHistorySensor: Last N voice commands
- VoicePipelineStatusSensor: Current pipeline state
- VoiceSTTStatusSensor: STT engine status
- VoiceTTSStatusSensor: TTS engine status
- VoiceCommandCountSensor: Commands today/total

Slice 165 — 168h Massive Iteration (Voice-Analytics)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


# ─── Voice Command History Sensor ─────────────────────────────────────────────


@dataclass
class VoiceCommandRecord:
    """A single voice command record."""
    command: str
    timestamp: datetime
    intent: str
    success: bool
    response: str
    duration_ms: int


class VoiceCommandHistorySensor(RestoreEntity, Entity):
    """Sensor that stores the last N voice commands."""

    def __init__(self, hass: HomeAssistant, max_history: int = 50) -> None:
        self._hass = hass
        self._max_history = max_history
        self._commands: List[VoiceCommandRecord] = []
        self._attr_name = "PilotSuite Voice Command History"
        self._attr_unique_id = "pilotsuite_voice_command_history"
        self._attr_icon = "mdi:microphone-message"
        self._attr_unit_of_measurement = "commands"

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.attributes:
            self._commands = [
                VoiceCommandRecord(
                    command=c.get("command", ""),
                    timestamp=datetime.fromisoformat(c.get("timestamp", datetime.now().isoformat())),
                    intent=c.get("intent", ""),
                    success=c.get("success", True),
                    response=c.get("response", ""),
                    duration_ms=c.get("duration_ms", 0),
                )
                for c in state.attributes.get("history", [])
            ][:self._max_history]

    @property
    def state(self) -> str:
        """Return last command or idle."""
        if self._commands:
            return self._commands[-1].command[:50]
        return "idle"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return command history."""
        return {
            "history": [
                {
                    "command": c.command,
                    "timestamp": c.timestamp.isoformat(),
                    "intent": c.intent,
                    "success": c.success,
                    "response": c.response,
                    "duration_ms": c.duration_ms,
                }
                for c in self._commands[-self._max_history:]
            ],
            "count_today": sum(
                1 for c in self._commands
                if c.timestamp.date() == datetime.now().date()
            ),
            "count_total": len(self._commands),
        }

    def record_command(
        self,
        command: str,
        intent: str,
        success: bool,
        response: str,
        duration_ms: int,
    ) -> None:
        """Record a new voice command."""
        record = VoiceCommandRecord(
            command=command,
            timestamp=datetime.now(),
            intent=intent,
            success=success,
            response=response[:200] if response else "",
            duration_ms=duration_ms,
        )
        self._commands.append(record)
        if len(self._commands) > self._max_history:
            self._commands = self._commands[-self._max_history:]
        self.async_write_ha_state()

    def clear_history(self) -> None:
        """Clear command history."""
        self._commands = []
        self.async_write_ha_state()


# ─── Voice Pipeline Status Sensor ─────────────────────────────────────────────


class VoicePipelineStatusSensor(Entity):
    """Sensor showing current voice pipeline status."""

    def __init__(self) -> None:
        self._attr_name = "PilotSuite Voice Pipeline Status"
        self._attr_unique_id = "pilotsuite_voice_pipeline_status"
        self._attr_icon = "mdi:voice"
        self._state = "idle"
        self._last_error: Optional[str] = None

    @property
    def state(self) -> str:
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "error": self._last_error,
            "stt_ready": True,  # Would check actual STT engine
            "tts_ready": True,  # Would check actual TTS engine
            "llm_ready": True,  # Would check actual LLM
        }

    def set_state(self, state: str, error: Optional[str] = None) -> None:
        """Update pipeline state."""
        self._state = state
        self._last_error = error
        self.async_write_ha_state()


# ─── Voice STT Status Sensor ─────────────────────────────────────────────────


class VoiceSTTStatusSensor(Entity):
    """Sensor showing STT engine status."""

    def __init__(self) -> None:
        self._attr_name = "PilotSuite STT Status"
        self._attr_unique_id = "pilotsuite_stt_status"
        self._attr_icon = "mdi:microphone"
        self._state = "ready"
        self._engine = "whisper"
        self._model = "base"

    @property
    def state(self) -> str:
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "engine": self._engine,
            "model": self._model,
            "language": "de",
            "sample_rate": 16000,
        }

    def update(self, engine: str, model: str, state: str) -> None:
        """Update STT status."""
        self._engine = engine
        self._model = model
        self._state = state
        self.async_write_ha_state()


# ─── Voice TTS Status Sensor ─────────────────────────────────────────────────


class VoiceTTSStatusSensor(Entity):
    """Sensor showing TTS engine status."""

    def __init__(self) -> None:
        self._attr_name = "PilotSuite TTS Status"
        self._attr_unique_id = "pilotsuite_tts_status"
        self._attr_icon = "mdi:speaker"
        self._state = "ready"
        self._engine = "piper"
        self._voice = "de_DE-thorsten-low"

    @property
    def state(self) -> str:
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "engine": self._engine,
            "voice": self._voice,
            "language": "de",
        }

    def update(self, engine: str, voice: str, state: str) -> None:
        """Update TTS status."""
        self._engine = engine
        self._voice = voice
        self._state = state
        self.async_write_ha_state()


# ─── Voice Command Count Sensor ───────────────────────────────────────────────


class VoiceCommandCountSensor(RestoreEntity, Entity):
    """Sensor counting voice commands."""

    def __init__(self) -> None:
        self._attr_name = "PilotSuite Voice Commands Today"
        self._attr_unique_id = "pilotsuite_voice_commands_today"
        self._attr_icon = "mdi:counter"
        self._count_today = 0
        self._count_total = 0
        self._last_reset = datetime.now().date()

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._count_today = int(state.state or 0)
            self._count_total = state.attributes.get("total", 0) or 0
            self._last_reset = datetime.fromisoformat(
                state.attributes.get("last_reset", datetime.now().isoformat())
            ).date()

    @property
    def state(self) -> int:
        """Return today's count."""
        today = datetime.now().date()
        if today != self._last_reset:
            self._count_today = 0
            self._last_reset = today
        return self._count_today

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "total": self._count_total,
            "last_reset": self._last_reset.isoformat(),
        }

    def increment(self) -> None:
        """Increment counters."""
        today = datetime.now().date()
        if today != self._last_reset:
            self._count_today = 0
            self._last_reset = today
        self._count_today += 1
        self._count_total += 1
        self.async_write_ha_state()


# ─── Sensor Registry ──────────────────────────────────────────────────────────


async def async_setup_voice_sensors(hass: HomeAssistant) -> None:
    """Set up all voice sensors.
    
    Call from __init__.py async_setup_entry.
    """
    sensors = [
        VoiceCommandHistorySensor(hass, max_history=50),
        VoicePipelineStatusSensor(),
        VoiceSTTStatusSensor(),
        VoiceTTSStatusSensor(),
        VoiceCommandCountSensor(),
    ]

    for sensor in sensors:
        hass.async_add_entity(sensor)

    # Store reference for voice pipeline to update
    hass.data.setdefault(DOMAIN, {})["voice_sensors"] = {
        "history": sensors[0],
        "pipeline_status": sensors[1],
        "stt_status": sensors[2],
        "tts_status": sensors[3],
        "command_count": sensors[4],
    }

    _LOGGER.info("Voice sensors registered: %d", len(sensors))
