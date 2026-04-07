"""Module Buttons — Slices 67-82.

HA Buttons for all intelligence modules:
- Presence (Slices 67, 70, 75)
- Light (Slices 68, 71, 76)
- TimeOfDay (Slices 69, 72, 77)
- Rules (Slices 73, 78)
- Climate (Slice 80)
- Humidity (Slice 81)
- Energy (Slice 82)
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api import CopilotApiClient

_LOGGER = logging.getLogger(__name__)


# ── Light Buttons ─────────────────────────────────────────────────────

class ActivateLightSceneButton(CopilotBaseEntity, ButtonEntity):
    """Button to activate a light scene."""
    
    _attr_icon = "mdi:lightbulb-on"
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str, scene: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._scene = scene
        self._attr_unique_id = f"copilot_light_scene_{zone_id}_{scene}"
        self._attr_name = f"PilotSuite Light Scene {zone_name} {scene}"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "scene": scene,
        }
    
    async def async_press(self) -> None:
        """Activate the light scene."""
        try:
            await self._api.activate_light_scene(self._zone_id, self._scene)
            _LOGGER.info("Activated light scene %s in zone %s", self._scene, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to activate light scene: %s", e)


# ── Climate Buttons ───────────────────────────────────────────────────

class SetClimateSetpointButton(CopilotBaseEntity, ButtonEntity):
    """Button to set climate setpoint."""
    
    _attr_icon = "mdi:thermostat"
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str, temperature: float):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._temperature = temperature
        self._attr_unique_id = f"copilot_climate_setpoint_{zone_id}_{int(temperature*10)}"
        self._attr_name = f"PilotSuite Climate {zone_name} {temperature}°C"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "target_temperature": temperature,
        }
    
    async def async_press(self) -> None:
        """Set the climate setpoint."""
        try:
            await self._api.set_climate_setpoint(self._zone_id, self._temperature)
            _LOGGER.info("Set climate setpoint to %s°C in zone %s", self._temperature, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to set climate setpoint: %s", e)


# ── Rules Buttons ─────────────────────────────────────────────────────

class ActivateRuleButton(CopilotBaseEntity, ButtonEntity):
    """Button to activate a rule."""
    
    _attr_icon = "mdi:script-text-play"
    
    def __init__(self, api: CopilotApiClient, rule_id: str, rule_name: str):
        super().__init__(api)
        self._rule_id = rule_id
        self._rule_name = rule_name
        self._attr_unique_id = f"copilot_rule_activate_{rule_id}"
        self._attr_name = f"PilotSuite Activate Rule {rule_name}"
        self._attr_extra_state_attributes = {
            "rule_id": rule_id,
            "rule_name": rule_name,
        }
    
    async def async_press(self) -> None:
        """Activate the rule."""
        try:
            await self._api.activate_rule(self._rule_id)
            _LOGGER.info("Activated rule %s", self._rule_id)
        except Exception as e:
            _LOGGER.error("Failed to activate rule: %s", e)


# ── Module Control Buttons ────────────────────────────────────────────

class RefreshModuleStatusButton(CopilotBaseEntity, ButtonEntity):
    """Button to refresh module status."""
    
    _attr_icon = "mdi:refresh"
    
    def __init__(self, api: CopilotApiClient, module_name: str):
        super().__init__(api)
        self._module_name = module_name
        self._attr_unique_id = f"copilot_module_refresh_{module_name}"
        self._attr_name = f"PilotSuite Refresh {module_name}"
        self._attr_extra_state_attributes = {
            "module": module_name,
        }
    
    async def async_press(self) -> None:
        """Refresh module status."""
        try:
            # Trigger update via API
            await self._api.get_module_status(self._module_name)
            _LOGGER.info("Refreshed module status for %s", self._module_name)
        except Exception as e:
            _LOGGER.error("Failed to refresh module status: %s", e)


class ResetModuleConfigButton(CopilotBaseEntity, ButtonEntity):
    """Button to reset module config to defaults."""
    
    _attr_icon = "mdi:cog-refresh"
    
    def __init__(self, api: CopilotApiClient, module_name: str):
        super().__init__(api)
        self._module_name = module_name
        self._attr_unique_id = f"copilot_module_reset_{module_name}"
        self._attr_name = f"PilotSuite Reset {module_name} Config"
        self._attr_extra_state_attributes = {
            "module": module_name,
        }
    
    async def async_press(self) -> None:
        """Reset module config."""
        try:
            await self._api.execute_module_action(self._module_name, "reset_config")
            _LOGGER.info("Reset module config for %s", self._module_name)
        except Exception as e:
            _LOGGER.error("Failed to reset module config: %s", e)


# ── Presence Buttons ──────────────────────────────────────────────────

class OverridePresenceButton(CopilotBaseEntity, ButtonEntity):
    """Button to override presence state."""
    
    _attr_icon = "mdi:motion-sensor-off"
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str, state: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._state = state
        self._attr_unique_id = f"copilot_presence_override_{zone_id}_{state}"
        self._attr_name = f"PilotSuite Presence {zone_name} {state}"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "override_state": state,
        }
    
    async def async_press(self) -> None:
        """Override presence state."""
        try:
            await self._api.execute_module_action("presence", "override", {
                "zone_id": self._zone_id,
                "state": self._state,
            })
            _LOGGER.info("Overrode presence to %s in zone %s", self._state, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to override presence: %s", e)


# ── Factory Function ──────────────────────────────────────────────────

async def async_create_module_buttons(
    hass: HomeAssistant,
    api: CopilotApiClient,
    config_entry: ConfigEntry,
) -> list[ButtonEntity]:
    """Create all module buttons."""
    buttons = []
    
    # Get zones from Core
    try:
        zones_data = await api.get_presence_zones()
        zones = zones_data.get("zones", [])
    except Exception:
        zones = []
    
    # Create buttons for each zone
    for zone in zones:
        zone_id = zone.get("zone_id", "unknown")
        zone_name = zone.get("zone_name", zone_id)
        
        # Light scene buttons
        for scene in ["relax", "focus", "movie", "night", "morning"]:
            buttons.append(ActivateLightSceneButton(api, zone_id, zone_name, scene))
        
        # Climate setpoint buttons
        for temp in [18.0, 20.0, 22.0, 24.0]:
            buttons.append(SetClimateSetpointButton(api, zone_id, zone_name, temp))
        
        # Presence override buttons
        for state in ["present", "absent"]:
            buttons.append(OverridePresenceButton(api, zone_id, zone_name, state))
    
    # Module control buttons
    for module in ["presence", "light", "climate", "humidity", "energy", "timeofday", "rules"]:
        buttons.append(RefreshModuleStatusButton(api, module))
        buttons.append(ResetModuleConfigButton(api, module))
    
    # Rule activation buttons (fetch from API)
    try:
        rules_data = await api.get_rules_list()
        rules = rules_data.get("rules", [])
        for rule in rules:
            rule_id = rule.get("rule_id", "")
            rule_name = rule.get("name", rule_id)
            if rule_id:
                buttons.append(ActivateRuleButton(api, rule_id, rule_name))
    except Exception:
        pass
    
    return buttons
