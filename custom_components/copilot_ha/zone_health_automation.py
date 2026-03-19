"""Zone Health Automation — Auto-triggers based on health metrics (PS-142).

Automations:
- Auto-notify when health drops below threshold
- Auto-adjust climate when temp/humid out of range
- Auto-ventilate when CO2 high
- Auto-dim lights when bright + idle

Configured per zone via options flow.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.components import persistent_notification

import voluptuous as vol

from .zone_health import ZoneHealthMetrics, TEMP_COMFORT_MIN, TEMP_COMFORT_MAX, HUMIDITY_COMFORT_MIN, HUMIDITY_COMFORT_MAX, CO2_GOOD_MAX, CO2_MODERATE_MAX
from .zone_health_card import create_health_card_state
from .habitus_zones_store_v2 import async_get_zones_v2, async_update_zone_state

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


@dataclass
class ZoneHealthAutomationConfig:
    """Per-zone health automation config."""
    zone_id: str
    enabled: bool = True
    
    # Notifications
    notify_on_poor_health: bool = True
    poor_health_threshold: float = 50.0
    
    # Climate auto-adjust
    auto_climate: bool = True
    climate_temp_target: float = 21.0
    climate_humid_target: float = 50.0
    
    # Ventilation auto-trigger
    auto_ventilate_on_co2: bool = True
    co2_ventilate_threshold: float = 1000.0
    
    # Light auto-adjust
    auto_light_adjust: bool = False
    light_dim_when_idle: bool = True
    
    # Cooldowns (prevent spam)
    notification_cooldown_minutes: int = 30
    last_notification: datetime | None = None


async def async_evaluate_zone_health_automations(
    hass: HomeAssistant,
    entry_id: str,
    metrics: ZoneHealthMetrics,
    config: ZoneHealthAutomationConfig,
) -> dict[str, Any]:
    """Evaluate and trigger automations for a zone."""
    triggered: dict[str, Any] = {
        "zone_id": metrics.zone_id,
        "zone_name": metrics.zone_name,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "actions": [],
    }
    
    if not config.enabled:
        return triggered
    
    state = create_health_card_state(metrics)
    
    # 1. Poor health notification
    if config.notify_on_poor_health and metrics.health_score < config.poor_health_threshold:
        now = datetime.now(tz=timezone.utc)
        if config.last_notification is None or now > config.last_notification + timedelta(minutes=config.notification_cooldown_minutes):
            message = f"""⚠️ Zone Health Alert

{metrics.zone_name}: Health Score {metrics.health_score:.0f} (poor)

Temp: {state.temperature_status}
Humidity: {state.humidity_status}
Air Quality: {state.air_quality}

Recommended actions:
- Check ventilation
- Adjust climate settings
- Review entity status"""
            
            hass.components.persistent_notification.async_create(
                message=message,
                title=f"Zone Health: {metrics.zone_name}",
                notification_id=f"zone_health_{metrics.zone_id}",
            )
            
            triggered["actions"].append({
                "type": "notification",
                "notification_id": f"zone_health_{metrics.zone_id}",
                "message": "Poor health alert sent",
            })
            
            config.last_notification = now
    
    # 2. Auto-climate adjustment
    if config.auto_climate:
        climate_actions = []
        
        if metrics.temperature is not None:
            if metrics.temperature < config.climate_temp_target - 2:
                climate_actions.append("heat")
            elif metrics.temperature > config.climate_temp_target + 2:
                climate_actions.append("cool")
        
        if metrics.humidity is not None:
            if metrics.humidity < config.climate_humid_target - 10:
                climate_actions.append("humidify")
            elif metrics.humidity > config.climate_humid_target + 10:
                climate_actions.append("dehumidify")
        
        if climate_actions:
            triggered["actions"].append({
                "type": "climate_adjustment",
                "actions": climate_actions,
                "message": f"Climate adjustment triggered: {', '.join(climate_actions)}",
            })
    
    # 3. Auto-ventilation on high CO2
    if config.auto_ventilate_on_co2 and metrics.co2 is not None:
        if metrics.co2 > config.co2_ventilate_threshold:
            triggered["actions"].append({
                "type": "ventilation",
                "co2_level": metrics.co2,
                "message": f"Ventilation recommended - CO2: {metrics.co2:.0f} ppm",
            })
    
    # 4. Auto-light adjustment
    if config.auto_light_adjust:
        light_actions = []
        
        if config.light_dim_when_idle and state.light_status == "bright":
            light_actions.append("dim")
        
        if light_actions:
            triggered["actions"].append({
                "type": "light_adjustment",
                "actions": light_actions,
                "message": f"Light adjustment: {', '.join(light_actions)}",
            })
    
    return triggered


async def async_setup_zone_health_automations(hass: HomeAssistant, entry_id: str) -> None:
    """Set up zone health automations for a config entry."""
    zones = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.debug("No zones found for entry %s, skipping health automations", entry_id)
        return
    
    _LOGGER.info("Zone health automations set up for %d zones", len(zones))
    
    # Store automation configs in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][f"health_automations_{entry_id}"] = {
        "zones": {zone.zone_id: ZoneHealthAutomationConfig(zone_id=zone.zone_id) for zone in zones},
        "last_update": datetime.now(tz=timezone.utc),
    }


async def async_update_zone_health_automation(
    hass: HomeAssistant,
    entry_id: str,
    zone_id: str,
    new_config: dict[str, Any],
) -> ZoneHealthAutomationConfig:
    """Update automation config for a specific zone."""
    if DOMAIN not in hass.data or f"health_automations_{entry_id}" not in hass.data[DOMAIN]:
        raise ValueError(f"Health automations not initialized for entry {entry_id}")
    
    automations = hass.data[DOMAIN][f"health_automations_{entry_id}"]
    
    if zone_id not in automations["zones"]:
        raise ValueError(f"Zone {zone_id} not found")
    
    config = automations["zones"][zone_id]
    
    # Update config fields
    if "enabled" in new_config:
        config.enabled = bool(new_config["enabled"])
    if "notify_on_poor_health" in new_config:
        config.notify_on_poor_health = bool(new_config["notify_on_poor_health"])
    if "poor_health_threshold" in new_config:
        config.poor_health_threshold = float(new_config["poor_health_threshold"])
    if "auto_climate" in new_config:
        config.auto_climate = bool(new_config["auto_climate"])
    if "auto_ventilate_on_co2" in new_config:
        config.auto_ventilate_on_co2 = bool(new_config["auto_ventilate_on_co2"])
    if "co2_ventilate_threshold" in new_config:
        config.co2_ventilate_threshold = float(new_config["co2_ventilate_threshold"])
    if "auto_light_adjust" in new_config:
        config.auto_light_adjust = bool(new_config["auto_light_adjust"])
    if "notification_cooldown_minutes" in new_config:
        config.notification_cooldown_minutes = int(new_config["notification_cooldown_minutes"])
    
    automations["last_update"] = datetime.now(tz=timezone.utc)
    
    _LOGGER.info("Health automation config updated for zone %s", zone_id)
    
    return config
