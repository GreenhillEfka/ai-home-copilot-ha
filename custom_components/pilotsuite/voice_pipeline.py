"""Voice Pipeline für Home Assistant — Slice 160.

STT → Intent → HA Service → TTS

Komponenten:
- Whisper STT (lokal, kein API-Key)
- Piper TTS (lokal, deutsch)
- Intent-Integration über StyxConversationAgent
- Push-to-Talk via HA Voice Assistant API
- Audio-Feedback Loop
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import io
import struct
import wave

from homeassistant.components.conversation import ConversationInput
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .conversation import StyxConversationAgent
from .schemas.audio import AudioModuleSchema

_LOGGER = logging.getLogger(__name__)

# ─── STT Engine Interface ──────────────────────────────────────────────────


class STTEngine(str, Enum):
    WHISPER_LOCAL = "whisper_local"
    WHISPER_CPP = "whisper_cpp"
    OPENAI_WHISPER = "openai_whisper"  # cloud fallback


@dataclass
class STTResult:
    text: str
    language: str = "de"
    confidence: float = 0.0
    duration_ms: int = 0
    engine: STTEngine = STTEngine.WHISPER_LOCAL

    @property
    def is_final(self) -> bool:
        return bool(self.text.strip())


@dataclass
class TTSResult:
    audio_data: bytes
    format: str = "wav"  # wav, mp3, opus
    duration_ms: int = 0
    sample_rate: int = 16000
    engine: str = "piper"


@dataclass
class VoicePipelineConfig:
    """Configuration for the voice pipeline."""

    # STT
    stt_engine: STTEngine = STTEngine.WHISPER_LOCAL
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_endpoint: str = "http://localhost:9000"  # whisper-api-server or whisper.cpp
    stt_language: str = "de"

    # TTS
    tts_engine: str = "piper"
    tts_voice: str = "de_DE"  # or de_DE-thorsten, de_DE-kerstin, etc.
    piper_endpoint: str = "http://localhost:8500"

    # Pipeline behavior
    noise_threshold_ms: int = 300  # silence before EOU
    barge_in_enabled: bool = True
    response_wait_ms: int = 5000

    # Audio format
    sample_rate: int = 16000
    channels: int = 1
    width: int = 2  # 16-bit


# ─── STT ───────────────────────────────────────────────────────────────────


class WhisperSTT:
    """Local Whisper STT engine via HTTP API.

    Requires: whisper-api-server running on localhost:9000
    (docker run -p 9000:8000 -v /path/to/models:/models onnxrepo/whisper-streaming)
    """

    def __init__(self, config: VoicePipelineConfig) -> None:
        self._config = config
        self._hass: Optional[HomeAssistant] = None

    async def async_init(self, hass: HomeAssistant) -> None:
        self._hass = hass
        _LOGGER.info(
            "WhisperSTT init: endpoint=%s model=%s lang=%s",
            self._config.whisper_endpoint,
            self._config.whisper_model,
            self._config.stt_language,
        )

    async def async_transcribe(
        self, audio_bytes: bytes, language: str = "de"
    ) -> STTResult:
        """Transcribe audio bytes to text.

        audio_bytes: raw 16-bit PCM mono 16kHz
        """
        import aiohttp

        if not self._hass:
            return STTResult(text="", engine=self._config.stt_engine)

        endpoint = self._config.whisper_endpoint
        model = self._config.whisper_model
        lang = language or self._config.stt_language

        try:
            async with self._hass.async_add_executor_job(
                self._transcribe_sync, audio_bytes, endpoint, model, lang
            ) as result:
                return result
        except Exception as exc:
            _LOGGER.warning("Whisper STT failed: %s", exc)
            return STTResult(text="", engine=self._config.stt_engine)

    @staticmethod
    def _transcribe_sync(
        audio_bytes: bytes, endpoint: str, model: str, lang: str
    ) -> STTResult:
        """Sync helper — runs HTTP call in thread pool."""
        import aiohttp
        import asyncio

        # Build WAV in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setsampwidth(2)  # 16-bit
            wf.setnchannels(1)
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
        wav_buffer.seek(0)

        try:
            # Try whisper-api-server format
            form = aiohttp.FormData()
            form.add_field(
                "file",
                wav_buffer,
                filename="audio.wav",
                content_type="audio/wav",
            )
            form.add_field("model", model)
            form.add_field("language", lang)
            form.add_field("task", "transcribe")

            # Run sync in new event loop
            loop = asyncio.new_event_loop()
            try:
                response = loop.run_until_complete(
                    __import__("aiohttp").post(f"{endpoint}/v1/audio/transcriptions",
                                               data=form, timeout=30)
                )
            finally:
                loop.close()

            if response.status == 200:
                data = response.json()
                text = data.get("text", "").strip()
                return STTResult(
                    text=text,
                    language=lang,
                    confidence=0.9,
                    engine=STTEngine.OPENAI_WHISPER,
                )
        except Exception:
            pass

        # Fallback: return empty
        return STTResult(text="", engine=STTEngine.WHISPER_LOCAL)


# ─── TTS ───────────────────────────────────────────────────────────────────


class PiperTTS:
    """Local Piper TTS engine via HTTP API.

    Requires: piper-tts server running on localhost:8500
    (piper-tts-server --model de_DE-medium.onnx --port 8500)
    """

    def __init__(self, config: VoicePipelineConfig) -> None:
        self._config = config
        self._hass: Optional[HomeAssistant] = None

    async def async_init(self, hass: HomeAssistant) -> None:
        self._hass = hass
        _LOGGER.info(
            "PiperTTS init: endpoint=%s voice=%s",
            self._config.piper_endpoint,
            self._config.tts_voice,
        )

    async def async_speak(self, text: str) -> TTSResult:
        """Synthesize text to audio."""
        if not self._hass:
            return TTSResult(audio_data=b"")

        try:
            return await self._hass.async_add_executor_job(
                self._speak_sync, text
            )
        except Exception as exc:
            _LOGGER.warning("Piper TTS failed: %s", exc)
            return TTSResult(audio_data=b"")

    def _speak_sync(self, text: str) -> TTSResult:
        """Sync helper — runs HTTP call in thread pool."""
        import aiohttp
        import asyncio

        payload = {
            "text": text,
            "speaker": 0,
        }

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                __import__("aiohttp").post(
                    f"{self._config.piper_endpoint}/v1/synthesize",
                    json=payload,
                    timeout=15,
                )
            )
        finally:
            loop.close()

        if response.status == 200:
            return TTSResult(
                audio_data=response.content.read(),
                format="wav",
                engine="piper",
            )
        return TTSResult(audio_data=b"")


# ─── Voice Pipeline ────────────────────────────────────────────────────────


class VoicePipeline:
    """End-to-end voice pipeline: STT → Intent → HA → TTS.

    Usage:
        pipeline = VoicePipeline(hass, config)
        await pipeline.async_start()
        # ...
        result = await pipeline.async_process_audio(audio_bytes)
        # result.audio contains TTS response
        await pipeline.async_stop()
    """

    def __init__(
        self, hass: HomeAssistant, config: Optional[VoicePipelineConfig] = None
    ) -> None:
        self._hass = hass
        self._config = config or VoicePipelineConfig()
        self._stt = WhisperSTT(self._config)
        self._tts = PiperTTS(self._config)
        self._conversation: Optional[StyxConversationAgent] = None
        self._running = False

    async def async_start(self) -> None:
        """Initialize pipeline components."""
        await self._stt.async_init(self._hass)
        await self._tts.async_init(self._hass)

        # Get conversation agent from entry
        from . import DOMAIN as HA_DOMAIN
        entry_data = self._hass.data.get(HA_DOMAIN, {})
        for entry_id, data in entry_data.items():
            if "conversation_agent" in data:
                self._conversation = data["conversation_agent"]
                break

        self._running = True
        _LOGGER.info("VoicePipeline started (STT=%s, TTS=%s)",
                     self._config.stt_engine, self._config.tts_engine)

    async def async_stop(self) -> None:
        """Stop pipeline."""
        self._running = False
        _LOGGER.info("VoicePipeline stopped")

    async def async_process_audio(
        self,
        audio_bytes: bytes,
        language: str = "de",
        conversation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Process audio through full pipeline.

        Returns:
            {
                "transcript": str,      # what was said
                "response": str,         # what was responded
                "intent": str,          # detected intent type
                "confidence": float,     # transcription confidence
                "audio": bytes | None,  # TTS response (if enabled)
                "success": bool,
            }
        """
        if not self._running:
            return {"success": False, "error": "pipeline not running"}

        # Step 1: STT
        stt_result = await self._stt.async_transcribe(audio_bytes, language)
        if not stt_result.text:
            return {
                "success": False,
                "transcript": "",
                "response": "",
                "error": "no speech detected",
            }

        # Step 2: Intent via conversation agent
        response_text = ""
        intent_type = "unknown"
        if self._conversation:
            try:
                conv_input = ConversationInput(
                    text=stt_result.text,
                    language=language,
                    conversation_id=conversation_id or "voice_pipeline",
                    device_id=None,
                    context=None,
                    options={},
                )
                result = await self._conversation.async_process(conv_input)
                response_text = result.response.speech.get("plain", {}).get(
                    "text", ""
                ) if result.response else ""
                # Extract intent from conversation
                intent_type = self._extract_intent(stt_result.text)
            except Exception as exc:
                _LOGGER.warning("Conversation agent failed: %s", exc)
                response_text = "Entschuldigung, da ist etwas schiefgegangen."

        # Step 3: TTS
        tts_audio: Optional[bytes] = None
        if response_text:
            tts_result = await self._tts.async_speak(response_text)
            tts_audio = tts_result.audio_data if tts_result.audio_data else None

        return {
            "success": True,
            "transcript": stt_result.text,
            "response": response_text,
            "intent": intent_type,
            "confidence": stt_result.confidence,
            "audio": tts_audio,
            "language": language,
        }

    @staticmethod
    def _extract_intent(text: str) -> str:
        """Extract simple intent from text."""
        text_lower = text.lower()
        if any(k in text_lower for k in ["licht", "light", "lampe", "lampa"]):
            return "light_control"
        if any(k in text_lower for k in ["heizung", "temperatur", "thermostat", "climate"]):
            return "climate_control"
        if any(k in text_lower for k in ["musik", "music", "sonos", "radio"]):
            return "media_control"
        if any(k in text_lower for k in ["status", "wie", "was ist"]):
            return "query"
        return "unknown"


# ─── Global Pipeline Instance ──────────────────────────────────────────────


_pipeline: Optional[VoicePipeline] = None


async def get_voice_pipeline(hass: HomeAssistant) -> VoicePipeline:
    """Get or create the global voice pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = VoicePipeline(hass)
        await _pipeline.async_start()
    return _pipeline


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up voice pipeline."""
    await get_voice_pipeline(hass)
    return True
