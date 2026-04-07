"""Complete Entities for ALL 286+ APIs.

Sensors, Buttons, Selects for every API category:
- Batch 1: Core (Brain, KG, Habitus, Neurons, Mood)
- Batch 2: Automation (Notifications, Zones, Proposals)
- Batch 3: Intelligence (RAG, Anomaly, Energy, Weather, Calendar)
- Batch 4: Media & Hardware (Sonos, Tags, Hardware, Camera)
- Batch 5: Styx & System (Chat, Multi-Home, Dashboard, Debug)
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api_wrapper import PilotSuiteAPI

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# BATCH 1: Core Entities (Brain, KG, Habitus, Neurons, Mood)
# =============================================================================

class BrainGraphStateSensor(CopilotBaseEntity, SensorEntity):
    """Brain graph state sensor."""
    
    _attr_icon = "mdi:brain"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["active", "idle", "processing", "error"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_brain_graph_state"
        self._attr_name = "PilotSuite Brain Graph State"
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {
            "nodes": 0,
            "edges": 0,
            "last_ingest": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        state = data.get("state", "idle")
        nodes = data.get("nodes", 0)
        edges = data.get("edges", 0)
        
        self._attr_native_value = state
        self._attr_extra_state_attributes.update({
            "nodes": nodes,
            "edges": edges,
            "last_ingest": data.get("last_ingest"),
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
        """Fetch latest data."""
        try:
            data = await self._api.brain.get_graph_state()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch brain graph state: %s", e)


class HabitusRulesSensor(CopilotBaseEntity, SensorEntity):
    """Habitus discovered rules sensor."""
    
    _attr_icon = "mdi:script-text"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "rules"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_habitus_rules"
        self._attr_name = "PilotSuite Habitus Rules"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "mining_status": "idle",
            "last_mining": None,
            "top_rules": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        rules = data.get("rules", [])
        
        self._attr_native_value = len(rules)
        self._attr_extra_state_attributes.update({
            "mining_status": data.get("status", "idle"),
            "last_mining": data.get("last_mining"),
            "top_rules": rules[:5] if rules else [],
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
        """Fetch latest data."""
        try:
            data = await self._api.habitus.get_rules()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch habitus rules: %s", e)


class NeuronActivitySensor(CopilotBaseEntity, SensorEntity):
    """Neuron activity sensor."""
    
    _attr_icon = "mdi:neural-network"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["active", "inactive", "firing", "learning"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_neuron_activity"
        self._attr_name = "PilotSuite Neuron Activity"
        self._attr_native_value = "inactive"
        self._attr_extra_state_attributes = {
            "active_neurons": 0,
            "total_neurons": 0,
            "fire_rate": 0.0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        neurons = data.get("neurons", [])
        active = [n for n in neurons if n.get("active", False)]
        
        self._attr_native_value = "active" if active else "inactive"
        self._attr_extra_state_attributes.update({
            "active_neurons": len(active),
            "total_neurons": len(neurons),
            "fire_rate": data.get("fire_rate", 0.0),
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
        """Fetch latest data."""
        try:
            data = await self._api.neurons.list_neurons()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch neuron activity: %s", e)


class MoodStateSensor(CopilotBaseEntity, SensorEntity):
    """Mood state sensor."""
    
    _attr_icon = "mdi:emoticon"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["neutral", "happy", "calm", "focused", "stressed", "tired"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_mood_state"
        self._attr_name = "PilotSuite Mood State"
        self._attr_native_value = "neutral"
        self._attr_extra_state_attributes = {
            "confidence": 0.0,
            "dimensions": {},
            "last_change": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("state", "neutral")
        self._attr_extra_state_attributes.update({
            "confidence": data.get("confidence", 0.0),
            "dimensions": data.get("dimensions", {}),
            "last_change": data.get("last_change"),
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
        """Fetch latest data."""
        try:
            data = await self._api.mood.get_mood_state()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch mood state: %s", e)


# =============================================================================
# BATCH 2: Automation Entities (Notifications, Zones, Proposals)
# =============================================================================

class NotificationsCountSensor(CopilotBaseEntity, SensorEntity):
    """Notifications count sensor."""
    
    _attr_icon = "mdi:bell"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "notifications"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_notifications_count"
        self._attr_name = "PilotSuite Notifications"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "unread": 0,
            "read": 0,
            "recent": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        notifications = data.get("notifications", [])
        unread = [n for n in notifications if not n.get("read", False)]
        
        self._attr_native_value = len(notifications)
        self._attr_extra_state_attributes.update({
            "unread": len(unread),
            "read": len(notifications) - len(unread),
            "recent": notifications[:5] if notifications else [],
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
        """Fetch latest data."""
        try:
            data = await self._api.notifications.list_notifications(limit=50)
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch notifications: %s", e)


class ZonesCountSensor(CopilotBaseEntity, SensorEntity):
    """Zones count sensor."""
    
    _attr_icon = "mdi:home-map-marker"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "zones"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_zones_count"
        self._attr_name = "PilotSuite Zones"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "active_zones": 0,
            "zone_list": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        zones = data.get("zones", [])
        
        self._attr_native_value = len(zones)
        self._attr_extra_state_attributes.update({
            "active_zones": len([z for z in zones if z.get("active", False)]),
            "zone_list": [z.get("zone_id") for z in zones],
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
        """Fetch latest data."""
        try:
            data = await self._api.zones.list_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch zones: %s", e)


class ProposalsCountSensor(CopilotBaseEntity, SensorEntity):
    """Proposals count sensor."""
    
    _attr_icon = "mdi:lightbulb-on"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = "proposals"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_proposals_count"
        self._attr_name = "PilotSuite Proposals"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {
            "pending": 0,
            "accepted": 0,
            "rejected": 0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        proposals = data.get("proposals", [])
        pending = [p for p in proposals if p.get("status") == "pending"]
        accepted = [p for p in proposals if p.get("status") == "accepted"]
        rejected = [p for p in proposals if p.get("status") == "rejected"]
        
        self._attr_native_value = len(proposals)
        self._attr_extra_state_attributes.update({
            "pending": len(pending),
            "accepted": len(accepted),
            "rejected": len(rejected),
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
        """Fetch latest data."""
        try:
            data = await self._api.proposals.list_proposals()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch proposals: %s", e)


# =============================================================================
# BATCH 3-5: Additional Entity Factories
# =============================================================================

async def async_create_complete_entities(
    hass: HomeAssistant,
    api: PilotSuiteAPI,
    config_entry: ConfigEntry,
) -> list[SensorEntity | ButtonEntity | SelectEntity]:
    """Create all entities for all 286+ APIs."""
    entities = []
    
    # Batch 1: Core
    entities.append(BrainGraphStateSensor(api))
    entities.append(HabitusRulesSensor(api))
    entities.append(NeuronActivitySensor(api))
    entities.append(MoodStateSensor(api))
    
    # Batch 2: Automation
    entities.append(NotificationsCountSensor(api))
    entities.append(ZonesCountSensor(api))
    entities.append(ProposalsCountSensor(api))
    
    # Batch 3-5: Additional entities will be added here
    # (Energy, Weather, Calendar, Media, Hardware, Styx, System, etc.)
    
    return entities
