"""PilotSuite Styx Habitus Zone Sync — HA Side.
Publishes HA Area changes to Core Habitus Zone API.
"""
from __future__ import annotations
import logging, requests, asyncio
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from .const import CONF_CORE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

class HabitusZoneSyncHandler:
    """Listens for HA Area changes and syncs to Core."""
    
    def __init__(self, hass: HomeAssistant, core_url: str):
        self.hass = hass
        self.core_url = core_url
        self._cancel_listen = None
        
    async def async_setup(self) -> bool:
        """Start listening for Area registry changes."""
        self.hass.bus.async_listen("area_registry_updated", self._on_area_change)
        _LOGGER.info("Habitus Zone Sync listening for area_registry_updated events")
        return True
    
    def _on_area_change(self, event: Event) -> None:
        """Trigger sync when Area changes."""
        area_id = event.data.get("area_id")
        _LOGGER.info(f"Area {area_id} changed, triggering Habitus Zone sync")
        self.hass.async_create_task(self._sync_area(area_id))
    
    async def _sync_area(self, area_id: str) -> None:
        """Sync single Area to Core Habitus Zone."""
        area = self.hass.config.area_registry.async_get_area(area_id)
        if not area:
            return
        
        zone_id = f"zone.{area.name.lower().replace(' ', '_')}"
        payload = {
            "zone_id": zone_id,
            "name": area.name,
            "ha_area_id": area_id,
            "linked_entities": []
        }
        
        try:
            resp = requests.post(f"{self.core_url}/api/v1/habitus/zones", json=payload, timeout=5)
            if resp.status_code in (200, 201):
                _LOGGER.info(f"Synced Area '{area.name}' to Core Habitus Zone {zone_id}")
            else:
                _LOGGER.error(f"Failed to sync Area {area.name}: {resp.text}")
        except Exception as e:
            _LOGGER.error(f"Error syncing Area {area.name}: {e}")
    
    async def async_unload(self) -> None:
        """Stop listening."""
        if self._cancel_listen:
            self._cancel_listen()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Habitus Zone Sync from config entry."""
    core_url = entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    sync_handler = HabitusZoneSyncHandler(hass, core_url)
    await sync_handler.async_setup()
    hass.data.setdefault(DOMAIN, {})["habitus_sync"] = sync_handler
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Habitus Zone Sync."""
    if "habitus_sync" in hass.data.get(DOMAIN, {}):
        await hass.data[DOMAIN]["habitus_sync"].async_unload()
    return True
