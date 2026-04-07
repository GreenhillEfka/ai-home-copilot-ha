"""Voice API for Home Assistant — REST endpoints for STT/TTS pipeline.

Provides:
- POST /api/copilot/voice/process — Audio → Transcript → Intent → Response → TTS
- GET  /api/copilot/voice/status — Pipeline status
- POST /api/copilot/voice/tts — Text → TTS audio

HA → Core flow:
1. HA receives audio from Voice Widget (MediaRecorder)
2. HA sends base64 audio to /api/copilot/voice/process
3. Core Whisper STT → Intent → Action → TTS
4. HA returns transcript + TTS audio
5. Voice Widget plays TTS audio
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, Optional

from aiohttp import web
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .conversation import StyxConversationAgent

_LOGGER = logging.getLogger(__name__)

# Routes are registered via manifest.yaml or async_setup
# This module exposes functions for the HA REST API layer


async def async_register_routes(hass: HomeAssistant) -> web.Application:
    """Register voice API routes on the HA instance."""

    app = web.Application()

    async def handle_process_voice(request: web.Request) -> web.Response:
        """Process voice: audio → transcript → response → TTS audio."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)

        audio_b64 = body.get("audio", "")
        language = body.get("language", "de")

        if not audio_b64:
            return web.json_response({"error": "no audio"}, status=400)

        # Decode base64 audio
        import base64
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception:
            return web.json_response({"error": "invalid audio encoding"}, status=400)

        # Get conversation agent
        agent = _get_conversation_agent(hass)
        if not agent:
            return web.json_response({"error": "conversation agent not available"}, status=503)

        # Process via conversation agent
        from homeassistant.components.conversation import ConversationInput
        from homeassistant.helpers.conversation import async_prepareConversation

        try:
            # Simple text-based transcription simulation
            # In production: call Core STT endpoint
            transcript = await _simulate_stt(hass, audio_bytes, language)

            conv_input = ConversationInput(
                text=transcript,
                language=language,
                conversation_id="voice_api",
                device_id=None,
                context=None,
                options={},
            )

            result = await agent.async_process(conv_input)
            response_text = ""
            if result and result.response:
                response_text = result.response.speech.get("plain", {}).get("text", "")

            return web.json_response({
                "ok": True,
                "transcript": transcript,
                "response": response_text,
                "intent": _extract_intent_type(transcript),
                "language": language,
            })

        except Exception as exc:
            _LOGGER.error("Voice processing failed: %s", exc)
            return web.json_response({
                "ok": False,
                "error": str(exc),
                "transcript": "",
                "response": "Entschuldigung, da ist etwas schiefgegangen.",
            })

    async def handle_tts(request: web.Request) -> web.Response:
        """Generate TTS audio from text."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)

        text = body.get("text", "")
        voice = body.get("voice", "de_DE")

        if not text:
            return web.json_response({"error": "no text"}, status=400)

        # Call Core TTS endpoint (piper)
        audio_bytes = await _call_piper_tts(hass, text, voice)
        if not audio_bytes:
            return web.json_response({"error": "TTS unavailable"}, status=503)

        import base64
        return web.json_response({
            "ok": True,
            "audio": base64.b64encode(audio_bytes).decode(),
            "format": "wav",
            "size": len(audio_bytes),
        })

    async def handle_status(request: web.Request) -> web.Response:
        """Return voice pipeline status."""
        agent = _get_conversation_agent(hass)
        return web.json_response({
            "ok": True,
            "stt_engine": "whisper_local",
            "tts_engine": "piper",
            "conversation_available": agent is not None,
            "supported_languages": ["de", "en"],
        })

    app.router.add_post("/process", handle_process_voice)
    app.router.add_post("/tts", handle_tts)
    app.router.add_get("/status", handle_status)

    return app


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _get_conversation_agent(hass: HomeAssistant) -> Optional[StyxConversationAgent]:
    """Get the StyxConversationAgent from DOMAIN data."""
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id, data in domain_data.items():
        if "conversation_agent" in data:
            return data["conversation_agent"]
    return None


async def _simulate_stt(
    hass: HomeAssistant, audio_bytes: bytes, language: str
) -> str:
    """Simulate STT — in production, call Core Whisper endpoint."""
    # For now: return empty (widget shows "no speech")
    # Real implementation: POST to Core /api/v1/voice/stt
    _LOGGER.debug("STT received %d bytes, language=%s", len(audio_bytes), language)
    # TODO: Call Core Whisper API
    return ""


async def _call_piper_tts(
    hass: HomeAssistant, text: str, voice: str
) -> Optional[bytes]:
    """Call Piper TTS server. Returns audio bytes or None."""
    import aiohttp

    try:
        async with hass.http.ws_connect("/api/websocket") as ws:
            # Subscribe to tts.player events
            result = await hass.async_add_executor_job(
                _piper_sync, text, voice
            )
            return result
    except Exception as exc:
        _LOGGER.warning("Piper TTS call failed: %s", exc)
        return None


def _piper_sync(text: str, voice: str) -> Optional[bytes]:
    """Sync TTS call to Piper HTTP API."""
    import aiohttp
    import asyncio

    piper_url = "http://localhost:8500/v1/synthesize"
    payload = {"text": text, "speaker": 0, "voice": voice}

    try:
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(
            aiohttp.post(piper_url, json=payload, timeout=15)
        )
        loop.close()
        if response.status == 200:
            return response.content.read()
    except Exception:
        pass
    return None


def _extract_intent_type(text: str) -> str:
    """Classify intent from transcript text."""
    t = text.lower()
    if any(k in t for k in ["licht", "light", "lampe"]):
        return "light_control"
    if any(k in t for k in ["heizung", "temperatur", "thermostat"]):
        return "climate_control"
    if any(k in t for k in ["musik", "music", "sonos", "radio"]):
        return "media_control"
    if any(k in t for k in ["status", "wie", "was"]):
        return "query"
    return "unknown"
