"""Module Selects — Slices 67-82.

HA Select entities for module configuration:
- Light Scene Select
- Climate Mode Select
- TimeOfDay Mode Select
- Rules Mode Select
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api import CopilotApiClient

_LOGGER = logging.getLogger(__name__)


# ── Light Scene Select ────────────────────────────────────────────────

class LightSceneSelect(CopilotBaseEntity, SelectEntity):
    """Select entity for light scenes."""
    
    _attr_icon = "mdi:palette"
    _attr_options = ["relax", "focus", "movie", "night", "morning", "party", "reading"]
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_light_scene_select_{zone_id}"
        self._attr_name = f"PilotSuite Light Scene {zone_name}"
        self._attr_current_option = "relax"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
        }
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            await self._api.activate_light_scene(self._zone_id, option)
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Selected light scene %s for zone %s", option, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to select light scene: %s", e)
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            current_scene = zone_data.get("current_scene", "relax")
            if current_scene in self._attr_options:
                self._attr_current_option = current_scene
                self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest light data."""
        try:
            data = await self._api.get_light_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch light data: %s", e)


# ── Climate Mode Select ───────────────────────────────────────────────

class ClimateModeSelect(CopilotBaseEntity, SelectEntity):
    """Select entity for climate modes."""
    
    _attr_icon = "mdi:thermostat"
    _attr_options = ["heat", "cool", "auto", "eco", "comfort", "away"]
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_climate_mode_select_{zone_id}"
        self._attr_name = f"PilotSuite Climate Mode {zone_name}"
        self._attr_current_option = "comfort"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
        }
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            await self._api.execute_module_action("climate", "set_mode", {
                "zone_id": self._zone_id,
                "mode": option,
            })
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Selected climate mode %s for zone %s", option, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to select climate mode: %s", e)
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            mode = zone_data.get("hvac_mode", "comfort")
            if mode in self._attr_options:
                self._attr_current_option = mode
                self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest climate data."""
        try:
            data = await self._api.get_climate_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch climate data: %s", e)


# ── TimeOfDay Mode Select ─────────────────────────────────────────────

class TimeOfDayModeSelect(CopilotBaseEntity, SelectEntity):
    """Select entity for time of day modes."""
    
    _attr_icon = "mdi:clock-outline"
    _attr_options = ["morning", "day", "evening", "night", "late_night"]
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_timeofday_mode_select"
        self._attr_name = "PilotSuite Time of Day Mode"
        self._attr_current_option = "day"
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            await self._api.execute_module_action("timeofday", "set_mode", {
                "mode": option,
            })
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Selected time of day mode %s", option)
        except Exception as e:
            _LOGGER.error("Failed to select time of day mode: %s", e)
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        state = data.get("state", "day")
        if state in self._attr_options:
            self._attr_current_option = state
            self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest time of day data."""
        try:
            data = await self._api.get_timeofday_current()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch time of day data: %s", e)


# ── Rules Mode Select ─────────────────────────────────────────────────

class RulesModeSelect(CopilotBaseEntity, SelectEntity):
    """Select entity for rules mode."""
    
    _attr_icon = "mdi:script-text"
    _attr_options = ["active", "passive", "learning", "disabled"]
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_rules_mode_select"
        self._attr_name = "PilotSuite Rules Mode"
        self._attr_current_option = "active"
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            await self._api.execute_module_action("rules", "set_mode", {
                "mode": option,
            })
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Selected rules mode %s", option)
        except Exception as e:
            _LOGGER.error("Failed to select rules mode: %s", e)
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        mode = data.get("mode", "active")
        if mode in self._attr_options:
            self._attr_current_option = mode
            self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest rules data."""
        try:
            data = await self._api.get_rules_list()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch rules data: %s", e)


# ── Presence Mode Select ──────────────────────────────────────────────

class PresenceModeSelect(CopilotBaseEntity, SelectEntity):
    """Select entity for presence mode."""
    
    _attr_icon = "mdi:motion-sensor"
    _attr_options = ["auto", "forced_present", "forced_absent", "disabled"]
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_presence_mode_select_{zone_id}"
        self._attr_name = f"PilotSuite Presence Mode {zone_name}"
        self._attr_current_option = "auto"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
        }
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            await self._api.execute_module_action("presence", "set_mode", {
                "zone_id": self._zone_id,
                "mode": option,
            })
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Selected presence mode %s for zone %s", option, self._zone_id)
        except Exception as e:
            _LOGGER.error("Failed to select presence mode: %s", e)
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            mode = zone_data.get("mode", "auto")
            if mode in self._attr_options:
                self._attr_current_option = mode
                self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest presence data."""
        try:
            data = await self._api.get_presence_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch presence data: %s", e)


# ── Factory Function ──────────────────────────────────────────────────

async def async_create_module_selects(
    hass: HomeAssistant,
    api: CopilotApiClient,
    config_entry: ConfigEntry,
) -> list[SelectEntity]:
    """Create all module selects."""
    selects = []
    
    # Get zones from Core
    try:
        zones_data = await api.get_presence_zones()
        zones = zones_data.get("zones", [])
    except Exception:
        zones = []
    
    # Create selects for each zone
    for zone in zones:
        zone_id = zone.get("zone_id", "unknown")
        zone_name = zone.get("zone_name", zone_id)
        
        # Light scene select
        selects.append(LightSceneSelect(api, zone_id, zone_name))
        
        # Climate mode select
        selects.append(ClimateModeSelect(api, zone_id, zone_name))
        
        # Presence mode select
        selects.append(PresenceModeSelect(api, zone_id, zone_name))
    
    # Global selects
    selects.append(TimeOfDayModeSelect(api))
    selects.append(RulesModeSelect(api))
    
    return selects
