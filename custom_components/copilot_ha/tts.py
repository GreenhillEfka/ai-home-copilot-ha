"""PilotSuite Text-to-Speech entity for Home Assistant.

Proxies text to the PilotSuite Core Add-on TTS endpoint
(/api/v1/styx/tts) which uses edge-tts (Microsoft Edge TTS).

Integrates with HA Assist pipeline so users can select PilotSuite
as their TTS engine under Settings > Voice assistants.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.tts import (
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CopilotApiError

_LOGGER = logging.getLogger(__name__)

# Voices available via edge-tts
_VOICES: dict[str, list[Voice]] = {
    "de": [
        Voice("de-DE-ConradNeural", "Conrad"),
        Voice("de-DE-KatjaNeural", "Katja"),
        Voice("de-DE-AmalaNeural", "Amala"),
        Voice("de-AT-IngridNeural", "Ingrid (AT)"),
        Voice("de-CH-LeniNeural", "Leni (CH)"),
    ],
    "en": [
        Voice("en-US-GuyNeural", "Guy"),
        Voice("en-US-JennyNeural", "Jenny"),
        Voice("en-GB-RyanNeural", "Ryan (GB)"),
        Voice("en-GB-SoniaNeural", "Sonia (GB)"),
    ],
    "fr": [
        Voice("fr-FR-HenriNeural", "Henri"),
        Voice("fr-FR-DeniseNeural", "Denise"),
    ],
    "es": [
        Voice("es-ES-AlvaroNeural", "Alvaro"),
        Voice("es-ES-ElviraNeural", "Elvira"),
    ],
    "it": [
        Voice("it-IT-DiegoNeural", "Diego"),
        Voice("it-IT-ElsaNeural", "Elsa"),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PilotSuite TTS entity from a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        _LOGGER.warning("PilotSuite coordinator not available for TTS setup")
        return

    async_add_entities([PilotSuiteTTSEntity(hass, entry, coordinator)])
    _LOGGER.info("PilotSuite TTS entity registered")


class PilotSuiteTTSEntity(TextToSpeechEntity):
    """PilotSuite Text-to-Speech entity using Core's edge-tts endpoint."""

    _attr_has_entity_name = True
    _attr_name = "PilotSuite TTS"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator) -> None:
        """Initialize the TTS entity."""
        self.hass = hass
        self._entry = entry
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_tts"

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return list(_VOICES.keys())

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "de"

    async def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return a list of supported voices for a language."""
        return _VOICES.get(language)

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Generate TTS audio via PilotSuite Core."""
        options = options or {}
        voice = options.get("voice")

        try:
            audio_bytes = await self._coordinator.api.async_tts(
                text=message,
                language=language,
                voice=voice,
            )
        except CopilotApiError as err:
            _LOGGER.error("PilotSuite TTS API error: %s", err)
            return (None, None)
        except Exception as err:
            _LOGGER.error("PilotSuite TTS failed: %s", err)
            return (None, None)

        if not audio_bytes:
            _LOGGER.warning("TTS returned empty audio")
            return (None, None)

        _LOGGER.debug("TTS generated %d bytes for: %s", len(audio_bytes), message[:60])
        return ("mp3", audio_bytes)
