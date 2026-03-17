"""Switch platform for PilotSuite integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_FRONTEND_MODULE_READY

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
        zone_list = []
        for z in zones:
            meta = z.metadata or {}
            area_names = meta.get("ha_area_names")
            area_name = area_names[0] if isinstance(area_names, list) and area_names else None
            zone_list.append({
                "zone_id": z.zone_id,
                "name": getattr(z, "name_de", None) or z.name,
                "area_name": area_name or z.name,
            })
        result = create_zone_automation_entities(coordinator, zone_list)
        entities.extend(result.get("switch", []))
    except Exception:
        _LOGGER.debug("Zone automation switches skipped (zones not configured)")

    # Dashboard view toggle switches (if frontend_module already loaded)
    frontend_switches_added = False
    try:
        frontend_mod = data.get("frontend_module")
        if frontend_mod is not None:
            from .frontend_entities import create_frontend_entities
            result = create_frontend_entities(coordinator, entry)
            entities.extend(result.get("switch", []))
            frontend_switches_added = True
    except Exception:
        _LOGGER.debug("Dashboard view toggles skipped")

    # Neuron feed per-tag switches
    try:
        from .neuron_feed_entities import async_create_neuron_feed_entities

        nf_result = await async_create_neuron_feed_entities(coordinator)
        entities.extend(nf_result.get("switch", []))
    except Exception:
        _LOGGER.debug("Neuron feed switches skipped")

    if entities:
        async_add_entities(entities, True)

    # Lazy creation: if frontend_module loads after switch platform,
    # add view toggles when SIGNAL_FRONTEND_MODULE_READY fires.
    # Guard prevents double-creation if already added above.
    @callback
    def _on_frontend_ready(ready_entry_id: str) -> None:
        nonlocal frontend_switches_added
        if ready_entry_id != entry.entry_id:
            return
        if frontend_switches_added:
            return
        try:
            from .frontend_entities import create_frontend_entities
            result = create_frontend_entities(coordinator, entry)
            new_switches = result.get("switch", [])
            if new_switches:
                async_add_entities(new_switches, True)
                frontend_switches_added = True
        except Exception:
            _LOGGER.debug("Failed to add frontend view switches on signal")

    async_dispatcher_connect(hass, SIGNAL_FRONTEND_MODULE_READY, _on_frontend_ready)
