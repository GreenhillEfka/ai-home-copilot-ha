"""Complete Entities Batch 4-5: Media/Hardware, Styx/System."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api_wrapper import PilotSuiteAPI

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# BATCH 4: Media & Hardware Entities
# =============================================================================

class MediaZoneSensor(CopilotBaseEntity, SensorEntity):
    """Media zone sensor."""
    
    _attr_icon = "mdi:speaker"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["playing", "paused", "idle", "offline"]
    
    def __init__(self, api: PilotSuiteAPI, zone_id: str, zone_name: str):
        super().__init__(api.api)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"pilotsuite_media_{zone_id}"
        self._attr_name = f"PilotSuite Media {zone_name}"
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {
            "zone_id": zone_id,
            "now_playing": None,
            "volume": 0,
            "player": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        zones = data.get("zones", [])
        zone_data = next((z for z in zones if z.get("zone_id") == self._zone_id), None)
        
        if zone_data:
            self._attr_native_value = zone_data.get("state", "idle")
            self._attr_extra_state_attributes.update({
                "now_playing": zone_data.get("now_playing"),
                "volume": zone_data.get("volume", 0),
                "player": zone_data.get("player"),
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
            data = await self._api.media.get_media_zones()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch media zone: %s", e)


class HardwareStatusSensor(CopilotBaseEntity, SensorEntity):
    """Hardware status sensor."""
    
    _attr_icon = "mdi:server"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["online", "offline", "degraded", "unknown"]
    
    def __init__(self, api: PilotSuiteAPI, hardware_type: str):
        super().__init__(api.api)
        self._hardware_type = hardware_type
        self._attr_unique_id = f"pilotsuite_hardware_{hardware_type}"
        self._attr_name = f"PilotSuite {hardware_type.title()} Status"
        self._attr_native_value = "unknown"
        self._attr_extra_state_attributes = {
            "devices_online": 0,
            "devices_total": 0,
            "health_score": 0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        status = data.get("status", "unknown")
        
        self._attr_native_value = status
        self._attr_extra_state_attributes.update({
            "devices_online": data.get("devices_online", 0),
            "devices_total": data.get("devices_total", 0),
            "health_score": data.get("health_score", 0),
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
            if self._hardware_type == "zigbee":
                data = await self._api.hardware.get_zigbee_status()
            elif self._hardware_type == "zwave":
                data = await self._api.hardware.get_zwave_status()
            elif self._hardware_type == "unifi":
                data = await self._api.hardware.get_unifi_status()
            else:
                data = await self._api.hardware.get_ha_module_status()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch hardware status: %s", e)


class CameraStatusSensor(CopilotBaseEntity, SensorEntity):
    """Camera status sensor."""
    
    _attr_icon = "mdi:cctv"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["recording", "idle", "offline", "motion"]
    
    def __init__(self, api: PilotSuiteAPI, camera_id: str):
        super().__init__(api.api)
        self._camera_id = camera_id
        self._attr_unique_id = f"pilotsuite_camera_{camera_id}"
        self._attr_name = f"PilotSuite Camera {camera_id}"
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {
            "camera_id": camera_id,
            "last_motion": None,
            "recording": False,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("state", "idle")
        self._attr_extra_state_attributes.update({
            "last_motion": data.get("last_motion"),
            "recording": data.get("recording", False),
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
            data = await self._api.camera.get_camera_status(self._camera_id)
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch camera status: %s", e)


# =============================================================================
# BATCH 5: Styx & System Entities
# =============================================================================

class StyxChatStatusSensor(CopilotBaseEntity, SensorEntity):
    """Styx chat status sensor."""
    
    _attr_icon = "mdi:robot"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ready", "processing", "error"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_styx_chat"
        self._attr_name = "PilotSuite Styx Chat"
        self._attr_native_value = "ready"
        self._attr_extra_state_attributes = {
            "conversations": 0,
            "last_message": None,
            "model": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("status", "ready")
        self._attr_extra_state_attributes.update({
            "conversations": data.get("conversations", 0),
            "last_message": data.get("last_message"),
            "model": data.get("model"),
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
            data = await self._api.styx.get_styx_dashboard()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch Styx status: %s", e)


class SystemHealthSensor(CopilotBaseEntity, SensorEntity):
    """System health sensor."""
    
    _attr_icon = "mdi:heart-pulse"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["healthy", "warning", "critical", "unknown"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_system_health"
        self._attr_name = "PilotSuite System Health"
        self._attr_native_value = "unknown"
        self._attr_extra_state_attributes = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "uptime": 0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("health", "unknown")
        self._attr_extra_state_attributes.update({
            "cpu_usage": data.get("cpu_usage", 0.0),
            "memory_usage": data.get("memory_usage", 0.0),
            "disk_usage": data.get("disk_usage", 0.0),
            "uptime": data.get("uptime", 0),
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
            data = await self._api.system.get_debug_status()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch system health: %s", e)


class MultiHomeStatusSensor(CopilotBaseEntity, SensorEntity):
    """Multi-home status sensor."""
    
    _attr_icon = "mdi:home-map-marker"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["synced", "syncing", "conflict", "offline"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_multihome"
        self._attr_name = "PilotSuite Multi-Home"
        self._attr_native_value = "synced"
        self._attr_extra_state_attributes = {
            "homes": 0,
            "sync_status": {},
            "conflicts": 0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        homes = data.get("homes", [])
        conflicts = data.get("conflicts", [])
        
        if len(conflicts) > 0:
            self._attr_native_value = "conflict"
        elif data.get("syncing", False):
            self._attr_native_value = "syncing"
        else:
            self._attr_native_value = "synced"
        
        self._attr_extra_state_attributes.update({
            "homes": len(homes),
            "sync_status": data.get("sync_status", {}),
            "conflicts": len(conflicts),
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
            homes = await self._api.multihome.list_homes()
            conflicts = await self._api.multihome.list_conflicts()
            self._handle_update({**homes, **conflicts})
        except Exception as e:
            _LOGGER.debug("Failed to fetch multi-home status: %s", e)


async def async_create_batch4_5_entities(
    hass: HomeAssistant,
    api: PilotSuiteAPI,
    config_entry: ConfigEntry,
) -> list[SensorEntity]:
    """Create Batch 4-5 entities."""
    entities = []
    
    # Batch 4: Media & Hardware
    # Get zones for media sensors
    try:
        zones_data = await api.zones.list_zones()
        zones = zones_data.get("zones", [])
        for zone in zones:
            zone_id = zone.get("zone_id", "unknown")
            zone_name = zone.get("zone_name", zone_id)
            entities.append(MediaZoneSensor(api, zone_id, zone_name))
    except Exception:
        pass
    
    # Hardware status
    for hw_type in ["zigbee", "zwave", "unifi", "ha"]:
        entities.append(HardwareStatusSensor(api, hw_type))
    
    # Cameras (get from API)
    try:
        cameras_data = await api.camera.list_cameras()
        cameras = cameras_data.get("cameras", [])
        for camera in cameras:
            camera_id = camera.get("camera_id", "unknown")
            entities.append(CameraStatusSensor(api, camera_id))
    except Exception:
        pass
    
    # Batch 5: Styx & System
    entities.append(StyxChatStatusSensor(api))
    entities.append(SystemHealthSensor(api))
    entities.append(MultiHomeStatusSensor(api))
    
    return entities
