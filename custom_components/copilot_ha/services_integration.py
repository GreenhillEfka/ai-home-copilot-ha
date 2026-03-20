"""Services Integration — Wire all services into HA service registry (PS-152).

Integrates:
- Zone health services
- Presence tracking services
- Module registry services
- Contract validation services
- Automation trigger services

Single entry point for all PilotSuite services.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.helpers import config_validation as cv

import voluptuous as vol

from .zone_health_service import async_setup_zone_health_services
from .presence_module import async_setup_presence_tracking
from .module_health_registry import async_setup_health_module_registry
from .zone_health_automation import async_evaluate_zone_health_automations
from .habitus_zones_store_v2 import async_get_zones_v2
from .zone_health import async_update_all_zone_health
from .presence_module import async_aggregate_all_zone_presence
from .presence_health_correlation import async_correlate_all_zones, async_get_presence_health_insights

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"

# Unified service schemas
SERVICE_PILOTSUITE_STATUS = "pilotsuite_status"
SERVICE_PILOTSUITE_REFRESH = "pilotsuite_refresh"
SERVICE_PILOTSUITE_INSIGHTS = "pilotsuite_insights"

SERVICE_STATUS_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("include_health"): cv.boolean,
    vol.Optional("include_presence"): cv.boolean,
    vol.Optional("include_correlations"): cv.boolean,
})

SERVICE_REFRESH_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("zones"): cv.ensure_list,
    vol.Optional("health"): cv.boolean,
    vol.Optional("presence"): cv.boolean,
})

SERVICE_INSIGHTS_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("zone_id"): cv.string,
})


async def async_setup_pilotsuite_services(hass: HomeAssistant) -> None:
    """Set up all PilotSuite services."""
    
    # Set up health services
    await async_setup_zone_health_services(hass)
    
    async def handle_pilotsuite_status(call: ServiceCall) -> ServiceResponse:
        """Handle unified status service."""
        entry_id = call.data.get("entry_id")
        include_health = call.data.get("include_health", True)
        include_presence = call.data.get("include_presence", True)
        include_correlations = call.data.get("include_correlations", True)
        
        if not entry_id:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"success": False, "error": "No config entries found"}
            entry_id = entries[0].entry_id
        
        zones = await async_get_zones_v2(hass, entry_id)
        if not zones:
            return {"success": False, "error": "No zones found"}
        
        status = {
            "success": True,
            "entry_id": entry_id,
            "zone_count": len(zones),
            "zones": [
                {
                    "zone_id": z.zone_id,
                    "zone_name": z.name,
                    "entity_count": len(z.entity_ids) if hasattr(z, "entity_ids") else 0,
                }
                for z in zones
            ],
        }
        
        if include_health:
            health_map = await async_update_all_zone_health(hass, zones)
            status["health"] = {
                zone_id: {
                    "health_score": m.health_score,
                    "temperature": m.temperature,
                    "humidity": m.humidity,
                    "co2": m.co2,
                    "air_quality": m.air_quality,
                }
                for zone_id, m in health_map.items()
            }
        
        if include_presence:
            presence_map = await async_aggregate_all_zone_presence(hass, entry_id, zones)
            status["presence"] = {
                zone_id: {
                    "is_present": p.is_present,
                    "confidence": p.confidence,
                    "source_count": p.source_count,
                    "active_sources": p.active_sources,
                }
                for zone_id, p in presence_map.items()
            }
        
        if include_correlations and include_health and include_presence:
            correlations = await async_correlate_all_zones(hass, entry_id, presence_map, health_map)
            insights = await async_get_presence_health_insights(hass, entry_id, correlations)
            status["insights"] = insights
        
        return status
    
    async def handle_pilotsuite_refresh(call: ServiceCall) -> ServiceResponse:
        """Handle unified refresh service."""
        entry_id = call.data.get("entry_id")
        zone_ids = call.data.get("zones")
        refresh_health = call.data.get("health", True)
        refresh_presence = call.data.get("presence", True)
        
        if not entry_id:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"success": False, "error": "No config entries found"}
            entry_id = entries[0].entry_id
        
        zones = await async_get_zones_v2(hass, entry_id)
        if not zones:
            return {"success": False, "error": "No zones found"}
        
        if zone_ids:
            zones = [z for z in zones if z.zone_id in zone_ids]
        
        refreshed = {
            "success": True,
            "entry_id": entry_id,
            "zones_refreshed": len(zones),
        }
        
        if refresh_health:
            health_map = await async_update_all_zone_health(hass, zones)
            refreshed["health_refreshed"] = len(health_map)
        
        if refresh_presence:
            presence_map = await async_aggregate_all_zone_presence(hass, entry_id, zones)
            refreshed["presence_refreshed"] = len(presence_map)
        
        return refreshed
    
    async def handle_pilotsuite_insights(call: ServiceCall) -> ServiceResponse:
        """Handle insights service."""
        entry_id = call.data.get("entry_id")
        zone_id = call.data.get("zone_id")
        
        if not entry_id:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"success": False, "error": "No config entries found"}
            entry_id = entries[0].entry_id
        
        zones = await async_get_zones_v2(hass, entry_id)
        if not zones:
            return {"success": False, "error": "No zones found"}
        
        if zone_id:
            zones = [z for z in zones if z.zone_id == zone_id]
        
        health_map = await async_update_all_zone_health(hass, zones)
        presence_map = await async_aggregate_all_zone_presence(hass, entry_id, zones)
        correlations = await async_correlate_all_zones(hass, entry_id, presence_map, health_map)
        insights = await async_get_presence_health_insights(hass, entry_id, correlations)
        
        return insights
    
    # Register unified services
    hass.services.async_register(
        DOMAIN, SERVICE_PILOTSUITE_STATUS, handle_pilotsuite_status,
        schema=SERVICE_STATUS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PILOTSUITE_REFRESH, handle_pilotsuite_refresh,
        schema=SERVICE_REFRESH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PILOTSUITE_INSIGHTS, handle_pilotsuite_insights,
        schema=SERVICE_INSIGHTS_SCHEMA,
    )
    
    _LOGGER.info("PilotSuite unified services registered")


async def async_validate_all_contracts(hass: HomeAssistant) -> ServiceResponse:
    """Validate all contracts and return result."""
    from pathlib import Path
    from . import contract_validation

    workspace = Path("/config/clawd")
    result = await contract_validation.async_validate_contracts(workspace)

    return {
        "success": result["success"],
        "core_openapi": result["core_openapi"],
        "ha_openapi": result["ha_openapi"],
        "drift_check": result["drift_check"],
        "runtime": result["runtime"],
    }
