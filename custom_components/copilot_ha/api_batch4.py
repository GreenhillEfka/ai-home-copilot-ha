"""Batch 4: Media & Hardware APIs — Sonos, Tags, Hardware, Camera."""
from __future__ import annotations
from .api import CopilotApiClient


class MediaAPI(CopilotApiClient):
    """Media & Sonos API client."""
    
    async def get_media_zones(self) -> dict:
        """Get media zones."""
        return await self._get_json("/api/v1/media/zones")
    
    async def get_zone_players(self, zone_id: str) -> dict:
        """Get zone players."""
        return await self._get_json(f"/api/v1/media/zones/{zone_id}")
    
    async def assign_player(self, zone_id: str, player_id: str) -> dict:
        """Assign player to zone."""
        return await self._post_json(f"/api/v1/media/zones/{zone_id}/assign", {"player_id": player_id})
    
    async def play(self, zone_id: str) -> dict:
        """Play in zone."""
        return await self._post_json(f"/api/v1/media/zones/{zone_id}/play", {})
    
    async def pause(self, zone_id: str) -> dict:
        """Pause in zone."""
        return await self._post_json(f"/api/v1/media/zones/{zone_id}/pause", {})
    
    async def set_volume(self, zone_id: str, volume: int) -> dict:
        """Set volume."""
        return await self._post_json(f"/api/v1/media/zones/{zone_id}/volume", {"volume": volume})
    
    async def get_now_playing(self, zone_id: str) -> dict:
        """Get now playing."""
        return await self._get_json(f"/api/v1/media/zones/{zone_id}/track")
    
    async def get_sonos_status(self) -> dict:
        """Get Sonos status."""
        return await self._get_json("/api/v1/sonos/status")
    
    async def get_musikwolke_status(self) -> dict:
        """Get music cloud status."""
        return await self._get_json("/api/v1/musikwolke/status")
    
    async def get_zone_map(self) -> dict:
        """Get zone-speaker map."""
        return await self._get_json("/api/v1/musikwolke/zone-map")
    
    async def set_zone_speaker(self, zone_id: str, speaker_id: str) -> dict:
        """Set zone speaker."""
        return await self._post_json("/api/v1/musikwolke/zone-map", {"zone_id": zone_id, "speaker_id": speaker_id})
    
    async def auto_discover_speakers(self) -> dict:
        """Auto-discover speakers."""
        return await self._post_json("/api/v1/musikwolke/auto-discover", {})


class TagsAPI(CopilotApiClient):
    """Tags & Entity Management API client."""
    
    async def list_tags(self) -> dict:
        """List all tags."""
        return await self._get_json("/api/v1/tag-system/tags")
    
    async def get_tag(self, tag_id: str) -> dict:
        """Get tag."""
        return await self._get_json(f"/api/v1/tag-system/tags/{tag_id}")
    
    async def create_tag(self, tag: dict) -> dict:
        """Create tag."""
        return await self._post_json("/api/v1/tag-system/tags", tag)
    
    async def delete_tag(self, tag_id: str) -> dict:
        """Delete tag."""
        return await self._post_json(f"/api/v1/tag-system/tags/{tag_id}/delete", {})
    
    async def list_assignments(self) -> dict:
        """List entity assignments."""
        return await self._get_json("/api/v1/tag-system/assignments")
    
    async def assign_entity(self, entity_id: str, tag_id: str) -> dict:
        """Assign entity to tag."""
        return await self._post_json("/api/v1/tag-system/assign", {"entity_id": entity_id, "tag_id": tag_id})
    
    async def get_zone_entities(self, zone_id: str) -> dict:
        """Get zone entities."""
        return await self._get_json(f"/api/v1/zones/{zone_id}/entities")
    
    async def get_all_zones_entities(self) -> dict:
        """Get all zones entities."""
        return await self._get_json("/api/v1/entity_adoption/zones")
    
    async def assign_entity_to_zone(self, entity_id: str, zone_id: str) -> dict:
        """Assign entity to zone."""
        return await self._post_json("/api/v1/entity_adoption/assign", {"entity_id": entity_id, "zone_id": zone_id})
    
    async def get_assignment_suggestions(self) -> dict:
        """Get assignment suggestions."""
        return await self._get_json("/api/v1/entity_assignment/suggestions")


class HardwareAPI(CopilotApiClient):
    """Hardware & Mesh API client."""
    
    async def get_zigbee_status(self) -> dict:
        """Get Zigbee status."""
        return await self._get_json("/api/v1/zigbee_module/status")
    
    async def get_zwave_status(self) -> dict:
        """Get Z-Wave status."""
        return await self._get_json("/api/v1/zwave_module/status")
    
    async def get_unifi_status(self) -> dict:
        """Get UniFi status."""
        return await self._get_json("/api/v1/unifi_stub/status")
    
    async def get_ha_module_status(self) -> dict:
        """Get HA module status."""
        return await self._get_json("/api/v1/ha_module/status")
    
    async def get_ha_connection(self) -> dict:
        """Get HA connection."""
        return await self._get_json("/api/v1/ha_module/connection")
    
    async def get_ha_events(self) -> dict:
        """Get HA events."""
        return await self._get_json("/api/v1/ha_module/events")
    
    async def configure_ha_events(self, config: dict) -> dict:
        """Configure HA events."""
        return await self._post_json("/api/v1/ha_module/events/config", config)
    
    async def list_sensors(self) -> dict:
        """List sensors."""
        return await self._get_json("/api/v1/sensors")
    
    async def call_service(self, domain: str, service: str, data: dict) -> dict:
        """Call HA service."""
        return await self._post_json("/api/v1/service", {"domain": domain, "service": service, "data": data})
    
    async def get_comfort_status(self) -> dict:
        """Get comfort status."""
        return await self._get_json("/api/v1/comfort")
    
    async def get_comfort_lighting(self) -> dict:
        """Get comfort lighting."""
        return await self._get_json("/api/v1/comfort/lighting")


class CameraAPI(CopilotApiClient):
    """Camera API client."""
    
    async def list_cameras(self) -> dict:
        """List cameras."""
        return await self._get_json("/api/v1/camera")
    
    async def get_camera_snapshot(self, camera_id: str) -> str:
        """Get camera snapshot."""
        return await self._get_json(f"/api/v1/camera/{camera_id}/snapshot")
    
    async def get_camera_status(self, camera_id: str) -> dict:
        """Get camera status."""
        return await self._get_json(f"/api/v1/camera/{camera_id}/status")
