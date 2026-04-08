"""Voice Context Sensor for HA Assist integration.

Exposes the neural system's voice context to Home Assistant:
- Current mood and confidence
- Zone presence
- Voice-friendly suggestions

Use in HA Assist templates:
```
{{ state_attr('sensor.ai_copilot_voice_context', 'voice_prompt') }}
```

HA 2025.8+ supports context-based sensor selection for Assist.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class VoiceContextSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing voice context from neural system."""
    
    _attr_name = "PilotSuite Voice Context"
    _attr_unique_id = "ai_copilot_voice_context"
    _attr_icon = "mdi:microphone-message"
    _attr_should_poll = False
    
    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the voice context sensor."""
        super().__init__(coordinator)
        self._attr_native_value = "ok"
        self._context_data: Dict[str, Any] = {}
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return voice context attributes."""
        if not self.coordinator.data:
            return {}
        
        # Get neural system data
        neural_data = self.coordinator.data.get("neural", {})
        mood_data = self.coordinator.data.get("mood", {})
        suggestions = self.coordinator.data.get("suggestions", [])
        
        # Build voice context
        context = self._build_voice_context(mood_data, neural_data, suggestions)
        self._context_data = context
        
        return {
            "dominant_mood": context.get("mood", {}).get("dominant", "unknown"),
            "mood_confidence": context.get("mood", {}).get("confidence", 0.0),
            "mood_contributors": context.get("mood", {}).get("contributors", []),
            "current_zone": context.get("zone", {}).get("current", "unknown"),
            "zone_presence": context.get("zone", {}).get("presence", []),
            "voice_tone": context.get("voice", {}).get("tone", "unknown"),
            "voice_greeting": context.get("voice", {}).get("greeting", ""),
            "voice_suggestions": context.get("voice", {}).get("suggestions", []),
            "voice_prompt": self._build_voice_prompt(context),
            "last_update": context.get("metadata", {}).get("last_update", ""),
        }
    
    def _build_voice_context(
        self,
        mood_data: Dict[str, Any],
        neural_data: Dict[str, Any],
        _suggestions: list,
    ) -> Dict[str, Any]:
        """Build voice context from Core-provided projection data.

        Home Assistant projects the values Core already exports. It must not
        translate actions, infer tones, or invent extra semantics locally.
        """
        dominant_mood = mood_data.get("mood", "unknown")
        confidence = mood_data.get("confidence", 0.0)

        core_time = neural_data.get("time", {})
        time_greeting = core_time.get("description_de") or core_time.get(
            "description_en", "Hallo"
        )

        core_zone = neural_data.get("zone", {})
        zone_name = core_zone.get("current", "unknown")
        zone_activities = core_zone.get("typical_activities", [])
        voice_suggestions = [f"{act} ist aktuell." for act in zone_activities[:3]]

        return {
            "mood": {
                "dominant": dominant_mood,
                "confidence": confidence,
                "contributors": mood_data.get("contributors", []),
            },
            "zone": {
                "current": zone_name,
                "presence": core_zone.get("presence", neural_data.get("presence", [])),
            },
            "voice": {
                "tone": dominant_mood,
                "greeting": time_greeting,
                "suggestions": voice_suggestions,
            },
            "metadata": {
                "last_update": neural_data.get("last_update", ""),
                "context_version": "1.1",
            },
        }
    
    def _build_voice_prompt(self, context: Dict[str, Any]) -> str:
        """Build a natural language prompt for HA Assist."""
        voice = context.get("voice", {})
        mood = context.get("mood", {})
        zone = context.get("zone", {})
        
        parts = [f"Der Nutzer ist gerade {voice.get('greeting', 'Neutral')}."]
        
        presence = zone.get("presence", [])
        if presence:
            zones = ", ".join(presence[:3])
            parts.append(f"Anwesend in: {zones}.")
        
        suggestions = voice.get("suggestions", [])
        if suggestions:
            parts.append(f"Vorschläge: {'; '.join(suggestions[:2])}.")
        
        return " ".join(parts)
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class VoicePromptSensor(CoordinatorEntity, SensorEntity):
    """Sensor providing a ready-to-use voice prompt for HA Assist."""
    
    _attr_name = "PilotSuite Voice Prompt"
    _attr_unique_id = "ai_copilot_voice_prompt"
    _attr_icon = "mdi:text-to-speech"
    _attr_should_poll = False
    
    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        """Initialize the voice prompt sensor."""
        super().__init__(coordinator)
    
    @property
    def native_value(self) -> str:
        """Return the voice prompt."""
        if not self.coordinator.data:
            return "Kein Kontext verfügbar."
        
        mood_data = self.coordinator.data.get("mood", {})
        suggestions = self.coordinator.data.get("suggestions", [])
        
        # Build prompt
        dominant_mood = mood_data.get("mood", "unknown")
        
        mood_tones = {
            "relax": "Entspannt",
            "focus": "Fokussiert",
            "active": "Aktiv",
            "sleep": "Müde",
            "away": "Abwesend",
            "alert": "Aufmerksam",
            "social": "Gesellig",
            "recovery": "Erholend",
        }
        
        tone = mood_tones.get(dominant_mood, "Neutral")
        prompt = f"Der Nutzer ist {tone}."
        
        if suggestions:
            prompt += f" {len(suggestions)} Vorschläge verfügbar."
        
        return prompt
    
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