"""Select platform for PilotSuite integration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

from .const import (
    DEBUG_LEVELS,
    DEBUG_LEVEL_FULL,
    DEBUG_LEVEL_LIGHT,
    DEBUG_LEVEL_OFF,
    DEFAULT_DEBUG_LEVEL,
    DOMAIN,
)
from .entity import CopilotBaseEntity
from .media_context_v2_entities import (
    ZoneSelectEntity,
    ManualTargetSelectEntity,
)
from .habitus_zones_entities_v2 import HabitusZonesV2GlobalStateSelect


class DiagnosticLevelSelectEntity(CopilotBaseEntity, SelectEntity):
    """Select entity to control debug/diagnostic level."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Debug Level"
    _attr_unique_id = "debug_level_select"
    _attr_icon = "mdi:bug-check"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_options = DEBUG_LEVELS
        self._attr_current_option = DEFAULT_DEBUG_LEVEL

    async def async_select_option(self, option: str) -> None:
        """Set the debug level."""
        if option not in DEBUG_LEVELS:
            return

        self._attr_current_option = option

        # Call service to update state
        await self.hass.services.async_call(
            DOMAIN,
            "set_debug_level",
            {"entry_id": self._entry_id, "level": option},
            blocking=False,
        )

        # Log the change
        kernel = self.coordinator.hass.data.get(DOMAIN, {}).get(self._entry_id, {}).get("dev_surface")
        if isinstance(kernel, dict) and "devlog" in kernel:
            kernel["devlog"].add(
                level="info",
                typ="debug_level",
                msg=f"Debug level changed to {option}",
                data={"level": option},
            )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up select entities for the integration."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        _LOGGER.error("Entry data not available for %s, skipping select setup", entry.entry_id)
        return
    coordinator = data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for %s, skipping select setup", entry.entry_id)
        return
    
    entities = [
        DiagnosticLevelSelectEntity(coordinator, entry.entry_id),
        # v2 Select
        HabitusZonesV2GlobalStateSelect(coordinator, entry),
    ]
    
    # Media Context v2 select entities
    media_coordinator_v2 = data.get("media_coordinator_v2") if isinstance(data, dict) else None
    if media_coordinator_v2 is not None:
        entities.extend([
            ZoneSelectEntity(media_coordinator_v2),
            ManualTargetSelectEntity(media_coordinator_v2),
        ])

    if entities:
        async_add_entities(entities, True)

    # Autonomy zone module selects (v14.2.0)
    try:
        from .autonomy_entities import create_zone_autonomy_entities, ZoneModuleStateSelect
        from .habitus_zones_store_v2 import async_get_zones_v2
        zones = await async_get_zones_v2(hass, entry.entry_id)
        zone_list = [{"zone_id": z.zone_id, "name": getattr(z, "name_de", None) or z.name} for z in zones]
        autonomy_entities = [e for e in create_zone_autonomy_entities(coordinator, zone_list) if isinstance(e, ZoneModuleStateSelect)]
        if autonomy_entities:
            async_add_entities(autonomy_entities, True)
    except Exception:
        _LOGGER.debug("Autonomy zone selects skipped (zones not configured)")

    # Zone automation mode selects (off/learning/autonomy per zone)
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
        zone_selects = result.get("select", [])
        if zone_selects:
            async_add_entities(zone_selects, True)
    except Exception:
        _LOGGER.debug("Zone automation mode selects skipped (zones not configured)")