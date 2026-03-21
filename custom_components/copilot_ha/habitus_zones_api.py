"""API endpoints for habitat zones in the HA integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from homeassistant.helpers import entity_registry as er

from .habitus_zones_store_v2 import async_get_zones_v2
from .pilotsuite_dashboard_store import async_get_state, async_set_state

# Import the enhanced zone matcher from Core HA module
# NOTE: This module lives in Core (copilot_core.homeassistant.zone_matcher),
# not in HA. At runtime, Core's HA-Modul exposes this via the Python path.
try:
    from copilot_core.homeassistant.zone_matcher import (
        create_zone_matcher, get_zone_suggestions
    )
    from copilot_core.homeassistant.habitus_zones import ZoneType
    HAS_ZONE_MATCHER = True
except ImportError:
    HAS_ZONE_MATCHER = False
    logging.getLogger(__name__).warning(
        "Habitus zone matcher not available. Using basic zone matching."
    )

_LOGGER = logging.getLogger(__name__)


@websocket_api.websocket_command(
    {
        "type": "pilotsuite/habitus/zones",
    }
)
@websocket_api.async_response
async def ws_get_habitus_zones(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get all habitat zones."""
    try:
        zones = await async_get_zones_v2(hass, connection.context.user.id)
        connection.send_result(msg["id"], {"zones": zones})
    except Exception as e:
        _LOGGER.error("Error getting habitus zones: %s", e)
        connection.send_error(msg["id"], "get_failed", str(e))


@websocket_api.websocket_command(
    {
        "type": "pilotsuite/habitus/match_zone",
        "input_text": str,
        "fuzzy_threshold": float,
    }
)
@websocket_api.async_response
async def ws_match_habitus_zone(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Match a habitat zone by text input."""
    if not HAS_ZONE_MATCHER:
        connection.send_error(
            msg["id"], "not_supported", "Zone matcher not available"
        )
        return
    
    try:
        input_text = msg["input_text"]
        fuzzy_threshold = msg.get("fuzzy_threshold", 0.6)
        
        matcher = create_zone_matcher()
        
        # Try exact match first
        exact_match = matcher.match_zone_by_name(input_text) or matcher.match_zone_by_keyword(input_text)
        if exact_match:
            zone_info = matcher.get_zone_info(exact_match)
            connection.send_result(msg["id"], {
                "matched_zone": {
                    "type": exact_match.value,
                    "name_de": zone_info.name_de,
                    "name_en": zone_info.name_en,
                    "confidence": 1.0
                }
            })
            return
        
        # Try fuzzy match
        fuzzy_result = matcher.fuzzy_match_zone(input_text, fuzzy_threshold)
        if fuzzy_result:
            zone_type, confidence = fuzzy_result
            zone_info = matcher.get_zone_info(zone_type)
            connection.send_result(msg["id"], {
                "matched_zone": {
                    "type": zone_type.value,
                    "name_de": zone_info.name_de,
                    "name_en": zone_info.name_en,
                    "confidence": confidence
                }
            })
            return
        
        # No match found
        connection.send_result(msg["id"], {"matched_zone": None})
    except Exception as e:
        _LOGGER.error("Error matching habitus zone: %s", e)
        connection.send_error(msg["id"], "match_failed", str(e))


@websocket_api.websocket_command(
    {
        "type": "pilotsuite/habitus/get_suggestions",
        "input_text": str,
        "max_results": int,
    }
)
@websocket_api.async_response
async def ws_get_habitus_zone_suggestions(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get habitat zone suggestions for input text."""
    if not HAS_ZONE_MATCHER:
        connection.send_error(
            msg["id"], "not_supported", "Zone matcher not available"
        )
        return
    
    try:
        input_text = msg["input_text"]
        max_results = msg.get("max_results", 5)
        
        suggestions = get_zone_suggestions(input_text, max_results)
        
        # Convert to serializable format
        serialized_suggestions = []
        matcher = create_zone_matcher()
        
        for zone_type, confidence in suggestions:
            zone_info = matcher.get_zone_info(zone_type)
            serialized_suggestions.append({
                "type": zone_type.value,
                "name_de": zone_info.name_de,
                "name_en": zone_info.name_en,
                "confidence": confidence
            })
        
        connection.send_result(msg["id"], {"suggestions": serialized_suggestions})
    except Exception as e:
        _LOGGER.error("Error getting habitus zone suggestions: %s", e)
        connection.send_error(msg["id"], "suggestions_failed", str(e))


@websocket_api.websocket_command(
    {
        "type": "pilotsuite/habitus/entities_in_zone",
        "zone_type": str,
    }
)
@websocket_api.async_response
async def ws_get_entities_in_zone(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: Dict[str, Any]
) -> None:
    """Get entities associated with a specific habitat zone."""
    try:
        zone_type_str = msg["zone_type"]
        
        # Validate zone type
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError:
            connection.send_error(
                msg["id"], "invalid_zone_type", f"Invalid zone type: {zone_type_str}"
            )
            return
        
        # Get entity registry
        entity_registry = er.async_get(hass)
        
        # Get all entities and filter by zone association
        # This would typically come from a configuration or mapping
        # For now, we'll return a placeholder implementation
        entities_in_zone = []
        
        # In a real implementation, this would look up entities associated with the zone
        # based on configuration, naming conventions, or other mappings
        
        connection.send_result(msg["id"], {
            "zone_type": zone_type_str,
            "entities": entities_in_zone
        })
    except Exception as e:
        _LOGGER.error("Error getting entities in zone: %s", e)
        connection.send_error(msg["id"], "entities_failed", str(e))


def async_register_habitus_zone_api(hass: HomeAssistant) -> None:
    """Register habitat zone API endpoints."""
    websocket_api.async_register_command(hass, ws_get_habitus_zones)
    websocket_api.async_register_command(hass, ws_match_habitus_zone)
    websocket_api.async_register_command(hass, ws_get_habitus_zone_suggestions)
    websocket_api.async_register_command(hass, ws_get_entities_in_zone)