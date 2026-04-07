"""Module Sensors — Slices 67-82.

HA Sensors for all intelligence modules:
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
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api import CopilotApiClient

_LOGGER = logging.getLogger(__name__)


# ── Presence Sensors ──────────────────────────────────────────────────

class PresenceZoneSensor(CopilotBaseEntity, SensorEntity):
    """Presence status for a zone."""
    
    _attr_icon = "mdi:motion-sensor"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["present", "absent", "uncertain", "extended_absent"]
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_presence_{zone_id}"
        self._attr_name = f"PilotSuite Presence {zone_name}"
        self._attr_native_value = "absent"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "confidence": 0.0,
            "active_sensors": [],
            "present_since": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            self._attr_native_value = zone_data.get("state", "absent")
            self._attr_extra_state_attributes.update({
                "confidence": zone_data.get("confidence", 0.0),
                "active_sensors": zone_data.get("active_sensors", []),
                "present_since": zone_data.get("present_since"),
                "absent_since": zone_data.get("absent_since"),
            })
            self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        # Initial fetch
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest presence data."""
        try:
            data = await self._api.get_presence_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch presence data: %s", e)


class PresenceCountSensor(CopilotBaseEntity, SensorEntity):
    """Total count of occupied zones."""
    
    _attr_icon = "mdi:account-multiple"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "zones"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_presence_count"
        self._attr_name = "PilotSuite Presence Count"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "total_zones": 0,
            "occupied_zones": [],
            "vacant_zones": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        occupied = [z for z in zones if z.get("state") == "present"]
        
        self._attr_native_value = len(occupied)
        self._attr_extra_state_attributes.update({
            "total_zones": len(zones),
            "occupied_zones": [z.get("zone_id") for z in occupied],
            "vacant_zones": [z.get("zone_id") for z in zones if z not in occupied],
        })
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
            _LOGGER.debug("Failed to fetch presence count: %s", e)


# ── Light Sensors ─────────────────────────────────────────────────────

class LightZoneSensor(CopilotBaseEntity, SensorEntity):
    """Light status for a zone."""
    
    _attr_icon = "mdi:lightbulb"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["on", "off", "dimmed", "scene"]
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_light_{zone_id}"
        self._attr_name = f"PilotSuite Light {zone_name}"
        self._attr_native_value = "off"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "current_scene": None,
            "brightness": 0,
            "color_temp": 0,
            "active_lights": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            self._attr_native_value = zone_data.get("state", "off")
            self._attr_extra_state_attributes.update({
                "current_scene": zone_data.get("current_scene"),
                "brightness": zone_data.get("brightness", 0),
                "color_temp": zone_data.get("color_temp", 0),
                "active_lights": zone_data.get("active_lights", []),
            })
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


# ── Climate Sensors ───────────────────────────────────────────────────

class ClimateZoneSensor(CopilotBaseEntity, SensorEntity):
    """Climate status for a zone."""
    
    _attr_icon = "mdi:thermostat"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_climate_{zone_id}"
        self._attr_name = f"PilotSuite Climate {zone_name}"
        self._attr_native_value = 20.0
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "target_temp": 20.0,
            "current_temp": 20.0,
            "hvac_mode": "heat",
            "hvac_action": "idle",
            "eco_mode": False,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            self._attr_native_value = zone_data.get("current_temp", 20.0)
            self._attr_extra_state_attributes.update({
                "target_temp": zone_data.get("target_temp", 20.0),
                "hvac_mode": zone_data.get("hvac_mode", "heat"),
                "hvac_action": zone_data.get("hvac_action", "idle"),
                "eco_mode": zone_data.get("eco_mode", False),
            })
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


# ── Humidity Sensors ──────────────────────────────────────────────────

class HumidityZoneSensor(CopilotBaseEntity, SensorEntity):
    """Humidity status for a zone."""
    
    _attr_icon = "mdi:water-percent"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: CopilotApiClient, zone_id: str, zone_name: str):
        super().__init__(api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_humidity_{zone_id}"
        self._attr_name = f"PilotSuite Humidity {zone_name}"
        self._attr_native_value = 50.0
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "target_humidity": 50.0,
            "ventilation_active": False,
            "mold_risk": "low",
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            self._attr_native_value = zone_data.get("humidity", 50.0)
            self._attr_extra_state_attributes.update({
                "target_humidity": zone_data.get("target_humidity", 50.0),
                "ventilation_active": zone_data.get("ventilation_active", False),
                "mold_risk": zone_data.get("mold_risk", "low"),
            })
            self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest humidity data."""
        try:
            data = await self._api.get_humidity_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch humidity data: %s", e)


# ── Energy Sensors ────────────────────────────────────────────────────

class EnergyForecastSensor(CopilotBaseEntity, SensorEntity):
    """Energy forecast sensor."""
    
    _attr_icon = "mdi:lightning-bolt"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_energy_forecast"
        self._attr_name = "PilotSuite Energy Forecast"
        self._attr_native_value = 0.0
        self._attr_extra_state_attributes = {
            "forecast_24h": 0.0,
            "forecast_7d": 0.0,
            "current_price": 0.0,
            "optimization_potential": 0.0,
            "recommendations": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        forecast = data.get("forecast", {})
        
        self._attr_native_value = forecast.get("current_consumption", 0.0)
        self._attr_extra_state_attributes.update({
            "forecast_24h": forecast.get("forecast_24h", 0.0),
            "forecast_7d": forecast.get("forecast_7d", 0.0),
            "current_price": forecast.get("current_price", 0.0),
            "optimization_potential": forecast.get("optimization_potential", 0.0),
            "recommendations": forecast.get("recommendations", []),
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest energy forecast."""
        try:
            data = await self._api.get_energy_forecast()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch energy forecast: %s", e)


# ── TimeOfDay Sensors ─────────────────────────────────────────────────

class TimeOfDaySensor(CopilotBaseEntity, SensorEntity):
    """Current time of day state."""
    
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["morning", "day", "evening", "night", "late_night"]
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_timeofday"
        self._attr_name = "PilotSuite Time of Day"
        self._attr_native_value = "day"
        self._attr_extra_state_attributes = {
            "current_hour": 0,
            "sunrise": None,
            "sunset": None,
            "next_transition": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        self._attr_native_value = data.get("state", "day")
        self._attr_extra_state_attributes.update({
            "current_hour": data.get("current_hour", 0),
            "sunrise": data.get("sunrise"),
            "sunset": data.get("sunset"),
            "next_transition": data.get("next_transition"),
        })
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


# ── Rules Sensors ─────────────────────────────────────────────────────

class RulesActiveSensor(CopilotBaseEntity, SensorEntity):
    """Count of active rules."""
    
    _attr_icon = "mdi:script-text"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "rules"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: CopilotApiClient):
        super().__init__(api)
        self._attr_unique_id = "copilot_rules_active"
        self._attr_name = "PilotSuite Active Rules"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "total_rules": 0,
            "active_rules": [],
            "inactive_rules": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle module update."""
        rules = data.get("rules", [])
        active = [r for r in rules if r.get("active", False)]
        
        self._attr_native_value = len(active)
        self._attr_extra_state_attributes.update({
            "total_rules": len(rules),
            "active_rules": [r.get("rule_id") for r in active],
            "inactive_rules": [r.get("rule_id") for r in rules if not r.get("active")],
        })
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


# ── Factory Function ──────────────────────────────────────────────────

async def async_create_module_sensors(
    hass: HomeAssistant,
    api: CopilotApiClient,
    config_entry: ConfigEntry,
) -> list[SensorEntity]:
    """Create all module sensors."""
    sensors = []
    
    # Get zones from Core
    try:
        zones_data = await api.get_presence_zones()
        zones = zones_data.get("zones", [])
    except Exception:
        zones = []
    
    # Create sensors for each zone
    for zone in zones:
        zone_id = zone.get("zone_id", "unknown")
        zone_name = zone.get("zone_name", zone_id)
        
        # Presence
        sensors.append(PresenceZoneSensor(api, zone_id, zone_name))
        
        # Light
        sensors.append(LightZoneSensor(api, zone_id, zone_name))
        
        # Climate
        sensors.append(ClimateZoneSensor(api, zone_id, zone_name))
        
        # Humidity
        sensors.append(HumidityZoneSensor(api, zone_id, zone_name))
    
    # Global sensors
    sensors.append(PresenceCountSensor(api))
    sensors.append(EnergyForecastSensor(api))
    sensors.append(TimeOfDaySensor(api))
    sensors.append(RulesActiveSensor(api))
    
    return sensors
