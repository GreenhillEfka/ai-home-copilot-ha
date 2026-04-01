"""Zone Automation Events — HA state_changed → CORE API (KEINE Logik!).

Architecture:
- Trackt HA state_changed Events
- Sendet Events an CORE API (via Client)
- KEINE Entscheidungs-Logik in HA!
- CORE entscheidet über Automation

Usage:
- Wird in __init__.py registriert
- Hört state_changed Events
- Sendet an CORE: POST /api/v1/zone-automation/zones/{zone_id}/event
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant, Event, EventStateChangedData
from homeassistant.helpers import entity_registry

from .zone_automation_client import ZoneAutomationClient

_LOGGER = logging.getLogger(__name__)


class ZoneAutomationEventHandler:
    """Event Handler für Zone Automation (NUR Event-Forwarding!)."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client: ZoneAutomationClient,
        zone_entity_map: Dict[str, str],  # entity_id → zone_id
    ):
        self._hass = hass
        self._client = client
        self._zone_entity_map = zone_entity_map
        self._remove_listener = None
        self._event_count = 0
    
    def start(self) -> None:
        """Event Listener starten."""
        self._remove_listener = self._hass.bus.async_listen(
            "state_changed",
            self._handle_state_change,
        )
        _LOGGER.info("Zone Automation Event Handler started")
    
    def stop(self) -> None:
        """Event Listener stoppen."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None
        _LOGGER.info("Zone Automation Event Handler stopped")
    
    def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        """state_changed Event verarbeiten (NUR Forwarding an CORE!)."""
        entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        
        # Skip if no new state
        if not new_state:
            return
        
        # Get zone for entity
        zone_id = self._get_zone_for_entity(entity_id)
        if not zone_id:
            return  # Entity not in any zone
        
        # Build context (NUR Daten sammeln, KEINE Logik!)
        context = self._build_context(entity_id, new_state, old_state)
        
        # Send to CORE (async, fire-and-forget)
        self._hass.async_create_task(
            self._send_event_to_core(zone_id, "state_changed", context)
        )
    
    def _get_zone_for_entity(self, entity_id: str) -> Optional[str]:
        """Zone für Entity holen (aus Map)."""
        return self._zone_entity_map.get(entity_id)
    
    def _build_context(
        self,
        entity_id: str,
        new_state,
        old_state,
    ) -> Dict[str, Any]:
        """Context bauen (NUR Daten sammeln!)."""
        context = {
            "entity_id": entity_id,
            "new_state": new_state.state if new_state else None,
            "old_state": old_state.state if old_state else None,
            "attributes": dict(new_state.attributes) if new_state else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Add common attributes
        if new_state:
            attrs = new_state.attributes
            if "brightness" in attrs:
                context["brightness"] = attrs["brightness"] / 255.0  # Normalize 0-1
            if "temperature" in attrs:
                context["temperature"] = attrs["temperature"]
            if "humidity" in attrs:
                context["humidity"] = attrs["humidity"]
            if "motion" in attrs or "occupancy" in attrs:
                context["presence"] = attrs.get("motion", False) or attrs.get("occupancy", False)
        
        return context
    
    async def _send_event_to_core(
        self,
        zone_id: str,
        event_type: str,
        context: Dict[str, Any],
    ) -> None:
        """Event an CORE senden (NUR HTTP-Call!)."""
        try:
            result = await self._client.send_event(zone_id, event_type, context)
            
            if "error" in result:
                _LOGGER.debug(f"Event sent to CORE: {zone_id} — {result.get('error', 'OK')}")
            else:
                self._event_count += 1
                _LOGGER.debug(
                    f"Event processed: {zone_id} — "
                    f"triggered={result.get('triggered_rules', 0)}, "
                    f"learned={result.get('learned', 0)}"
                )
        except Exception as e:
            _LOGGER.error(f"Event send failed: {e}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "event_count": self._event_count,
            "zones_tracked": len(set(self._zone_entity_map.values())),
            "entities_tracked": len(self._zone_entity_map),
        }


# =============================================================================
# SETUP HELPER
# =============================================================================

async def setup_zone_automation_events(
    hass: HomeAssistant,
    client: ZoneAutomationClient,
) -> ZoneAutomationEventHandler:
    """Zone Automation Events setupen."""
    # Build entity → zone map (from HA area registry)
    zone_entity_map = await _build_zone_entity_map(hass)
    
    # Create handler
    handler = ZoneAutomationEventHandler(hass, client, zone_entity_map)
    handler.start()
    
    _LOGGER.info(
        f"Zone Automation Events setup: "
        f"{len(zone_entity_map)} entities in {len(set(zone_entity_map.values()))} zones"
    )
    
    return handler


async def _build_zone_entity_map(hass: HomeAssistant) -> Dict[str, str]:
    """Entity → Zone Map bauen (aus HA Area Registry)."""
    zone_entity_map = {}
    
    # Get entity registry
    ent_reg = entity_registry.async_get(hass)
    
    # Get all entities
    for entry in ent_reg.entities.values():
        entity_id = entry.entity_id
        area_id = entry.area_id
        
        if area_id:
            # Map area_id to zone_id (simplified: area_id = zone_id)
            # In production: Use proper area→zone mapping
            zone_id = area_id
            zone_entity_map[entity_id] = zone_id
    
    return zone_entity_map
