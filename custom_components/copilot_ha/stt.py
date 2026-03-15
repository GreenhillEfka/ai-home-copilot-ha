"""PilotSuite Speech-to-Text entity for Home Assistant.

Proxies audio to the PilotSuite Core Add-on STT endpoint
(/api/v1/styx/stt) which uses Whisper via Ollama or cloud fallback.

Integrates with HA Assist pipeline so users can select PilotSuite
as their STT engine under Settings > Voice assistants.
"""

from __future__ import annotations

import io
import logging
import wave
from collections.abc import AsyncIterable

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CopilotApiError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PilotSuite STT entity from a config entry."""
    async_add_entities([PilotSuiteSTTEntity(hass, entry)])
    _LOGGER.info("PilotSuite STT entity registered")


class PilotSuiteSTTEntity(SpeechToTextEntity):
    """PilotSuite Speech-to-Text entity using Core's Whisper endpoint."""

    _attr_has_entity_name = True
    _attr_name = "PilotSuite STT"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the STT entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stt"

    @property
    def _coordinator(self):
        """Lazily resolve coordinator from hass.data."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return entry_data.get("coordinator") if isinstance(entry_data, dict) else None

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["de", "en", "fr", "es", "it", "nl", "pt", "pl", "ru", "ja", "zh"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return supported audio formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return supported audio codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return supported sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return supported audio channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to the STT service."""
        # Collect audio chunks
        audio_buffer = bytearray()
        async for chunk in stream:
            audio_buffer.extend(chunk)

        if not audio_buffer:
            return SpeechResult("", SpeechResultState.ERROR)

        if self._coordinator is None or not hasattr(self._coordinator, "api"):
            _LOGGER.warning("PilotSuite Core not connected — STT unavailable")
            return SpeechResult("", SpeechResultState.ERROR)

        # Wrap raw PCM in WAV container
        wav_data = await self.hass.async_add_executor_job(
            self._pcm_to_wav,
            bytes(audio_buffer),
            metadata.sample_rate,
            metadata.channel,
            metadata.bit_rate,
        )

        language = metadata.language or "de"

        try:
            result = await self._coordinator.api.async_stt(wav_data, language=language)
        except CopilotApiError as err:
            _LOGGER.error("PilotSuite STT API error: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
        except Exception as err:
            _LOGGER.error("PilotSuite STT failed: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)

        if not result.get("ok"):
            _LOGGER.warning("STT returned not ok: %s", result.get("error", "unknown"))
            return SpeechResult("", SpeechResultState.ERROR)

        text = result.get("text", "").strip()
        if not text:
            return SpeechResult("", SpeechResultState.ERROR)

        _LOGGER.debug("STT transcription: %s", text[:100])
        return SpeechResult(text, SpeechResultState.SUCCESS)

    @staticmethod
    def _pcm_to_wav(
        pcm_data: bytes,
        sample_rate: int,
        channels: int,
        bit_rate: int,
    ) -> bytes:
        """Wrap raw PCM bytes in a WAV container."""
        sample_width = bit_rate // 8
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()
