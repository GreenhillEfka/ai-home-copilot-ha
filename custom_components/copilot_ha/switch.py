"""Switch platform for PilotSuite integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up switch entities for the integration."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        _LOGGER.debug("Entry data not available for %s, skipping switch setup", entry.entry_id)
        return
    coordinator = data.get("coordinator")
    if coordinator is None:
        _LOGGER.debug("Coordinator not available for %s, skipping switch setup", entry.entry_id)
        return

    entities = []

    # Zone automation switches (light auto, music auto, music follow)
    try:
        from .zone_automation_entities import create_zone_automation_entities
        from .habitus_zones_store_v2 import async_get_zones_v2

        zones = await async_get_zones_v2(hass, entry.entry_id)
        zone_list = [
            {"zone_id": z.zone_id, "name": getattr(z, "name_de", None) or z.name}
            for z in zones
        ]
        result = create_zone_automation_entities(coordinator, zone_list)
        entities.extend(result.get("switch", []))
    except Exception:
        _LOGGER.debug("Zone automation switches skipped (zones not configured)")

    if entities:
        async_add_entities(entities, True)
