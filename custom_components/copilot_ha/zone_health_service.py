"""Zone Health Service — Service endpoints for health updates (PS-140).

Provides Home Assistant services:
- copilot_ha.update_zone_health: Manual health metrics refresh
- copilot_ha.notify_zone_health: Send notification when health is poor
- copilot_ha.get_zone_health_status: Get current health status

Called from automations or manual triggers.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.helpers import config_validation as cv, entity_platform

import voluptuous as vol

from .zone_health import async_update_all_zone_health, ZoneHealthMetrics
from .zone_health_card import async_render_all_zone_health_cards, create_health_card_state
from .habitus_zones_store_v2 import async_get_zones_v2

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"

# Service schemas
SERVICE_UPDATE_HEALTH = "update_zone_health"
SERVICE_NOTIFY_HEALTH = "notify_zone_health"
SERVICE_GET_HEALTH_STATUS = "get_zone_health_status"

SERVICE_UPDATE_HEALTH_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("zone_id"): cv.string,
})

SERVICE_NOTIFY_HEALTH_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("zone_id"): cv.string,
    vol.Optional("threshold"): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
})

SERVICE_GET_HEALTH_STATUS_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("zone_id"): cv.string,
})


async def async_setup_zone_health_services(hass: HomeAssistant) -> None:
    """Set up zone health services."""
    
    async def handle_update_health(call: ServiceCall) -> ServiceResponse:
        """Handle zone health update service."""
        entry_id = call.data.get("entry_id")
        zone_id = call.data.get("zone_id")
        
        if not entry_id:
            # Get first config entry
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"success": False, "error": "No config entries found"}
            entry_id = entries[0].entry_id
        
        zones = await async_get_zones_v2(hass, entry_id)
        if not zones:
            return {"success": False, "error": "No zones found"}
        
        health_map = await async_update_all_zone_health(hass, zones)
        
        if zone_id:
            # Single zone
            if zone_id not in health_map:
                return {"success": False, "error": f"Zone {zone_id} not found"}
            metrics = health_map[zone_id]
            return {
                "success": True,
                "zone_id": zone_id,
                "health_score": metrics.health_score,
                "temperature": metrics.temperature,
                "humidity": metrics.humidity,
                "co2": metrics.co2,
                "air_quality": metrics.air_quality,
            }
        
        # All zones
        return {
            "success": True,
            "zones": [
                {
                    "zone_id": m.zone_id,
                    "zone_name": m.zone_name,
                    "health_score": m.health_score,
                    "temperature": m.temperature,
                    "humidity": m.humidity,
                    "co2": m.co2,
                    "air_quality": m.air_quality,
                }
                for m in health_map.values()
            ]
        }
    
    async def handle_notify_health(call: ServiceCall) -> ServiceResponse:
        """Handle zone health notification service."""
        entry_id = call.data.get("entry_id")
        zone_id = call.data.get("zone_id")
        threshold = call.data.get("threshold", 50.0)
        
        if not entry_id:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"success": False, "error": "No config entries found"}
            entry_id = entries[0].entry_id
        
        zones = await async_get_zones_v2(hass, entry_id)
        if not zones:
            return {"success": False, "error": "No zones found"}
        
        health_map = await async_update_all_zone_health(hass, zones)
        
        notifications_sent = 0
        for metrics in health_map.values():
            if zone_id and metrics.zone_id != zone_id:
                continue
            
            if metrics.health_score < threshold:
                state = create_health_card_state(metrics)
                message = f"""⚠️ Zone Health Alert

{metrics.zone_name}: Health Score {metrics.health_score:.0f}

Temp: {state.temperature_status}
Humidity: {state.humidity_status}
Air Quality: {state.air_quality}

Please check zone conditions."""
                
                # Send persistent notification
                hass.components.persistent_notification.async_create(
                    message=message,
                    title=f"Zone Health: {metrics.zone_name}",
                    notification_id=f"zone_health_{metrics.zone_id}",
                )
                notifications_sent += 1
        
        return {
            "success": True,
            "notifications_sent": notifications_sent,
            "threshold": threshold,
        }
    
    async def handle_get_health_status(call: ServiceCall) -> ServiceResponse:
        """Handle zone health status service."""
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
        
        health_map = await async_update_all_zone_health(hass, zones)
        
        if zone_id:
            if zone_id not in health_map:
                return {"success": False, "error": f"Zone {zone_id} not found"}
            metrics = health_map[zone_id]
            state = create_health_card_state(metrics)
            return {
                "success": True,
                "zone_id": zone_id,
                "zone_name": metrics.zone_name,
                "health_score": metrics.health_score,
                "score_category": state.score_category,
                "temperature": metrics.temperature,
                "temperature_status": state.temperature_status,
                "humidity": metrics.humidity,
                "humidity_status": state.humidity_status,
                "co2": metrics.co2,
                "air_quality": metrics.air_quality,
                "light": metrics.lux,
                "light_status": state.light_status,
                "last_updated": metrics.last_updated.isoformat(),
            }
        
        # All zones
        return {
            "success": True,
            "zones": [
                {
                    "zone_id": m.zone_id,
                    "zone_name": m.zone_name,
                    "health_score": m.health_score,
                    "score_category": create_health_card_state(m).score_category,
                    "temperature": m.temperature,
                    "humidity": m.humidity,
                    "co2": m.co2,
                    "air_quality": m.air_quality,
                }
                for m in health_map.values()
            ]
        }
    
    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_HEALTH, handle_update_health,
        schema=SERVICE_UPDATE_HEALTH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_NOTIFY_HEALTH, handle_notify_health,
        schema=SERVICE_NOTIFY_HEALTH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_HEALTH_STATUS, handle_get_health_status,
        schema=SERVICE_GET_HEALTH_STATUS_SCHEMA,
    )
    
    _LOGGER.info("Zone health services registered")
