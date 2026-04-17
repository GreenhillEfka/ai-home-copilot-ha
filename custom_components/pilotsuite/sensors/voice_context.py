"""Voice Context Sensor for HA Assist integration.

Exposes the neural system's voice context to Home Assistant:
- Current mood and confidence
- Zone presence
- Voice-friendly suggestions

Use in HA Assist templates:
```
{{ state_attr('sensor.pilotsuite_voice_context', 'voice_prompt') }}
```

HA 2025.8+ supports context-based sensor selection for Assist.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# HA entity state_attributes have a 255-byte hard limit; truncate all scalars to stay safe.
_MAX_SCALAR_LENGTH = 64
_VOICE_SUGGESTION_SUFFIX = " ist aktuell."
_MAX_VOICE_SUGGESTION_BASE_LENGTH = _MAX_SCALAR_LENGTH - len(_VOICE_SUGGESTION_SUFFIX)


def _as_mapping(value: Any) -> Dict[str, Any]:
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _normalize_whitespace(value: str) -> str:
    """Collapse internal whitespace so HA attrs/prompts stay single-line and stable."""
    return " ".join(value.split())


def _as_string_list(value: Any) -> list[str]:
    """Return normalized string-only list payloads without inventing fallback semantics."""
    if not isinstance(value, list):
        return []
    return [normalized for item in value if isinstance(item, str) if (normalized := _normalize_whitespace(item))]


def _as_string(value: Any, default: str) -> str:
    """Return normalized string payloads, otherwise a safe default."""
    if not isinstance(value, str):
        return default
    normalized = _normalize_whitespace(value)
    return normalized if normalized else default


def _as_float(value: Any, default: float) -> float:
    """Return finite numeric payloads, otherwise a safe default."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    numeric_value = float(value)
    return numeric_value if math.isfinite(numeric_value) else default


def _project_voice_context(
    mood_data: Dict[str, Any],
    neural_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Project Core-provided voice context fields without local semantics."""
    mood_data = _as_mapping(mood_data)
    neural_data = _as_mapping(neural_data)

    dominant_mood = _as_string(mood_data.get("mood"), "unknown")
    confidence = _as_float(mood_data.get("confidence"), 0.0)

    core_time = _as_mapping(neural_data.get("time"))
    time_greeting = (
        _as_string(core_time.get("description_de"), "")
        or _as_string(core_time.get("description_en"), "")
        or "Hallo"
    )

    core_zone = _as_mapping(neural_data.get("zone"))
    zone_name = _as_string(core_zone.get("current"), "unknown")
    zone_activities = _as_string_list(core_zone.get("typical_activities"))
    raw_suggestions = [
        f"{act[:_MAX_VOICE_SUGGESTION_BASE_LENGTH]}{_VOICE_SUGGESTION_SUFFIX}"
        for act in zone_activities[:3]
    ]
    voice_suggestions = [s[:_MAX_SCALAR_LENGTH] for s in raw_suggestions]
    zone_presence = _as_string_list(core_zone.get("presence"))
    if not zone_presence:
        zone_presence = _as_string_list(neural_data.get("presence"))
    zone_presence = [zone[:_MAX_SCALAR_LENGTH] for zone in zone_presence]

    return {
        "mood": {
            "dominant": dominant_mood,
            "confidence": confidence,
            "contributors": _as_string_list(mood_data.get("contributors"))[:3],
        },
        "zone": {
            "current": zone_name,
            "presence": zone_presence,
        },
        "voice": {
            "tone": dominant_mood,
            "greeting": time_greeting,
            "suggestions": voice_suggestions,
        },
        "metadata": {
            "last_update": _as_string(neural_data.get("last_update"), "")[:_MAX_SCALAR_LENGTH],
        },
    }


def _prompt_suggestion_fragments(suggestions: Any) -> list[str]:
    """Return prompt-safe suggestion fragments without duplicate terminal punctuation."""
    fragments: list[str] = []
    for suggestion in _as_string_list(suggestions)[:2]:
        fragment = suggestion.rstrip(".!?")
        if fragment:
            fragments.append(fragment)
    return fragments



def _build_voice_prompt(context: Dict[str, Any]) -> str:
    """Build a natural-language prompt from already projected Core fields."""
    voice = _as_mapping(context.get("voice"))
    zone = _as_mapping(context.get("zone"))

    greeting = _as_string(voice.get("greeting"), "") or "Neutral"
    parts = [f"Der Nutzer ist gerade {greeting}."]

    presence = _as_string_list(zone.get("presence"))
    if presence:
        zones = ", ".join(presence[:3])
        parts.append(f"Anwesend in: {zones}.")

    suggestion_fragments = _prompt_suggestion_fragments(voice.get("suggestions"))
    if suggestion_fragments:
        parts.append(f"Vorschläge: {'; '.join(suggestion_fragments)}.")

    return " ".join(parts)


class VoiceContextSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing voice context from neural system."""

    _attr_name = "PilotSuite Voice Context"
    _attr_unique_id = "pilotsuite_voice_context"
    _attr_icon = "mdi:microphone-message"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the voice context sensor."""
        super().__init__(coordinator)
        self._context_data: Dict[str, Any] = {}

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return voice context attributes."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return {}

        neural_data = coordinator_data.get("neural", {})
        mood_data = coordinator_data.get("mood", {})

        context = self._build_voice_context(mood_data, neural_data)
        self._context_data = context

        return {
            "dominant_mood": _as_string(context.get("mood", {}).get("dominant"), "unknown")[:_MAX_SCALAR_LENGTH],
            "mood_confidence": round(float(context.get("mood", {}).get("confidence", 0.0)), 4),
            "mood_contributors": context.get("mood", {}).get("contributors", [])[:3],
            "current_zone": _as_string(context.get("zone", {}).get("current"), "unknown")[:_MAX_SCALAR_LENGTH],
            "zone_presence": context.get("zone", {}).get("presence", [])[:3],
            "voice_tone": _as_string(context.get("voice", {}).get("tone"), "")[:_MAX_SCALAR_LENGTH] or "unknown",
            "voice_greeting": _as_string(context.get("voice", {}).get("greeting"), "")[:_MAX_SCALAR_LENGTH],
            "voice_suggestions": [s[:_MAX_SCALAR_LENGTH] for s in _as_string_list(context.get("voice", {}).get("suggestions"))[:3]],
            "voice_prompt": self._build_voice_prompt(context)[:255],
            "last_update": context.get("metadata", {}).get("last_update", "")[:_MAX_SCALAR_LENGTH],
        }

    @property
    def native_value(self) -> str:
        """Return the dominant mood as primary state — rotates with context changes."""
        if self._context_data:
            return _as_string(self._context_data.get("mood", {}).get("dominant"), "unknown")[:255]

        coordinator_data = _as_mapping(self.coordinator.data)
        mood_data = _as_mapping(coordinator_data.get("mood", {}))
        return _as_string(mood_data.get("mood"), "unknown")[:255]

    def _build_voice_context(
        self,
        mood_data: Dict[str, Any],
        neural_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build voice context from Core-provided projection data.

        Note: coordinator.data["suggestions"] is intentionally not consumed here.
        Voice suggestions are derived solely from neural.zone.typical_activities
        to keep the HA Assist prompt grounded in factual zone activity rather than
        raw Core suggestion payloads.
        """
        return _project_voice_context(mood_data, neural_data)

    def _build_voice_prompt(self, context: Dict[str, Any]) -> str:
        """Build a natural language prompt for HA Assist."""
        return _build_voice_prompt(context)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._context_data = {}
        self.async_write_ha_state()


class VoicePromptSensor(CoordinatorEntity, SensorEntity):
    """Sensor providing a ready-to-use voice prompt for HA Assist."""

    _attr_name = "PilotSuite Voice Prompt"
    _attr_unique_id = "pilotsuite_voice_prompt"
    _attr_icon = "mdi:text-to-speech"
    _attr_should_poll = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the voice prompt sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self) -> str:
        """Return the projected voice prompt."""
        coordinator_data = _as_mapping(self.coordinator.data)
        if not coordinator_data:
            return "Kein Kontext verfügbar."

        mood_data = coordinator_data.get("mood", {})
        neural_data = coordinator_data.get("neural", {})
        context = _project_voice_context(mood_data, neural_data)
        return _build_voice_prompt(context)[:255]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up voice context sensors."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for entry %s", entry.entry_id)
        return

    entities = [
        VoiceContextSensor(coordinator),
        VoicePromptSensor(coordinator),
    ]

    async_add_entities(entities)
    _LOGGER.info("Voice context sensors set up for entry %s", entry.entry_id)
