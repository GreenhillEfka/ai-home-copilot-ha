"""Zone Health Options Flow — Per-zone health config in options flow (PS-145).

Adds health configuration options to each zone:
- Enable/disable health tracking
- Notification thresholds
- Auto-climate settings
- Auto-ventilation triggers
- Auto-light adjustment
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .config_options_flow import OptionsFlowHandler
from .zone_health_automation import ZoneHealthAutomationConfig

_LOGGER = logging.getLogger(__name__)

# Health options schema
STEP_HEALTH_CONFIG = vol.Schema({
    vol.Optional("health_enabled", default=True): bool,
    vol.Optional("health_notify_on_poor", default=True): bool,
    vol.Optional("health_poor_threshold", default=50.0): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
    vol.Optional("health_auto_climate", default=True): bool,
    vol.Optional("health_climate_temp_target", default=21.0): vol.All(vol.Coerce(float), vol.Range(min=10, max=35)),
    vol.Optional("health_climate_humid_target", default=50.0): vol.All(vol.Coerce(float), vol.Range(min=10, max=90)),
    vol.Optional("health_auto_ventilate", default=True): bool,
    vol.Optional("health_co2_ventilate_threshold", default=1000.0): vol.All(vol.Coerce(float), vol.Range(min=400, max=5000)),
    vol.Optional("health_auto_light", default=False): bool,
    vol.Optional("health_light_dim_idle", default=True): bool,
    vol.Optional("health_notification_cooldown_min", default=30): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
})


async def async_step_health_config(
    self: OptionsFlowHandler,
    user_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Handle health configuration step."""
    from homeassistant.data_entry_flow import FlowResultType
    
    if user_input is not None:
        # Merge health config into options
        current_options = dict(self._resolve_config_entry().options)
        current_options.update({
            "health_enabled": user_input.get("health_enabled", True),
            "health_notify_on_poor": user_input.get("health_notify_on_poor", True),
            "health_poor_threshold": user_input.get("health_poor_threshold", 50.0),
            "health_auto_climate": user_input.get("health_auto_climate", True),
            "health_climate_temp_target": user_input.get("health_climate_temp_target", 21.0),
            "health_climate_humid_target": user_input.get("health_climate_humid_target", 50.0),
            "health_auto_ventilate": user_input.get("health_auto_ventilate", True),
            "health_co2_ventilate_threshold": user_input.get("health_co2_ventilate_threshold", 1000.0),
            "health_auto_light": user_input.get("health_auto_light", False),
            "health_light_dim_idle": user_input.get("health_light_dim_idle", True),
            "health_notification_cooldown_min": user_input.get("health_notification_cooldown_min", 30),
        })
        
        self.hass.config_entries.async_update_entry(
            self._resolve_config_entry(),
            options=current_options,
        )
        
        return self.async_create_entry(title="", data={})
    
    # Get current health config
    entry = self._resolve_config_entry()
    current_options = entry.options
    
    # Pre-fill form with current values
    defaults = {
        "health_enabled": current_options.get("health_enabled", True),
        "health_notify_on_poor": current_options.get("health_notify_on_poor", True),
        "health_poor_threshold": current_options.get("health_poor_threshold", 50.0),
        "health_auto_climate": current_options.get("health_auto_climate", True),
        "health_climate_temp_target": current_options.get("health_climate_temp_target", 21.0),
        "health_climate_humid_target": current_options.get("health_climate_humid_target", 50.0),
        "health_auto_ventilate": current_options.get("health_auto_ventilate", True),
        "health_co2_ventilate_threshold": current_options.get("health_co2_ventilate_threshold", 1000.0),
        "health_auto_light": current_options.get("health_auto_light", False),
        "health_light_dim_idle": current_options.get("health_light_dim_idle", True),
        "health_notification_cooldown_min": current_options.get("health_notification_cooldown_min", 30),
    }
    
    return self.async_show_form(
        step_id="health_config",
        data_schema=vol.Schema({
            vol.Optional("health_enabled", default=defaults["health_enabled"]): bool,
            vol.Optional("health_notify_on_poor", default=defaults["health_notify_on_poor"]): bool,
            vol.Optional("health_poor_threshold", default=defaults["health_poor_threshold"]): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            vol.Optional("health_auto_climate", default=defaults["health_auto_climate"]): bool,
            vol.Optional("health_climate_temp_target", default=defaults["health_climate_temp_target"]): vol.All(vol.Coerce(float), vol.Range(min=10, max=35)),
            vol.Optional("health_climate_humid_target", default=defaults["health_climate_humid_target"]): vol.All(vol.Coerce(float), vol.Range(min=10, max=90)),
            vol.Optional("health_auto_ventilate", default=defaults["health_auto_ventilate"]): bool,
            vol.Optional("health_co2_ventilate_threshold", default=defaults["health_co2_ventilate_threshold"]): vol.All(vol.Coerce(float), vol.Range(min=400, max=5000)),
            vol.Optional("health_auto_light", default=defaults["health_auto_light"]): bool,
            vol.Optional("health_light_dim_idle", default=defaults["health_light_dim_idle"]): bool,
            vol.Optional("health_notification_cooldown_min", default=defaults["health_notification_cooldown_min"]): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
        }),
        description_placeholders={
            "hint": "Configure per-zone health tracking and automations",
        },
    )


async def async_step_zone_health_select(
    self: OptionsFlowHandler,
    user_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Handle zone selection for health config."""
    from homeassistant.data_entry_flow import FlowResultType
    from .habitus_zones_store_v2 import async_get_zones_v2
    
    if user_input is not None:
        # Store selected zone for next step
        self._health_zone_id = user_input.get("zone_id")
        return await self.async_step_health_config()
    
    # Get zones
    entry = self._resolve_config_entry()
    zones = await async_get_zones_v2(self.hass, entry.entry_id)
    
    if not zones:
        return self.async_show_menu(
            step_id="zone_health_select",
            menu_options=["back"],
            description_placeholders={"hint": "No zones configured"},
        )
    
    # Build zone selector
    zone_options = [
        {"value": z.zone_id, "label": z.name}
        for z in zones
    ]
    
    return self.async_show_form(
        step_id="zone_health_select",
        data_schema=vol.Schema({
            vol.Required("zone_id"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=zone_options,
                    mode="dropdown",
                )
            ),
        }),
        description_placeholders={
            "hint": f"Select zone to configure health tracking ({len(zones)} zones)",
        },
    )


async def async_setup_health_options_menu(
    self: OptionsFlowHandler,
) -> dict[str, Any]:
    """Add health config to options menu."""
    from homeassistant.data_entry_flow import FlowResultType
    
    return self.async_show_menu(
        step_id="init",
        menu_options=[
            "connection",
            "modules",
            "llm_provider",
            "knowledge_graph",
            "autonomy",
            "zone_health",  # New health menu option
            "ml_anomaly",
            "automation_modes",
            "habitus_zones",
            "entity_tags",
            "neurons",
            "backup_restore",
        ],
    )
