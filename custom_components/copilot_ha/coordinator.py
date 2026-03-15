"""PilotSuite — Coordinator with Neural System."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import logging
from typing import Any
import re

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT
from .api import (
    CopilotApiClient as SharedCopilotApiClient,
    CopilotApiError,
    CopilotStatus,
)
from .connection_config import resolve_core_connection_from_mapping
from .core_endpoint import build_base_url, build_candidate_hosts
from .camera_entities import (
    CameraState,
    CameraMotionEvent,
    CameraPresenceEvent,
    CameraActivityEvent,
    CameraZoneEvent,
    CameraPrivacySettings,
)

_LOGGER = logging.getLogger(__name__)

# ── Timeout constants (seconds) ──────────────────────────────────────
# Standard REST calls (health, mood, neurons, zone-automation, etc.)
API_DEFAULT_TIMEOUT_S = 10.0
# Audio endpoints (STT, TTS) — larger payloads, model inference
AUDIO_TIMEOUT_S = 30.0
# Chat completions — qwen3 on HA-class hardware often needs >20s
CHAT_COMPLETIONS_TIMEOUT_S = 90.0


def _extract_http_status(err: CopilotApiError) -> int | None:
    match = re.match(r"^HTTP\s+(\d+)\s+for\s+", str(err))
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def _should_failover(err: CopilotApiError) -> bool:
    message = str(err)
    if message.startswith("Timeout calling ") or message.startswith("Client error calling "):
        return True
    if message.startswith("Unexpected content type ") or message.startswith("Invalid JSON from "):
        return True

    status = _extract_http_status(err)
    if status is None:
        return False

    # Wrong endpoint or transport issues should trigger fallback.
    # Do not fail over on auth failures: that usually indicates token issues,
    # and trying random hosts (e.g. host.docker.internal) only adds noise.
    return status in {404, 405, 408, 429} or status >= 500


class CopilotApiClient(SharedCopilotApiClient):
    """Coordinator-facing API client with endpoint failover + legacy helpers."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        base_urls: list[str],
        token: str,
    ) -> None:
        primary = (base_urls[0] if base_urls else "").rstrip("/")
        super().__init__(session, primary, token)
        self._base_urls = [u.rstrip("/") for u in base_urls if u]
        if not self._base_urls:
            self._base_urls = [primary]
        self._active_base_url = self._base_urls[0]

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        params: dict | None = None,
        timeout_s: float = API_DEFAULT_TIMEOUT_S,
    ) -> dict:
        normalized_path = path if path.startswith("/") else f"/{path}"
        last_err: CopilotApiError | None = None

        for idx, base_url in enumerate(self._base_urls):
            url = f"{base_url}{normalized_path}"
            try:
                async with self._session.request(
                    method,
                    url,
                    json=payload,
                    params=params,
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=timeout_s),
                ) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")

                    ctype = (resp.headers.get("Content-Type", "") or "").lower()
                    if resp.status == 204:
                        data: dict = {}
                    else:
                        body = await resp.text()
                        if "json" not in ctype:
                            raise CopilotApiError(
                                f"Unexpected content type '{ctype or 'unknown'}' for {url}: {body[:200]}"
                            )
                        try:
                            parsed = json.loads(body) if body else {}
                        except json.JSONDecodeError as json_err:
                            raise CopilotApiError(
                                f"Invalid JSON from {url}: {body[:200]}"
                            ) from json_err
                        data = parsed if isinstance(parsed, dict) else {"data": parsed}

                    if base_url != self._active_base_url:
                        _LOGGER.warning(
                            "PilotSuite API failover: switched endpoint from %s to %s",
                            self._active_base_url,
                            base_url,
                        )
                    self._active_base_url = base_url
                    self._base_url = base_url
                    return data
            except asyncio.TimeoutError as err:
                last_err = CopilotApiError(f"Timeout calling {url}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except aiohttp.ClientError as err:
                last_err = CopilotApiError(f"Client error calling {url}: {err}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except CopilotApiError as err:
                last_err = err
                if idx < len(self._base_urls) - 1 and _should_failover(err):
                    continue
                raise

        raise last_err or CopilotApiError("No available Core API endpoint")

    async def async_get(self, path: str, params: dict | None = None) -> dict:
        return await self._request_json("GET", path, params=params)

    async def async_post(self, path: str, payload: dict) -> dict:
        return await self._request_json("POST", path, payload=payload)

    async def async_put(self, path: str, payload: dict) -> dict:
        return await self._request_json("PUT", path, payload=payload)

    # ── Safe wrappers to reduce boilerplate in API methods ────────────

    async def _safe_get(
        self,
        path: str,
        default: Any,
        *,
        key: str | None = None,
        label: str = "",
    ) -> Any:
        """GET with error handling — returns *default* on failure."""
        try:
            data = await self.async_get(path)
            return data.get(key, data) if key else data
        except CopilotApiError as e:
            _LOGGER.debug("%s not available: %s", label or path, e)
        return default

    async def _safe_post(
        self,
        path: str,
        payload: dict,
        *,
        label: str = "",
    ) -> dict[str, Any]:
        """POST with error handling — returns ``{ok: False, error: ...}`` on failure."""
        try:
            return await self._request_json("POST", path, payload=payload)
        except CopilotApiError as e:
            _LOGGER.debug("%s failed: %s", label or path, e)
            return {"ok": False, "error": str(e)}

    async def async_get_status(self) -> CopilotStatus:
        health: dict | None = None
        version: dict | None = None

        ok: bool | None = None
        ver: str | None = None

        try:
            health = await self.async_get("/health")
            ok_val = health.get("ok")
            ok = bool(ok_val) if ok_val is not None else None
        except CopilotApiError:
            ok = None

        try:
            version = await self.async_get("/version")
            if isinstance(version.get("version"), str):
                ver = version["version"]
            elif isinstance(version.get("data"), dict) and isinstance(version["data"].get("version"), str):
                ver = version["data"]["version"]
        except CopilotApiError:
            ver = None

        return CopilotStatus(ok=ok, version=ver)

    async def async_get_mood(self) -> dict[str, Any]:
        """Get current mood from neural system."""
        return await self._safe_get(
            "/api/v1/neurons/mood", {"mood": "unknown", "confidence": 0.0},
            key="data", label="Mood API",
        )

    async def async_get_neurons(self) -> dict[str, Any]:
        """Get all neuron states."""
        return await self._safe_get(
            "/api/v1/neurons", {"neurons": {}}, key="data", label="Neurons API",
        )

    async def async_get_zone_automation(self) -> dict[str, Any]:
        """Get zone automation dashboard (presence, lights, music per zone)."""
        return await self._safe_get(
            "/api/v1/zone-automation/dashboard", {"zones": [], "summary": {}},
            label="Zone automation API",
        )

    async def async_get_sonos_summary(self) -> dict[str, Any]:
        """Get Sonos speaker summary from jishi API."""
        return await self._safe_get(
            "/api/v1/sonos/summary",
            {"total_speakers": 0, "speakers": [], "playing": 0},
            label="Sonos API",
        )

    async def async_get_sonos_favorites(self) -> list[dict[str, Any]]:
        """Get Sonos favorites."""
        return await self._safe_get(
            "/api/v1/sonos/favorites", [], key="favorites", label="Sonos favorites API",
        )

    async def async_sonos_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a Sonos action (play, pause, volume, etc.)."""
        return await self._safe_post(
            f"/api/v1/sonos/{action}", payload, label=f"Sonos action {action}",
        )

    async def async_sync_tags_to_core(self, tags: list[dict[str, Any]]) -> dict[str, Any]:
        """Push HA entity tags to Core for bidirectional tag sync."""
        return await self._safe_post(
            "/api/v1/tags/sync", {"source": "ha", "tags": tags}, label="Tag sync",
        )

    async def async_get_core_tags(self) -> list[dict[str, Any]]:
        """Fetch tag definitions from Core (canonical tags.yaml registry)."""
        return await self._safe_get(
            "/api/v1/tags", [], key="tags", label="Core tags API",
        )

    # ── Musikwolke / Media Zone Control ────────────────────────────────

    async def async_get_musikwolke_status(self) -> dict[str, Any]:
        """Get Musikwolke status (active zones, Sonos connection)."""
        return await self._safe_get(
            "/api/v1/musikwolke/status",
            {"ok": False, "sonos_connected": False, "active_zones": []},
            label="Musikwolke status",
        )

    async def async_musikwolke_play(self, zone_id: str, volume_pct: int | None = None) -> dict[str, Any]:
        """Play media in a zone via Musikwolke."""
        result = await self._safe_post(
            f"/api/v1/media/zones/{zone_id}/play", {}, label=f"Musikwolke play {zone_id}",
        )
        if volume_pct is not None and result.get("ok", True):
            await self.async_musikwolke_volume(zone_id, volume_pct)
        return result

    async def async_musikwolke_pause(self, zone_id: str) -> dict[str, Any]:
        """Pause media in a zone via Musikwolke."""
        return await self._safe_post(
            f"/api/v1/media/zones/{zone_id}/pause", {}, label=f"Musikwolke pause {zone_id}",
        )

    async def async_musikwolke_volume(self, zone_id: str, volume_pct: int) -> dict[str, Any]:
        """Set volume for a zone (0-100)."""
        return await self._safe_post(
            f"/api/v1/musikwolke/volume/{zone_id}", {"volume_pct": volume_pct},
            label=f"Musikwolke volume {zone_id}",
        )

    async def async_create_musikwolke(self, zone_ids: list[str]) -> dict[str, Any]:
        """Create a Musikwolke group across zones."""
        return await self._safe_post(
            "/api/v1/musikwolke/create", {"zone_ids": zone_ids}, label="Musikwolke create",
        )

    async def async_dissolve_musikwolke(self, zone_ids: list[str]) -> dict[str, Any]:
        """Dissolve a Musikwolke group."""
        return await self._safe_post(
            "/api/v1/musikwolke/dissolve", {"zone_ids": zone_ids}, label="Musikwolke dissolve",
        )

    async def async_start_media_follow(self, person_id: str, source_zone: str) -> dict[str, Any]:
        """Start a Musikwolke follow session for a person."""
        return await self._safe_post(
            "/api/v1/media/musikwolke/start",
            {"person_id": person_id, "source_zone": source_zone},
            label="Media follow start",
        )

    async def async_stop_media_follow(self, session_id: str) -> dict[str, Any]:
        """Stop a Musikwolke follow session."""
        return await self._safe_post(
            f"/api/v1/media/musikwolke/{session_id}/stop", {}, label="Media follow stop",
        )

    async def async_get_media_follow_sessions(self) -> list[dict[str, Any]]:
        """List active Musikwolke follow sessions."""
        return await self._safe_get(
            "/api/v1/media/musikwolke", [], key="sessions", label="Media follow sessions",
        )

    async def async_set_zone_automation_mode(self, zone_id: str, mode: str) -> dict[str, Any]:
        """Set zone automation mode (off/learning/autonomy)."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/mode", {"mode": mode},
            label=f"Zone automation mode {zone_id}",
        )

    async def async_get_zone_automation_mode(self, zone_id: str) -> str:
        """Get zone automation mode."""
        return await self._safe_get(
            f"/api/v1/zone-automation/zones/{zone_id}/mode", "off",
            key="automation_mode", label=f"Zone automation mode {zone_id}",
        )

    async def async_set_zone_config(self, zone_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Update zone automation config (partial: light, music, or individual fields)."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/config", config,
            label=f"Zone config {zone_id}",
        )

    async def async_set_zone_override(self, zone_id: str, target: str, enabled: bool) -> dict[str, Any]:
        """Toggle zone automation override (light or music)."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/override",
            {"target": target, "enabled": enabled},
            label=f"Zone override {zone_id}/{target}",
        )

    async def async_get_musikwolke_zone_map(self) -> dict[str, Any]:
        """Get zone-to-speaker mapping."""
        return await self._safe_get(
            "/api/v1/musikwolke/zone-map", {"ok": False, "zone_map": {}},
            label="Musikwolke zone map",
        )

    # ── Smart Home Module Dashboards ──────────────────────────────────

    async def async_get_module_dashboards(self) -> dict[str, Any]:
        """Get aggregated dashboard for all 5 smart home modules (single call)."""
        return await self._safe_get(
            "/api/v1/modules/dashboard", {"ok": False, "modules": {}},
            label="Module dashboards API",
        )

    async def async_get_anomaly_status(self) -> dict[str, Any]:
        """Get anomaly detection status and history from Core."""
        return await self._safe_get(
            "/api/v1/anomaly/history?limit=50&level=low",
            {"history": [], "total": 0},
            label="Anomaly API",
        )

    async def async_get_module_zone_detail(self, zone_id: str) -> dict[str, Any]:
        """Get aggregated zone detail for all 5 modules."""
        return await self._safe_get(
            f"/api/v1/modules/zones/{zone_id}",
            {"ok": False, "zone_id": zone_id, "modules": {}},
            label=f"Module zone detail {zone_id}",
        )

    # ── Autonomy / Zone Health (v14.2.0) ────────────────────────────

    async def async_get_autonomy_dashboard(self) -> dict[str, Any]:
        """Fetch autonomy executor dashboard from Core."""
        return await self._safe_get(
            "/api/v1/autonomy/dashboard",
            {},
            label="Autonomy dashboard",
        )

    async def async_get_zone_health(self) -> dict[str, Any]:
        """Fetch zone health overview from Core."""
        return await self._safe_get(
            "/api/v1/zone/health",
            {},
            label="Zone health",
        )

    async def async_get_zone_aggregates(self, zone_id: str) -> dict[str, Any]:
        """Fetch device-class aggregates for a zone."""
        return await self._safe_get(
            f"/api/v1/zone/aggregates/{zone_id}",
            {},
            label=f"Zone aggregates {zone_id}",
        )

    async def async_set_zone_module_state(self, zone_id: str, module_id: str, state: str) -> dict[str, Any]:
        """Set per-zone module state via Core API."""
        return await self._safe_post(
            f"/api/v1/autonomy/zones/{zone_id}/module",
            {"module_id": module_id, "state": state},
            label=f"Zone module state {zone_id}/{module_id}",
        )

    async def async_capture_zone_scene(self, zone_id: str, name: str) -> dict[str, Any]:
        """Capture current zone state as a scene via Core API."""
        return await self._safe_post(
            f"/api/v1/zone/aggregates/{zone_id}/scene/capture",
            {"name": name},
            label=f"Zone scene capture {zone_id}",
        )

    async def async_apply_zone_scene(self, zone_id: str, scene_id: str) -> dict[str, Any]:
        """Apply a saved zone scene via Core API."""
        return await self._safe_post(
            f"/api/v1/zone/aggregates/{zone_id}/scene/apply",
            {"scene_id": scene_id},
            label=f"Zone scene apply {scene_id} in {zone_id}",
        )

    # ── Memory / Conversation ────────────────────────────────────────

    async def async_get_memory_stats(self) -> dict[str, Any]:
        """Get ConversationMemory statistics and learned preferences."""
        return await self._safe_get("/api/styx/memory", {"ok": False}, label="Memory stats API")

    async def async_get_memory_history(
        self, conversation_id: str, limit: int = 20
    ) -> dict[str, Any]:
        """Get conversation history for a specific thread."""
        return await self._safe_get(
            f"/api/styx/memory/history?conversation_id={conversation_id}&limit={limit}",
            {"ok": False, "messages": []},
            label="Memory history API",
        )

    # ── Presence / Light / Chat ────────────────────────────────────────

    async def async_get_presence(self) -> dict[str, Any]:
        """Get presence intelligence data."""
        return await self._safe_get("/api/v1/hub/presence", {"ok": False}, label="Presence API")

    async def async_get_light_intelligence(self) -> dict[str, Any]:
        """Get light intelligence data."""
        return await self._safe_get("/api/v1/hub/light", {"ok": False}, label="Light intelligence API")

    async def async_chat_completions(
        self, messages: list[dict[str, str]], conversation_id: str | None = None
    ) -> dict[str, Any]:
        """Send a chat request to the Core Add-on via /v1/chat/completions."""
        payload: dict[str, Any] = {"model": "pilotsuite", "messages": messages}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        data = await self._request_json(
            "POST",
            "/v1/chat/completions",
            payload=payload,
            # qwen3:4b on HA-class hardware often needs >20s for first tokens.
            timeout_s=CHAT_COMPLETIONS_TIMEOUT_S,
        )
        choices = data.get("choices", [])
        content = ""
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        return {"content": content, "conversation_id": conversation_id}

    async def async_stt(
        self, audio_data: bytes, language: str = "de"
    ) -> dict[str, Any]:
        """Send audio to Core STT endpoint and return transcription."""
        path = f"/api/v1/styx/stt?language={language}"
        last_err: CopilotApiError | None = None

        for idx, base_url in enumerate(self._base_urls):
            url = f"{base_url}{path}"
            try:
                async with self._session.post(
                    url,
                    data=audio_data,
                    headers={
                        **self._headers(),
                        "Content-Type": "audio/wav",
                    },
                    timeout=aiohttp.ClientTimeout(total=AUDIO_TIMEOUT_S),
                ) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                    return await resp.json()
            except asyncio.TimeoutError as err:
                last_err = CopilotApiError(f"Timeout calling {url}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except aiohttp.ClientError as err:
                last_err = CopilotApiError(f"Client error calling {url}: {err}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except CopilotApiError as err:
                last_err = err
                if idx < len(self._base_urls) - 1 and _should_failover(err):
                    continue
                raise
        raise last_err or CopilotApiError("No available Core API endpoint")

    async def async_tts(
        self, text: str, language: str = "de", voice: str | None = None
    ) -> bytes:
        """Send text to Core TTS endpoint and return audio bytes."""
        path = "/api/v1/styx/tts"
        payload = {"text": text, "language": language}
        if voice:
            payload["voice"] = voice
        last_err: CopilotApiError | None = None

        for idx, base_url in enumerate(self._base_urls):
            url = f"{base_url}{path}"
            try:
                async with self._session.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=AUDIO_TIMEOUT_S),
                ) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                    return await resp.read()
            except asyncio.TimeoutError as err:
                last_err = CopilotApiError(f"Timeout calling {url}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except aiohttp.ClientError as err:
                last_err = CopilotApiError(f"Client error calling {url}: {err}")
                if idx < len(self._base_urls) - 1:
                    continue
                raise last_err from err
            except CopilotApiError as err:
                last_err = err
                if idx < len(self._base_urls) - 1 and _should_failover(err):
                    continue
                raise
        raise last_err or CopilotApiError("No available Core API endpoint")

    async def async_voice_status(self) -> dict[str, Any]:
        """Get voice service status from Core."""
        return await self._safe_get(
            "/api/v1/styx/voice/status",
            {"ok": False, "stt": {"available": False}, "tts": {"available": False}},
            label="Voice status",
        )

    async def async_evaluate_neurons(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate neural pipeline with HA states."""
        try:
            data = await self.async_post("/api/v1/neurons/evaluate", context)
            return data.get("data", data)
        except CopilotApiError as e:
            _LOGGER.warning("Neural evaluation failed: %s", e)
        return {}

    @staticmethod
    def _normalize_v1_path(path: str) -> str:
        p = path.strip()
        if p.startswith("/"):
            return p
        if p.startswith("api/") or p.startswith("v1/"):
            return f"/{p}"
        return f"/api/v1/{p}"

    async def get_with_auth(self, path: str, params: dict | None = None) -> dict:
        return await self.async_get(self._normalize_v1_path(path), params=params)

    async def post_with_auth(self, path: str, data: dict | None = None) -> dict:
        return await self.async_post(self._normalize_v1_path(path), payload=data or {})

    async def put_with_auth(self, path: str, data: dict | None = None) -> dict:
        return await self.async_put(self._normalize_v1_path(path), payload=data or {})


class CopilotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator with neural system integration."""
    
    def __init__(self, hass: HomeAssistant, config: dict):
        self._config = config
        session = async_get_clientsession(hass)

        host, port, token = resolve_core_connection_from_mapping(config)
        self._config[CONF_HOST] = host
        self._config[CONF_PORT] = port
        self._config[CONF_TOKEN] = token

        candidate_hosts = build_candidate_hosts(
            host,
            internal_url=getattr(hass.config, "internal_url", None),
            external_url=getattr(hass.config, "external_url", None),
            include_docker_internal=host == "host.docker.internal",
        )
        port_candidates = [port]
        if DEFAULT_PORT not in port_candidates:
            port_candidates.append(DEFAULT_PORT)
        candidate_urls: list[str] = []
        for candidate_host in candidate_hosts:
            for candidate_port in port_candidates:
                url = build_base_url(candidate_host, candidate_port)
                if url not in candidate_urls:
                    candidate_urls.append(url)

        self.api = CopilotApiClient(
            session,
            base_urls=candidate_urls,
            token=token,
        )
        
        # Camera state management
        self.camera_state: dict[str, CameraState] = {}
        self.camera_privacy: dict[str, CameraPrivacySettings] = {}

        # Set by __init__.py after CopilotRuntime.async_setup_entry() completes
        self.modules_ready: bool = False

        # Hybrid mode: 120s fallback polling (real-time via webhook push)
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=120),
        )
    
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with retry on transient failures."""
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                status = await self.api.async_get_status()

                # Get mood from neural system
                mood_data = await self.api.async_get_mood()

                # Get neuron states
                neurons_data = await self.api.async_get_neurons()

                # Get habit learning data from ML context if available
                habit_data = await self._get_habit_learning_data()

                # Get smart home module dashboards (aggregated single call)
                module_data = await self.api.async_get_module_dashboards()

                # Feed module data into HA module stubs
                await self._update_smart_home_modules(module_data)

                # Get anomaly detection data from Core
                anomaly_data = await self.api.async_get_anomaly_status()
                anomaly_history = anomaly_data.get("history", [])
                anomaly_status = {
                    "status": "active" if anomaly_history else "idle",
                    "summary": {
                        "count": len(anomaly_history),
                        "last_anomaly": anomaly_history[0].get("detected_at") if anomaly_history else None,
                        "peak_score": max((a.get("score", 0) for a in anomaly_history), default=0),
                    },
                    "features": list({a.get("anomaly_type", "") for a in anomaly_history if a.get("anomaly_type")}),
                }

                result = {
                    "ok": bool(status.ok) if status.ok is not None else True,
                    "version": status.version or "unknown",
                    "mood": mood_data,
                    "neurons": neurons_data.get("neurons", {}),
                    "dominant_mood": mood_data.get("mood", "unknown"),
                    "mood_confidence": mood_data.get("confidence", 0.0),
                    "habit_summary": habit_data.get("habit_summary", {}),
                    "predictions": habit_data.get("predictions", []),
                    "sequences": habit_data.get("sequences", []),
                    "modules": module_data.get("modules", {}),
                    "anomaly_status": anomaly_status,
                    "alert_history": anomaly_history,
                }

                # Autonomy dashboard (v14.2.0)
                try:
                    autonomy_data = await self.api.async_get_autonomy_dashboard()
                    if autonomy_data:
                        result["autonomy"] = autonomy_data
                except Exception:
                    _LOGGER.debug("Autonomy dashboard fetch skipped")

                # Zone health (v14.2.0)
                try:
                    zone_health = await self.api.async_get_zone_health()
                    if zone_health:
                        result["zone_health"] = zone_health
                except Exception:
                    _LOGGER.debug("Zone health fetch skipped")

                # Zone automation config (per-zone light/music settings)
                try:
                    zone_auto = await self.api.async_get_zone_automation()
                    if zone_auto:
                        result["zone_automation"] = zone_auto
                except Exception:
                    _LOGGER.debug("Zone automation dashboard fetch skipped")

                # Preserve webhook-pushed data across coordinator refreshes
                if self.data:
                    if "autonomy_history" in self.data:
                        result["autonomy_history"] = self.data["autonomy_history"]
                    if "zone_module_states" in self.data:
                        result["zone_module_states"] = self.data["zone_module_states"]

                return result
            except CopilotApiError as err:
                last_err = err
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s backoff
                    _LOGGER.debug("Retrying PilotSuite API (attempt %d): %s", attempt + 1, err)
                continue
                # fallthrough prevented by continue
            except Exception as err:  # noqa: BLE001
                last_err = err
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    _LOGGER.debug(
                        "Retrying PilotSuite API after unexpected error (attempt %d): %s",
                        attempt + 1,
                        err,
                    )
                    continue
                break

        if last_err is None:
            last_err = RuntimeError("unknown API error")
        _LOGGER.warning("PilotSuite API unreachable after 3 attempts: %s", last_err)
        raise UpdateFailed(f"API unavailable after retries: {last_err}") from last_err
    
    async def _update_smart_home_modules(self, module_data: dict[str, Any]) -> None:
        """Feed Core module dashboard data into HA module stubs.

        Each HA smart home module (licht, helligkeit, heiz, bewegung, praesenz)
        stores per-zone state locally. This method bridges Core → HA by pushing
        the aggregated dashboard data from Core into the local module instances.
        """
        modules = module_data.get("modules", {})
        if not modules:
            return

        # Find the active config entry store
        entry_data = self.hass.data.get(DOMAIN, {})
        entry_store: dict[str, Any] | None = None
        for _eid, data in entry_data.items():
            if isinstance(data, dict) and any(
                k.endswith("_module") for k in data
            ):
                entry_store = data
                break

        if not entry_store:
            if not self.modules_ready:
                _LOGGER.debug(
                    "Module entry store noch nicht vorhanden — "
                    "Module-Updates uebersprungen (Module noch nicht geladen)"
                )
            else:
                _LOGGER.warning(
                    "Smart home module entry store nicht gefunden — "
                    "Module-Updates uebersprungen"
                )
            return

        # Also fetch zone automation data for per-zone detail
        try:
            zone_auto = await self.api.async_get_zone_automation()
            zones = zone_auto.get("zones", [])
        except Exception:
            zones = []

        # ── Licht ──
        licht = entry_store.get("licht_module")
        if licht and modules.get("licht"):
            licht_summary = modules["licht"]
            # Push zone-level data from zone automation if available
            for zone in zones:
                zid = zone.get("zone_id", "")
                light_info = zone.get("light", {})
                if zid and light_info:
                    licht.update_zone(
                        zone_id=zid,
                        lights_on=light_info.get("lights_on", 0),
                        lights_total=light_info.get("lights_total", 0),
                        avg_brightness=light_info.get("avg_brightness", 0.0),
                        auto_enabled=light_info.get("auto_enabled", False),
                    )

        # ── Helligkeit ──
        helligkeit = entry_store.get("helligkeit_module")
        if helligkeit and modules.get("helligkeit"):
            for zone in zones:
                zid = zone.get("zone_id", "")
                brightness_info = zone.get("brightness", {})
                if zid and brightness_info:
                    helligkeit.update_zone(
                        zone_id=zid,
                        avg_indoor_lux=brightness_info.get("avg_indoor_lux", 0.0),
                        avg_outdoor_lux=brightness_info.get("avg_outdoor_lux", 0.0),
                        needs_light=brightness_info.get("needs_light", False),
                        deficit_pct=brightness_info.get("deficit_pct", 0.0),
                    )

        # ── Heiz ──
        heiz = entry_store.get("heiz_module")
        if heiz and modules.get("heiz"):
            for zone in zones:
                zid = zone.get("zone_id", "")
                climate_info = zone.get("climate", {})
                if zid and climate_info:
                    heiz.update_zone(zone_id=zid, **climate_info)

        # ── Bewegung ──
        bewegung = entry_store.get("bewegung_module")
        if bewegung and modules.get("bewegung"):
            for zone in zones:
                zid = zone.get("zone_id", "")
                motion_info = zone.get("motion", {})
                if zid and motion_info:
                    bewegung.update_zone(zone_id=zid, **motion_info)

        # ── Praesenz ──
        praesenz = entry_store.get("praesenz_module")
        if praesenz and modules.get("praesenz"):
            for zone in zones:
                zid = zone.get("zone_id", "")
                presence_info = zone.get("presence", {})
                if zid and presence_info:
                    praesenz.update_zone(zone_id=zid, **presence_info)

        _LOGGER.debug(
            "Smart home modules updated: %s",
            [k for k, v in modules.items() if v is not None],
        )

    async def _get_habit_learning_data(self) -> dict[str, Any]:
        """Get habit learning data from ML context."""
        try:
            # Try to get ML context from hass.data
            entry_data = self.hass.data.get("copilot_ha", {})
            
            for entry_id, data in entry_data.items():
                ml_context = data.get("ml_context")
                if ml_context and ml_context.habit_predictor:
                    # Get habit summary
                    summary = ml_context.habit_predictor.get_habit_summary(hours=24)
                    
                    # Build predictions
                    predictions = []
                    for device_id, device_info in summary.get("device_patterns", {}).items():
                        for event_type in device_info.get("event_types", []):
                            pred = ml_context.get_habit_prediction(device_id, event_type)
                            if pred.get("predicted"):
                                predictions.append({
                                    "pattern": f"{device_id}:{event_type}",
                                    "confidence": pred.get("confidence", 0),
                                    "predicted": True,
                                    "details": pred.get("details", {}),
                                })
                    
                    # Build sequences
                    sequences = []
                    for start_device, seq_list in ml_context.habit_predictor.sequence_patterns.items():
                        if seq_list:
                            seq_pred = ml_context.habit_predictor.predict_sequence(start_device)
                            if seq_pred.get("predicted"):
                                sequences.append({
                                    "sequence": seq_pred.get("sequence", []),
                                    "confidence": seq_pred.get("confidence", 0),
                                    "occurrences": seq_pred.get("occurrences", 0),
                                    "predicted": True,
                                })
                    
                    return {
                        "habit_summary": {
                            "total_patterns": summary.get("total_patterns", 0),
                            "time_patterns": summary.get("time_patterns", {}),
                            "sequences": summary.get("sequences", {}),
                            "device_patterns": summary.get("device_patterns", {}),
                            "last_update": summary.get("last_update"),
                        },
                        "predictions": predictions,
                        "sequences": sequences,
                    }
        except Exception as e:
            _LOGGER.debug("Could not get habit learning data: %s", e)
        
        return {
            "habit_summary": {},
            "predictions": [],
            "sequences": [],
        }
    
    @callback
    def async_get_mood(self) -> dict[str, Any]:
        """Get cached mood data."""
        return self.data.get("mood", {}) if self.data else {}
    
    @callback
    def async_get_neurons(self) -> dict[str, Any]:
        """Get cached neuron states."""
        return self.data.get("neurons", {}) if self.data else {}
    
    async def async_evaluate_with_states(self) -> dict[str, Any]:
        """Evaluate neural pipeline with current HA states."""
        # Build context from HA states
        context = {
            "states": {},
            "time": {},
            "weather": {},
            "presence": {},
        }
        
        # Get relevant states
        entity_patterns = [
            "person.", "binary_sensor.", "sensor.temperature", 
            "sensor.humidity", "sensor.light", "sensor.illuminance",
            "weather.", "light.", "media_player."
        ]
        
        for entity_id in self.hass.states.async_entity_ids():
            for pattern in entity_patterns:
                if entity_id.startswith(pattern):
                    state = self.hass.states.get(entity_id)
                    if state:
                        context["states"][entity_id] = {
                            "state": state.state,
                            "attributes": dict(state.attributes)
                        }
                    break
        
        # Evaluate
        return await self.api.async_evaluate_neurons(context)
    
    # ── Autonomy / Zone API wrappers (v14.2.0) ─────────────────────

    async def async_get_autonomy_dashboard(self) -> dict:
        """Fetch autonomy executor dashboard from Core."""
        return await self.api.async_get_autonomy_dashboard()

    async def async_get_zone_health(self) -> dict:
        """Fetch zone health overview from Core."""
        return await self.api.async_get_zone_health()

    async def async_get_zone_aggregates(self, zone_id: str) -> dict:
        """Fetch device-class aggregates for a zone."""
        return await self.api.async_get_zone_aggregates(zone_id)

    async def async_set_zone_module_state(self, zone_id: str, module_id: str, state: str) -> dict:
        """Set per-zone module state via Core API."""
        return await self.api.async_set_zone_module_state(zone_id, module_id, state)

    async def async_set_zone_automation_mode(self, zone_id: str, mode: str) -> dict:
        """Set zone automation mode (off/learning/autonomy)."""
        return await self.api.async_set_zone_automation_mode(zone_id, mode)

    async def async_set_zone_config(self, zone_id: str, config: dict) -> dict:
        """Update zone automation config (partial: light, music fields)."""
        return await self.api.async_set_zone_config(zone_id, config)

    async def async_set_zone_override(self, zone_id: str, target: str, enabled: bool) -> dict:
        """Toggle zone automation override (light or music)."""
        return await self.api.async_set_zone_override(zone_id, target, enabled)

    async def async_capture_zone_scene(self, zone_id: str, name: str) -> dict:
        """Capture current zone state as a scene via Core API."""
        return await self.api.async_capture_zone_scene(zone_id, name)

    async def async_apply_zone_scene(self, zone_id: str, scene_id: str) -> dict:
        """Apply a saved zone scene via Core API."""
        return await self.api.async_apply_zone_scene(zone_id, scene_id)

    # ========== Camera State Management ==========
    
    def register_camera(
        self,
        camera_id: str,
        camera_name: str,
        zones: list[str] | None = None,
        retention_hours: int = 24,
    ) -> CameraState:
        """Register a camera and return its state."""
        if camera_id not in self.camera_state:
            self.camera_state[camera_id] = CameraState(retention_hours=retention_hours)
            self.camera_privacy[camera_id] = CameraPrivacySettings(self.hass, camera_id)
            _LOGGER.info("Registered camera: %s (%s)", camera_name, camera_id)
        else:
            # Update retention
            self.camera_state[camera_id].retention_hours = retention_hours
        return self.camera_state[camera_id]
    
    def unregister_camera(self, camera_id: str) -> None:
        """Unregister a camera."""
        if camera_id in self.camera_state:
            del self.camera_state[camera_id]
            del self.camera_privacy[camera_id]
            _LOGGER.info("Unregistered camera: %s", camera_id)
    
    @callback
    def async_add_motion_event(
        self,
        camera_id: str,
        camera_name: str,
        confidence: float = 1.0,
        zone: str | None = None,
        thumbnail: str | None = None,
    ) -> None:
        """Add a motion event to a camera."""
        if camera_id not in self.camera_state:
            self.register_camera(camera_id, camera_name)
        
        state = self.camera_state[camera_id]
        event = CameraMotionEvent(
            camera_id=camera_id,
            camera_name=camera_name,
            timestamp=dt_util.now(),
            confidence=confidence,
            zone=zone,
            thumbnail=thumbnail,
        )
        state.motion_events.append(event)
        state.last_motion = event.timestamp
        state.is_motion_detected = True
        
        # Clean old events
        self._clean_old_events(camera_id)
        
        _LOGGER.debug("Motion detected: %s at %s", camera_id, event.timestamp)
    
    @callback
    def async_clear_motion(self, camera_id: str) -> None:
        """Clear motion detection for a camera."""
        if camera_id in self.camera_state:
            self.camera_state[camera_id].is_motion_detected = False
    
    @callback
    def async_add_presence_event(
        self,
        camera_id: str,
        camera_name: str,
        presence_type: str = "person",
        person_name: str | None = None,
        confidence: float = 1.0,
    ) -> None:
        """Add a presence event to a camera."""
        if camera_id not in self.camera_state:
            self.register_camera(camera_id, camera_name)
        
        state = self.camera_state[camera_id]
        event = CameraPresenceEvent(
            camera_id=camera_id,
            camera_name=camera_name,
            timestamp=dt_util.now(),
            presence_type=presence_type,
            person_name=person_name,
            confidence=confidence,
        )
        state.presence_events.append(event)
        state.last_presence = event.timestamp
        state.current_presence = presence_type
        
        # Clean old events
        self._clean_old_events(camera_id)
        
        _LOGGER.debug("Presence detected: %s - %s at %s", camera_id, presence_type, event.timestamp)
    
    @callback
    def async_add_activity_event(
        self,
        camera_id: str,
        camera_name: str,
        activity_type: str,
        duration_seconds: int = 0,
        confidence: float = 1.0,
    ) -> None:
        """Add an activity event to a camera."""
        if camera_id not in self.camera_state:
            self.register_camera(camera_id, camera_name)
        
        state = self.camera_state[camera_id]
        event = CameraActivityEvent(
            camera_id=camera_id,
            camera_name=camera_name,
            timestamp=dt_util.now(),
            activity_type=activity_type,
            duration_seconds=duration_seconds,
            confidence=confidence,
        )
        state.activity_events.append(event)
        
        # Clean old events
        self._clean_old_events(camera_id)
        
        _LOGGER.debug("Activity detected: %s - %s at %s", camera_id, activity_type, event.timestamp)
    
    @callback
    def async_add_zone_event(
        self,
        camera_id: str,
        camera_name: str,
        zone_name: str,
        event_type: str = "entered",
        object_type: str | None = None,
    ) -> None:
        """Add a zone event to a camera."""
        if camera_id not in self.camera_state:
            self.register_camera(camera_id, camera_name)
        
        state = self.camera_state[camera_id]
        event = CameraZoneEvent(
            camera_id=camera_id,
            camera_name=camera_name,
            timestamp=dt_util.now(),
            zone_name=zone_name,
            event_type=event_type,
            object_type=object_type,
        )
        state.zone_events.append(event)
        
        # Clean old events
        self._clean_old_events(camera_id)
        
        _LOGGER.debug("Zone event: %s - %s %s at %s", camera_id, zone_name, event_type, event.timestamp)
    
    def _clean_old_events(self, camera_id: str) -> None:
        """Clean old events based on retention policy."""
        if camera_id not in self.camera_state:
            return
        
        state = self.camera_state[camera_id]
        retention = timedelta(hours=state.retention_hours)
        now = dt_util.now()
        
        # Clean motion events
        state.motion_events = [
            e for e in state.motion_events
            if now - e.timestamp < retention
        ]
        
        # Clean presence events
        state.presence_events = [
            e for e in state.presence_events
            if now - e.timestamp < retention
        ]
        
        # Clean activity events
        state.activity_events = [
            e for e in state.activity_events
            if now - e.timestamp < retention
        ]
        
        # Clean zone events
        state.zone_events = [
            e for e in state.zone_events
            if now - e.timestamp < retention
        ]
        
        # Update 24h motion count
        state.motion_count_24h = sum(
            1 for e in state.motion_events
            if now - e.timestamp < timedelta(hours=24)
        )
    
    def get_camera_privacy(self, camera_id: str) -> CameraPrivacySettings | None:
        """Get privacy settings for a camera."""
        return self.camera_privacy.get(camera_id)
    
    def set_camera_face_blur(self, camera_id: str, enabled: bool) -> None:
        """Enable/disable face blur for a camera."""
        if camera_id in self.camera_privacy:
            self.camera_privacy[camera_id].face_blur_enabled = enabled
    
    def set_camera_retention(self, camera_id: str, hours: int) -> None:
        """Set retention hours for a camera."""
        if camera_id in self.camera_state:
            self.camera_state[camera_id].retention_hours = hours
            self._clean_old_events(camera_id)
