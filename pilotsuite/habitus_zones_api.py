"""API endpoints for habitat zones in the HA integration.

WebSocket commands exposed:
  pilotsuite/habitus/zones          — list all zones for the config entry
  pilotsuite/habitus/zones/sync    — trigger Core zone sync and return result
  pilotsuite/habitus/match_zone    — match a zone by name text (exact / fuzzy)
  pilotsuite/habitus/get_suggestions — autocomplete suggestions
  pilotsuite/habitus/entities_in_zone — entities for a zone type (stub / extensible)

All commands resolve the active PilotSuite config entry from the WS connection
context so callers do not need to pass entry_id manually.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .habitus_zones_store_v2 import async_get_zones_v2

try:
    from copilot_core.homeassistant.habitus_zones_matcher import (
        create_zone_matcher,
        get_zone_suggestions,
    )
    from copilot_core.homeassistant.habitus_zones import ZoneType
    HAS_ZONE_MATCHER = True
except ImportError:
    HAS_ZONE_MATCHER = False

_LOGGER = logging.getLogger(__name__)

# ── entry-id resolution ───────────────────────────────────────────────────────

def _entry_id_from_connection(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection,
) -> str | None:
    """Resolve the active PilotSuite config entry id from a WS connection.

    HA >= 2024.2 stores the ConfigEntry as connection.context.settings_data.
    The fallback iterates all DOMAIN entries (appropriate for single-instance setups).
    Returns None when no entry is found — callers must handle this gracefully.
    """
    settings_data = getattr(connection.context, "settings_data", None)
    if settings_data is not None:
        entry_id = getattr(settings_data, "entry_id", None)
        if entry_id:
            return entry_id

    # Fallback: return the first available PilotSuite entry.
    entry_data = hass.data.get(DOMAIN, {})
    if isinstance(entry_data, dict):
        for eid in entry_data:
            return eid
    return None


# ── sync-status helpers ───────────────────────────────────────────────────────

def _zone_summary_for_response(zones: list) -> dict[str, Any]:
    """Summarise zone state for dashboard / frontend consumption."""
    total = len(zones)
    by_state: dict[str, int] = {}
    by_type: dict[str, int] = {}
    total_entities = 0

    for z in zones:
        state = getattr(z, "current_state", "unknown")
        ztype = getattr(z, "zone_type", "room")
        entities = getattr(z, "entity_ids", ()) or ()
        by_state[state] = by_state.get(state, 0) + 1
        by_type[ztype] = by_type.get(ztype, 0) + 1
        total_entities += len(entities)

    return {
        "total_zones": total,
        "total_entities": total_entities,
        "by_state": by_state,
        "by_type": by_type,
        "has_zones": total > 0,
    }


def _serialize_zone(z) -> dict[str, Any]:
    """Serialize a HabitusZoneV2 dataclass to a JSON-serializable dict."""
    if hasattr(z, "to_dict") and callable(z.to_dict):
        return z.to_dict()
    return {
        "zone_id": getattr(z, "zone_id", None),
        "name": getattr(z, "name", ""),
        "zone_type": getattr(z, "zone_type", "room"),
        "current_state": getattr(z, "current_state", "idle"),
        "entity_ids": list(getattr(z, "entity_ids", ()) or []),
        "entities": dict(getattr(z, "entities", {}) or {}),
        "floor": getattr(z, "floor", None),
        "priority": getattr(z, "priority", 0),
        "tags": list(getattr(z, "tags", ()) or []),
        "metadata": dict(getattr(z, "metadata", {}) or {}),
    }


# ── WebSocket commands ─────────────────────────────────────────────────────────

@websocket_api.websocket_command({"type": "pilotsuite/habitus/zones"})
@websocket_api.async_response
async def ws_get_habitus_zones(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List all Habitus zones for the active config entry.

    Response:
      zones   — list of serialized zone objects
      summary — aggregated counts (total_zones, total_entities, by_state, by_type)
    """
    entry_id = _entry_id_from_connection(hass, connection)
    if not entry_id:
        connection.send_error(msg["id"], "not_found", "PilotSuite not configured")
        return

    try:
        zones = await async_get_zones_v2(hass, entry_id)
        connection.send_result(msg["id"], {
            "zones": [_serialize_zone(z) for z in zones],
            "summary": _zone_summary_for_response(zones),
        })
    except Exception as e:
        _LOGGER.error("ws_get_habitus_zones: %s", e)
        connection.send_error(msg["id"], "get_failed", str(e))


@websocket_api.websocket_command({"type": "pilotsuite/habitus/zones/sync"})
@websocket_api.async_response
async def ws_sync_habitus_zones(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Trigger a zone-definition sync to Core and return the result.

    Calls coordinator._first_zone_sync() which:
      1. Loads HA zones from store
      2. POSTs /api/v1/zone-automation/ensure-zones
      3. POSTs /api/v1/zone-automation/sync-definitions

    Response:
      ok          — True on any successful Core response
      synced      — number of zones synced
      errors      — list of error strings (empty on full success)
    """
    entry_id = _entry_id_from_connection(hass, connection)
    if not entry_id:
        connection.send_error(msg["id"], "not_found", "PilotSuite not configured")
        return

    try:
        entry_store = hass.data.get(DOMAIN, {}).get(entry_id, {})
        coord = entry_store.get("coordinator") if isinstance(entry_store, dict) else None

        if coord is None:
            connection.send_error(msg["id"], "coordinator_unavailable",
                                 "PilotSuite coordinator not ready")
            return

        # _first_zone_sync() is normally called once on first coordinator refresh.
        # Re-running it here lets operators manually re-sync after zone changes.
        # Guard to avoid infinite loops: only run if zones exist.
        from .habitus_zones_store_v2 import async_get_zones_v2
        zones = await async_get_zones_v2(hass, entry_id)

        if not zones:
            connection.send_result(msg["id"], {
                "ok": True,
                "synced": 0,
                "errors": [],
                "message": "no zones to sync",
            })
            return

        # Build result dict (mirrors what _first_zone_sync logs)
        zone_ids = [z.zone_id.removeprefix("zone:") for z in zones if z.zone_id]
        synced = {"zones": zone_ids, "created": []}
        errors: list[str] = []

        # Try ensure-zones
        try:
            ensure_result = await coord.api.async_ensure_zone_automation_zones(zone_ids)
            if ensure_result:
                synced = ensure_result
        except Exception as exc:
            errors.append(f"ensure-zones: {exc}")

        # Try sync-definitions
        zone_defs = []
        for z in zones:
            meta = z.metadata or {}
            zone_defs.append({
                "zone_id": z.zone_id.removeprefix("zone:"),
                "name": z.name,
                "zone_type": z.zone_type,
                "entity_ids": list(z.entity_ids),
                "entities": {k: list(v) for k, v in (z.entities or {}).items()},
                "floor": z.floor,
                "priority": z.priority,
                "tags": list(z.tags),
                "ha_area_ids": meta.get("ha_area_ids", []),
                "ha_area_names": meta.get("ha_area_names", []),
            })
        try:
            sync_result = await coord.api.async_sync_zone_definitions(zone_defs)
            if not sync_result.get("ok", True):
                errors.append(f"sync-definitions returned: {sync_result}")
        except Exception as exc:
            errors.append(f"sync-definitions: {exc}")

        ok = len(errors) == 0
        connection.send_result(msg["id"], {
            "ok": ok,
            "synced": len(zone_ids),
            "zones": synced.get("zones", zone_ids),
            "created": synced.get("created", []),
            "errors": errors,
        })

    except Exception as e:
        _LOGGER.error("ws_sync_habitus_zones: %s", e)
        connection.send_error(msg["id"], "sync_failed", str(e))


@websocket_api.websocket_command({
    "type": "pilotsuite/habitus/match_zone",
    vol.Required("input_text"): str,
    vol.Optional("fuzzy_threshold", default=0.6): float,
})
@websocket_api.async_response
async def ws_match_habitus_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Match a zone template by name (exact → keyword → fuzzy).

    Returns null when no match is found.
    """
    if not HAS_ZONE_MATCHER:
        connection.send_error(
            msg["id"], "not_supported", "Zone matcher not available (copilot_core not installed)"
        )
        return

    try:
        input_text = str(msg["input_text"]).strip()
        fuzzy_threshold = float(msg.get("fuzzy_threshold", 0.6))

        matcher = create_zone_matcher()

        exact = (matcher.match_zone_by_name(input_text)
                 or matcher.match_zone_by_keyword(input_text))
        if exact:
            info = matcher.get_zone_info(exact)
            connection.send_result(msg["id"], {
                "matched_zone": {
                    "type": exact.value,
                    "name_de": info.name_de,
                    "name_en": info.name_en,
                    "confidence": 1.0,
                }
            })
            return

        fuzzy = matcher.fuzzy_match_zone(input_text, fuzzy_threshold)
        if fuzzy:
            zone_type, confidence = fuzzy
            info = matcher.get_zone_info(zone_type)
            connection.send_result(msg["id"], {
                "matched_zone": {
                    "type": zone_type.value,
                    "name_de": info.name_de,
                    "name_en": info.name_en,
                    "confidence": confidence,
                }
            })
            return

        connection.send_result(msg["id"], {"matched_zone": None})
    except Exception as e:
        _LOGGER.error("ws_match_habitus_zone: %s", e)
        connection.send_error(msg["id"], "match_failed", str(e))


@websocket_api.websocket_command({
    "type": "pilotsuite/habitus/get_suggestions",
    vol.Required("input_text"): str,
    vol.Optional("max_results", default=5): int,
})
@websocket_api.async_response
async def ws_get_habitus_zone_suggestions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Autocomplete-style zone suggestions for a partial text input."""
    if not HAS_ZONE_MATCHER:
        connection.send_error(
            msg["id"], "not_supported", "Zone matcher not available"
        )
        return

    try:
        input_text = str(msg["input_text"]).strip()
        max_results = max(1, min(int(msg.get("max_results", 5)), 20))

        suggestions = get_zone_suggestions(input_text, max_results)
        matcher = create_zone_matcher()
        result = []
        for zone_type, confidence in suggestions:
            info = matcher.get_zone_info(zone_type)
            result.append({
                "type": zone_type.value,
                "name_de": info.name_de,
                "name_en": info.name_en,
                "confidence": confidence,
            })

        connection.send_result(msg["id"], {"suggestions": result})
    except Exception as e:
        _LOGGER.error("ws_get_habitus_zone_suggestions: %s", e)
        connection.send_error(msg["id"], "suggestions_failed", str(e))


@websocket_api.websocket_command({
    "type": "pilotsuite/habitus/entities_in_zone",
    vol.Required("zone_type"): str,
})
@websocket_api.async_response
async def ws_get_entities_in_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return HA entity IDs associated with a zone_type template.

    Currently a stub: returns the canonical entity domains for the zone type.
    Full implementation (Core-backed) is tracked in:
    https://github.com/pilotsuite/pilotsuite/issues/483
    """
    entry_id = _entry_id_from_connection(hass, connection)
    if not entry_id:
        connection.send_error(msg["id"], "not_found", "PilotSuite not configured")
        return

    zone_type_str = str(msg["zone_type"]).strip().lower()
    try:
        ZoneType(zone_type_str)
    except ValueError:
        connection.send_error(
            msg["id"], "invalid_zone_type", f"Unknown zone type: {zone_type_str}"
        )
        return

    # Canonical entity domains per zone type (conservative fallback).
    CANONICAL_DOMAINS: dict[str, list[str]] = {
        "living": ["light", "binary_sensor", "sensor", "climate", "media_player"],
        "kitchen": ["light", "binary_sensor", "sensor", "climate"],
        "bedroom": ["light", "binary_sensor", "sensor", "climate", "media_player"],
        "bathroom": ["light", "binary_sensor", "sensor", "climate"],
        "office": ["light", "binary_sensor", "sensor", "climate", "media_player"],
        "corridor": ["light", "binary_sensor", "sensor"],
        "outdoor": ["light", "binary_sensor", "camera"],
        "garage": ["light", "binary_sensor", "cover", "sensor"],
    }

    domains = CANONICAL_DOMAINS.get(zone_type_str, ["light", "binary_sensor", "sensor"])
    ent_reg = er.async_get(hass)
    entities = [
        eid for eid, entry in ent_reg.entities.items()
        if entry.domain in domains and entry.disabled_by is None
    ]

    connection.send_result(msg["id"], {
        "zone_type": zone_type_str,
        "entities": sorted(entities),
        "domains": domains,
        "note": "stub — full Core-backed lookup is pending (#483)",
    })


def async_register_habitus_zone_api(hass: HomeAssistant) -> None:
    """Register all habitat-zone WebSocket commands on the HomeAssistant instance."""
    websocket_api.async_register_command(hass, ws_get_habitus_zones)
    websocket_api.async_register_command(hass, ws_sync_habitus_zones)
    websocket_api.async_register_command(hass, ws_match_habitus_zone)
    websocket_api.async_register_command(hass, ws_get_habitus_zone_suggestions)
    websocket_api.async_register_command(hass, ws_get_entities_in_zone)
    _LOGGER.info("Registered %d habitat-zone WS commands", 5)
