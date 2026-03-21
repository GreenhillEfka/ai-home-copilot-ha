"""PilotSuite — Coordinator with Neural System."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import logging
import time
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

# ── Adaptive polling constants ──────────────────────────────────────
POLL_INTERVAL_NORMAL_S = 120   # Default / backward-compatible interval
POLL_INTERVAL_IDLE_S = 180     # Stretched interval when data is stale
POLL_NO_CHANGE_THRESHOLD = 5   # Consecutive unchanged polls before stretching

# ── Priority data categories ────────────────────────────────────────
# HIGH: fetched every poll cycle
# MEDIUM: fetched every 2nd poll cycle
# LOW: fetched every 3rd poll cycle
PRIORITY_HIGH = "high"      # mood, zone_automation status
PRIORITY_MEDIUM = "medium"  # neurons, module_dashboards
PRIORITY_LOW = "low"        # anomaly_status, autonomy_dashboard


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
        try:
            data = await self._request_json(
                "GET", "/api/v1/zone-automation/dashboard",
            )
            zones = data.get("zones", [])
            _LOGGER.debug(
                "Zone automation: fetched %d zones from %s",
                len(zones), self._active_base_url,
            )
            return data
        except Exception as exc:
            _LOGGER.warning("Zone automation API failed: %s", exc)
            return {"zones": [], "summary": {}}

    async def async_ensure_zone_automation_zones(self, zone_ids: list[str]) -> dict[str, Any]:
        """Ensure zone automation configs exist for given zone IDs.

        Calls Core's ensure-zones endpoint which auto-creates missing zones
        and returns the updated dashboard.
        """
        return await self._safe_post(
            "/api/v1/zone-automation/ensure-zones",
            {"zone_ids": zone_ids},
            label="Zone automation ensure-zones",
        )

    async def async_sync_zone_definitions(self, zones: list[dict[str, Any]]) -> dict[str, Any]:
        """Push full zone definitions (entities, roles, metadata) to Core.

        Goes beyond ensure-zones by syncing entity assignments and zone metadata
        so Core's Brain/Neuron system knows the full zone topology.
        """
        zone_ids = [z.get("zone_id", z.get("id", "")) for z in zones if z.get("zone_id") or z.get("id")]
        return await self._safe_post(
            "/api/v1/zone-automation/ensure-zones",
            {"zone_ids": zone_ids},
            label="Zone definitions sync",
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
        """Update zone automation config (partial: light, music, modules, or individual fields)."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/config", config,
            label=f"Zone config {zone_id}",
        )

    async def async_get_module_schemas(self) -> dict[str, Any]:
        """Fetch self-describing module schemas from Core.

        Returns dict of module_id -> {name_de, icon, color, fields: [...]}.
        Used by HA to dynamically generate per-zone entities.
        """
        try:
            data = await self._request_json(
                "GET", "/api/v1/zone-automation/module-schemas",
            )
            schemas = data.get("schemas", {})
            _LOGGER.info(
                "Module schemas: fetched %d modules (%s)",
                len(schemas), ", ".join(schemas.keys()),
            )
            return schemas
        except Exception as exc:
            _LOGGER.warning("Module schemas API failed: %s", exc)
            return {}

    async def async_set_zone_module_config(
        self, zone_id: str, module_id: str, config: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a specific module config for a zone."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/modules/{module_id}",
            config,
            label=f"Zone module config {zone_id}/{module_id}",
        )

    async def async_send_suggestion_feedback(
        self,
        suggestion_id: str,
        accepted: bool,
        *,
        related_entities: list[str] | None = None,
        pattern_key: str = "",
    ) -> dict[str, Any]:
        """Send suggestion accept/reject feedback to Core for Brain Graph weight adjustment.

        Core's FeedbackLoop adjusts Brain Graph weights:
        - Accept: +0.5 weight boost on correlated edges
        - Reject: -0.3 weight penalty on correlated edges
        """
        payload: dict[str, Any] = {
            "suggestion_id": suggestion_id,
            "accepted": accepted,
        }
        if related_entities:
            payload["related_entities"] = related_entities
        if pattern_key:
            payload["pattern_key"] = pattern_key
        return await self._safe_post(
            "/api/v1/integration/feedback",
            payload,
            label="Suggestion feedback",
        )

    async def async_sync_habitus_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Push habitus mining config from HA to Core.

        Config may include: min_support, min_confidence, context_features,
        auto_mine_interval_s, auto_mine_event_threshold.
        """
        return await self._safe_post(
            "/api/v1/habitus/config", config, label="Habitus config sync",
        )

    async def async_get_habitus_config(self) -> dict[str, Any]:
        """Get current habitus mining config from Core."""
        return await self._safe_get(
            "/api/v1/habitus/config", {},
            label="Habitus config",
        )

    async def async_get_mood_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get mood snapshots from Core for the last N hours."""
        return await self._safe_get(
            f"/api/v1/neurons/mood/history?hours={hours}", [],
            key="snapshots", label="Mood history",
        )

    async def async_get_mood_trend(self, hours: int = 24) -> dict[str, Any]:
        """Get mood distribution/trend from Core for the last N hours."""
        return await self._safe_get(
            f"/api/v1/neurons/mood/trend?hours={hours}", {},
            label="Mood trend",
        )

    async def async_set_zone_override(self, zone_id: str, target: str, enabled: bool) -> dict[str, Any]:
        """Toggle zone automation override (light or music)."""
        return await self._safe_post(
            f"/api/v1/zone-automation/zones/{zone_id}/override",
            {"target": target, "enabled": enabled},
            label=f"Zone override {zone_id}/{target}",
        )

    async def async_set_zone_presence_hold(self, zone_id: str, hold: str) -> dict[str, Any]:
        """Set zone presence hold state (auto, force_on, force_off).

        Used by AreaPresenceSensor to persist hold-switch changes to Core.
        """
        return await self._safe_post(
            f"/api/v1/presence/zone/presence/{zone_id}/hold",
            {"hold": hold},
            label=f"Zone presence hold {zone_id}/{hold}",
        )

    async def async_set_zone_presence_state(
        self,
        zone_id: str,
        occupied: bool,
        primary_source: str | None,
        confidence: float,
        hold_state: str,
    ) -> dict[str, Any]:
        """Send aggregated presence state from HA AreaPresenceSensor to Core Neurons.

        Called when Core is unreachable and HA's any-on aggregation is authoritative.
        Throttled by the sensor to ≤1 call / 30 s per zone.
        """
        return await self._safe_post(
            f"/api/v1/presence/zone/presence/{zone_id}/state",
            {
                "occupied": occupied,
                "primary_source": primary_source,
                "confidence": confidence,
                "hold_state": hold_state,
            },
            label=f"Zone presence state {zone_id}",
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


# ── Circuit Breaker ──────────────────────────────────────────────────
_CB_FAILURE_THRESHOLD = 3   # consecutive failures before opening
_CB_RECOVERY_TIMEOUT_S = 60  # seconds to wait before half-open retry


class _CircuitBreakerState:
    """Simple circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED."""

    __slots__ = ("_failures", "_opened_at", "_state")

    def __init__(self) -> None:
        self._failures: int = 0
        self._opened_at: float = 0.0
        self._state: str = "closed"  # closed | open | half_open

    @property
    def state(self) -> str:
        if self._state == "open":
            elapsed = asyncio.get_event_loop().time() - self._opened_at
            if elapsed >= _CB_RECOVERY_TIMEOUT_S:
                self._state = "half_open"
        return self._state

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= _CB_FAILURE_THRESHOLD:
            self._state = "open"
            self._opened_at = asyncio.get_event_loop().time()
            _LOGGER.warning(
                "Circuit breaker OPEN after %d consecutive failures — "
                "skipping Core API calls for %ds",
                self._failures, _CB_RECOVERY_TIMEOUT_S,
            )

    @property
    def is_open(self) -> bool:
        return self.state == "open"


class CopilotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator with neural system integration."""

    def __init__(self, hass: HomeAssistant, config: dict):
        self._config = config
        self._circuit_breaker = _CircuitBreakerState()
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

        # Zone module schemas (fetched once from Core, cached with TTL)
        self.module_schemas: dict[str, Any] = {}
        self._module_schemas_fetched_at: float = 0.0  # time.monotonic() of last successful fetch
        self._module_schemas_ttl_s: float = 3600.0  # refresh every 1h (schema changes are rare)

        # ── Multi-tier adaptive polling state ───────────────────────────
        self._poll_generation: int = 0       # Monotonic counter, decides priority tiers
        self._consecutive_no_changes: int = 0  # Unchanged polls → stretch interval
        self._consecutive_failures: int = 0    # API failures toward Core
        self._last_fetch_duration_s: float = 0.0  # Last successful fetch duration
        self._previous_mood: str | None = None   # For change detection
        self._previous_zone_modes: dict[str, str] = {}  # zone_id → mode
        self._last_webhook_ts: float = 0.0   # time.monotonic() of last webhook push

        # Hybrid mode: 120s fallback polling (real-time via webhook push)
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=POLL_INTERVAL_NORMAL_S),
        )
    
    # ── Priority tier helpers ─────────────────────────────────────────

    def _should_fetch_tier(self, tier: str) -> bool:
        """Decide whether a priority tier should be fetched this cycle.

        HIGH  → every poll
        MEDIUM → every 2nd poll (generation % 2 == 0)
        LOW   → every 3rd poll (generation % 3 == 0)
        """
        if tier == PRIORITY_HIGH:
            return True
        if tier == PRIORITY_MEDIUM:
            return self._poll_generation % 2 == 0
        if tier == PRIORITY_LOW:
            return self._poll_generation % 3 == 0
        return True  # unknown tier → always fetch

    def _adjust_poll_interval(self, data_changed: bool) -> None:
        """Adapt update_interval based on change frequency.

        If data hasn't changed for POLL_NO_CHANGE_THRESHOLD consecutive polls,
        stretch to POLL_INTERVAL_IDLE_S. Reset to POLL_INTERVAL_NORMAL_S when
        a webhook push is received or data changes.
        """
        if data_changed:
            self._consecutive_no_changes = 0
            if self.update_interval != timedelta(seconds=POLL_INTERVAL_NORMAL_S):
                _LOGGER.debug(
                    "Adaptive polling: data changed, restoring %ds interval",
                    POLL_INTERVAL_NORMAL_S,
                )
                self.update_interval = timedelta(seconds=POLL_INTERVAL_NORMAL_S)
        else:
            self._consecutive_no_changes += 1
            if (
                self._consecutive_no_changes >= POLL_NO_CHANGE_THRESHOLD
                and self.update_interval != timedelta(seconds=POLL_INTERVAL_IDLE_S)
            ):
                _LOGGER.debug(
                    "Adaptive polling: %d unchanged polls, stretching to %ds",
                    self._consecutive_no_changes,
                    POLL_INTERVAL_IDLE_S,
                )
                self.update_interval = timedelta(seconds=POLL_INTERVAL_IDLE_S)

    def _detect_changes_and_fire_events(self, result: dict[str, Any]) -> bool:
        """Compare result with previous data and fire HA events on changes.

        Returns True if any tracked data changed.
        """
        changed = False

        # ── Mood change detection ────────────────────────────────────
        new_mood = result.get("dominant_mood", "unknown")
        if self._previous_mood is not None and new_mood != self._previous_mood:
            changed = True
            _LOGGER.info(
                "Mood changed: %s → %s", self._previous_mood, new_mood,
            )
            self.hass.bus.async_fire(
                f"{DOMAIN}_mood_changed",
                {
                    "previous_mood": self._previous_mood,
                    "new_mood": new_mood,
                    "confidence": result.get("mood_confidence", 0.0),
                },
            )
        self._previous_mood = new_mood

        # ── Zone automation mode change detection ────────────────────
        zone_auto = result.get("zone_automation", {})
        new_zone_modes: dict[str, str] = {}
        for zone_info in zone_auto.get("zones", []):
            zid = zone_info.get("zone_id", "")
            config = zone_info.get("config", {})
            mode = config.get("automation_mode", "off")
            if zid:
                new_zone_modes[zid] = mode

        if self._previous_zone_modes:
            for zid, new_mode in new_zone_modes.items():
                old_mode = self._previous_zone_modes.get(zid)
                if old_mode is not None and new_mode != old_mode:
                    changed = True
                    _LOGGER.info(
                        "Zone mode changed: %s %s → %s", zid, old_mode, new_mode,
                    )
                    self.hass.bus.async_fire(
                        f"{DOMAIN}_zone_mode_changed",
                        {
                            "zone_id": zid,
                            "previous_mode": old_mode,
                            "new_mode": new_mode,
                        },
                    )

        self._previous_zone_modes = new_zone_modes
        return changed

    # ── Webhook-triggered refresh ──────────────────────────────────

    @callback
    def async_notify_webhook_received(self) -> None:
        """Called by webhook handler to signal that fresh data was pushed.

        Resets the adaptive interval back to normal so the next scheduled
        poll doesn't wait the stretched idle interval.
        """
        self._last_webhook_ts = time.monotonic()
        self._consecutive_no_changes = 0
        if self.update_interval != timedelta(seconds=POLL_INTERVAL_NORMAL_S):
            _LOGGER.debug(
                "Adaptive polling: webhook received, restoring %ds interval",
                POLL_INTERVAL_NORMAL_S,
            )
            self.update_interval = timedelta(seconds=POLL_INTERVAL_NORMAL_S)

    async def async_request_refresh_for(self, data_type: str) -> None:
        """Request an immediate targeted refresh for a specific data type.

        Called by webhook handler when push data arrives for mood/zone/autonomy
        so that derived data (zone states, module stubs) stays in sync without
        waiting for the next scheduled poll.

        Falls back to a full coordinator refresh on failure.
        """
        try:
            current = dict(self.data) if self.data else {}

            if data_type == "mood":
                mood_data = await self.api.async_get_mood()
                current["mood"] = mood_data
                current["dominant_mood"] = mood_data.get("mood", "unknown")
                current["mood_confidence"] = mood_data.get("confidence", 0.0)

            elif data_type == "zone_automation":
                zone_auto = await self.api.async_get_zone_automation()
                if isinstance(zone_auto, dict) and zone_auto:
                    current["zone_automation"] = zone_auto
                    await self._sync_zone_states(current, zone_auto)

            elif data_type == "autonomy":
                autonomy_data = await self.api.async_get_autonomy_dashboard()
                if isinstance(autonomy_data, dict) and autonomy_data:
                    current["autonomy"] = autonomy_data

            elif data_type == "neurons":
                neurons_data = await self.api.async_get_neurons()
                current["neurons"] = neurons_data.get("neurons", {})

            elif data_type == "anomaly":
                anomaly_data = await self.api.async_get_anomaly_status()
                anomaly_history = anomaly_data.get("history", [])
                current["anomaly_status"] = {
                    "status": "active" if anomaly_history else "idle",
                    "summary": {
                        "count": len(anomaly_history),
                        "last_anomaly": (
                            anomaly_history[0].get("detected_at")
                            if anomaly_history else None
                        ),
                        "peak_score": max(
                            (a.get("score", 0) for a in anomaly_history),
                            default=0,
                        ),
                    },
                    "features": list(
                        {a.get("anomaly_type", "")
                         for a in anomaly_history if a.get("anomaly_type")}
                    ),
                }
                current["alert_history"] = anomaly_history

            else:
                _LOGGER.debug(
                    "Unknown data_type '%s' for targeted refresh, triggering full refresh",
                    data_type,
                )
                await self.async_request_refresh()
                return

            # Notify webhook timestamp + reset adaptive interval
            self.async_notify_webhook_received()

            # Detect changes and fire events
            self._detect_changes_and_fire_events(current)

            # Push the updated data to listeners
            self.async_set_updated_data(current)
            _LOGGER.debug("Targeted refresh completed for '%s'", data_type)

        except Exception:
            _LOGGER.debug(
                "Targeted refresh for '%s' failed, falling back to full refresh",
                data_type,
                exc_info=True,
            )
            await self.async_request_refresh()

    # ── Main update method ─────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with prioritized tiers, adaptive interval, and circuit breaker."""
        # Circuit breaker: skip all Core calls when open
        if self._circuit_breaker.is_open:
            _LOGGER.debug("Circuit breaker OPEN — returning stale data")
            if self.data:
                return self.data
            raise UpdateFailed("Core API circuit breaker is open")

        gen = self._poll_generation
        self._poll_generation += 1
        fetch_medium = self._should_fetch_tier(PRIORITY_MEDIUM)
        fetch_low = self._should_fetch_tier(PRIORITY_LOW)

        _LOGGER.debug(
            "Poll generation %d: HIGH=always, MEDIUM=%s, LOW=%s",
            gen, fetch_medium, fetch_low,
        )

        last_err: Exception | None = None
        start = time.monotonic()
        for attempt in range(3):
            try:
                # ── Parallel batch 1: HIGH + conditional MEDIUM/LOW ──
                coros: list[Any] = [
                    # HIGH priority (always)
                    self.api.async_get_status(),       # [0]
                    self.api.async_get_mood(),          # [1]
                    self._get_habit_learning_data(),    # [2]
                ]
                # MEDIUM priority (every 2nd poll)
                coros.append(
                    self.api.async_get_neurons() if fetch_medium
                    else asyncio.sleep(0, result=None)
                )  # [3]
                coros.append(
                    self.api.async_get_module_dashboards() if fetch_medium
                    else asyncio.sleep(0, result=None)
                )  # [4]
                # LOW priority (every 3rd poll)
                coros.append(
                    self.api.async_get_anomaly_status() if fetch_low
                    else asyncio.sleep(0, result=None)
                )  # [5]

                batch1 = await asyncio.gather(*coros)
                status = batch1[0]
                mood_data = batch1[1]
                habit_data = batch1[2]
                neurons_data = batch1[3]
                module_data = batch1[4]
                anomaly_data = batch1[5]

                # Start building result from current data (preserve skipped tiers)
                result: dict[str, Any] = dict(self.data) if self.data else {}

                # HIGH: always update
                result["ok"] = bool(status.ok) if status.ok is not None else True
                result["version"] = status.version or "unknown"
                result["mood"] = mood_data
                result["dominant_mood"] = mood_data.get("mood", "unknown")
                result["mood_confidence"] = mood_data.get("confidence", 0.0)
                result["habit_summary"] = habit_data.get("habit_summary", {})
                result["predictions"] = habit_data.get("predictions", [])
                result["sequences"] = habit_data.get("sequences", [])

                # MEDIUM: update only when fetched
                if fetch_medium:
                    if neurons_data is not None:
                        result["neurons"] = neurons_data.get("neurons", {})
                    if module_data is not None:
                        result["modules"] = module_data.get("modules", {})
                        # Feed module data into HA module stubs
                        await self._update_smart_home_modules(module_data)

                # LOW: update only when fetched
                if fetch_low and anomaly_data is not None:
                    anomaly_history = anomaly_data.get("history", [])
                    result["anomaly_status"] = {
                        "status": "active" if anomaly_history else "idle",
                        "summary": {
                            "count": len(anomaly_history),
                            "last_anomaly": anomaly_history[0].get("detected_at") if anomaly_history else None,
                            "peak_score": max((a.get("score", 0) for a in anomaly_history), default=0),
                        },
                        "features": list({a.get("anomaly_type", "") for a in anomaly_history if a.get("anomaly_type")}),
                    }
                    result["alert_history"] = anomaly_history

                # ── Parallel batch 2: secondary API calls ────────────
                # zone_automation is HIGH priority; autonomy/zone_health are LOW
                batch2_coros = [
                    self.api.async_get_zone_automation(),  # [0] HIGH
                ]
                batch2_coros.append(
                    self.api.async_get_autonomy_dashboard() if fetch_low
                    else asyncio.sleep(0, result=None)
                )  # [1]
                batch2_coros.append(
                    self.api.async_get_zone_health() if fetch_low
                    else asyncio.sleep(0, result=None)
                )  # [2]

                batch2 = await asyncio.gather(
                    *batch2_coros,
                    return_exceptions=True,
                )
                zone_auto = batch2[0]
                autonomy_data_b2 = batch2[1]
                zone_health = batch2[2]

                if fetch_low:
                    if isinstance(autonomy_data_b2, dict) and autonomy_data_b2:
                        result["autonomy"] = autonomy_data_b2
                    if isinstance(zone_health, dict) and zone_health:
                        result["zone_health"] = zone_health

                if isinstance(zone_auto, dict) and zone_auto:
                    result["zone_automation"] = zone_auto
                    await self._sync_zone_states(result, zone_auto)

                # Fetch module schemas once (cached with TTL: 1h)
                stale = (
                    not self.module_schemas
                    or (time.monotonic() - self._module_schemas_fetched_at) > self._module_schemas_ttl_s
                )
                if stale:
                    try:
                        self.module_schemas = await self.api.async_get_module_schemas()
                        self._module_schemas_fetched_at = time.monotonic()
                        _LOGGER.debug(
                            "Module schemas refreshed (TTL=%.0fs)",
                            self._module_schemas_ttl_s,
                        )
                    except Exception:
                        if not self.module_schemas:
                            _LOGGER.debug("Module schemas fetch deferred")

                # Zone automation sync: ensure HA zones exist in Core on first refresh
                if not getattr(self, "_zone_auto_synced", False):
                    await self._first_zone_sync(result)

                # Habitus config sync: push HA config to Core on first refresh
                if not getattr(self, "_habitus_config_synced", False):
                    try:
                        cfg = self.config_entry.data | self.config_entry.options
                        habitus_cfg = {
                            k: v for k, v in cfg.items()
                            if k.startswith("habitus_") or k in (
                                "min_support", "min_confidence", "context_features",
                            )
                        }
                        if habitus_cfg:
                            await self.api.async_sync_habitus_config(habitus_cfg)
                            _LOGGER.debug("Habitus config synced to Core: %s", list(habitus_cfg.keys()))
                        self._habitus_config_synced = True
                    except Exception:
                        _LOGGER.debug("Habitus config sync skipped")

                # Preserve webhook-pushed data across coordinator refreshes
                if self.data:
                    for key in (
                        "autonomy_history", "autonomy_errors",
                        "zone_module_states", "zone_updates",
                        "neurons_fired", "brain_insights",
                        "ranked_candidates", "zone_moods",
                    ):
                        if key in self.data and key not in result:
                            result[key] = self.data[key]

                # ── Change detection + adaptive polling ──────────────
                data_changed = self._detect_changes_and_fire_events(result)
                self._adjust_poll_interval(data_changed)

                # Circuit breaker: successful cycle → reset
                self._circuit_breaker.record_success()
                self._consecutive_failures = 0
                self._last_fetch_duration_s = time.monotonic() - start
                return result
            except CopilotApiError as err:
                last_err = err
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s backoff
                    _LOGGER.debug("Retrying PilotSuite API (attempt %d): %s", attempt + 1, err)
                continue
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

        # All retries exhausted → record failure for circuit breaker
        self._circuit_breaker.record_failure()
        self._consecutive_failures += 1
        if last_err is None:
            last_err = RuntimeError("unknown API error")
        _LOGGER.warning("PilotSuite API unreachable after 3 attempts: %s", last_err)
        raise UpdateFailed(f"API unavailable after retries: {last_err}") from last_err

    async def _sync_zone_states(
        self, result: dict[str, Any], zone_auto: dict[str, Any],
    ) -> None:
        """Sync zone automation states from Core response into HA zone store."""
        try:
            from .habitus_zones_store_v2 import (
                async_get_zones_v2,
                async_set_zone_state,
            )
            ha_zones = await async_get_zones_v2(
                self.hass, self.config_entry.entry_id,
            )
            ha_zone_ids = {z.zone_id for z in ha_zones}
            for core_zone in zone_auto.get("zones", []):
                core_id = core_zone.get("zone_id", "")
                config = core_zone.get("config", {})
                mode = config.get("automation_mode", "off")
                matched_id = None
                if f"zone:{core_id}" in ha_zone_ids:
                    matched_id = f"zone:{core_id}"
                elif core_id in ha_zone_ids:
                    matched_id = core_id
                if matched_id:
                    new_state = "active" if mode != "off" else "idle"
                    await async_set_zone_state(
                        self.hass,
                        self.config_entry.entry_id,
                        matched_id,
                        new_state,
                        fire_event=True,
                    )
        except Exception:
            _LOGGER.debug("Zone state sync skipped")

    async def _first_zone_sync(self, result: dict[str, Any]) -> None:
        """One-time zone automation sync: ensure HA zones exist in Core."""
        try:
            from .habitus_zones_store_v2 import async_get_zones_v2

            ha_zones = await async_get_zones_v2(
                self.hass, self.config_entry.entry_id,
            )
            if ha_zones:
                zone_ids = [z.zone_id for z in ha_zones if z.zone_id]
                # Strip 'zone:' prefix for Core compatibility
                clean_ids = [
                    zid.removeprefix("zone:") for zid in zone_ids
                ]
                synced = await self.api.async_ensure_zone_automation_zones(clean_ids)
                if synced and synced.get("zones"):
                    result["zone_automation"] = synced
                _LOGGER.info(
                    "Zone automation synced %d zones to Core (created: %s)",
                    len(clean_ids),
                    synced.get("created", []),
                )

                # Push full zone definitions (entities, roles, metadata)
                zone_defs = []
                for z in ha_zones:
                    zid = z.zone_id.removeprefix("zone:")
                    meta = z.metadata or {}
                    zone_defs.append({
                        "zone_id": zid,
                        "name": z.name,
                        "zone_type": z.zone_type,
                        "entity_ids": list(z.entity_ids),
                        "entities": {
                            role: list(eids)
                            for role, eids in (z.entities or {}).items()
                        },
                        "floor": z.floor,
                        "priority": z.priority,
                        "tags": list(z.tags),
                        "ha_area_ids": meta.get("ha_area_ids", []),
                        "ha_area_names": meta.get("ha_area_names", []),
                    })
                await self.api.async_sync_zone_definitions(zone_defs)
                _LOGGER.info(
                    "Zone definitions synced: %d zones with %d total entities",
                    len(zone_defs),
                    sum(len(zd["entity_ids"]) for zd in zone_defs),
                )
            self._zone_auto_synced = True
        except Exception:
            _LOGGER.debug("Zone automation sync skipped")
    
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
