"""Entity-centric zone reassignment via HA services.

Provides services to assign/remove entities from Habitus Zones
using the HA entity selector (entity-centric workflow).
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .habitus_zones_store_v2 import (
    HabitusZoneV2,
    async_get_zones_v2,
    async_set_zones_v2,
)

_LOGGER = logging.getLogger(__name__)

UNASSIGNED = "Nicht zugeordnet"


def _find_entry_id(hass: HomeAssistant) -> str | None:
    """Find the first pilotsuite config entry ID."""
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0].entry_id if entries else None


def _rebuild_zone_with_entity(
    zone: HabitusZoneV2,
    entity_id: str,
    add: bool,
) -> HabitusZoneV2:
    """Return a new zone with entity added or removed."""
    current = set(zone.entity_ids)
    if add:
        current.add(entity_id)
    else:
        current.discard(entity_id)

    # Also update role-based mapping if present
    new_entities = None
    if zone.entities:
        new_entities = dict(zone.entities)
        if add:
            # Add to "other" role by default
            other = list(new_entities.get("other", ()))
            if entity_id not in other:
                other.append(entity_id)
            new_entities["other"] = tuple(other)
        else:
            # Remove from all roles
            for role, eids in list(new_entities.items()):
                filtered = tuple(e for e in eids if e != entity_id)
                if filtered:
                    new_entities[role] = filtered
                else:
                    del new_entities[role]
            if not new_entities:
                new_entities = None

    return HabitusZoneV2(
        zone_id=zone.zone_id,
        name=zone.name,
        zone_type=zone.zone_type,
        entity_ids=tuple(sorted(current)),
        entities=new_entities,
        parent_zone_id=zone.parent_zone_id,
        child_zone_ids=zone.child_zone_ids,
        floor=zone.floor,
        graph_node_id=zone.graph_node_id,
        current_state=zone.current_state,
        state_since_ms=zone.state_since_ms,
        priority=zone.priority,
        tags=zone.tags,
        metadata=zone.metadata,
    )


async def async_assign_entity_to_zone(
    hass: HomeAssistant,
    entity_id: str,
    zone_id: str,
    entry_id: str | None = None,
) -> bool:
    """Assign an entity to a zone, removing it from any current zone first.

    Returns True if the assignment was successful.
    """
    entry_id = entry_id or _find_entry_id(hass)
    if not entry_id:
        _LOGGER.warning("No config entry found for zone assignment")
        return False

    zones = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.warning("No zones configured")
        return False

    # Find target zone
    target_zone = None
    for z in zones:
        if z.zone_id == zone_id:
            target_zone = z
            break

    if target_zone is None:
        _LOGGER.warning("Zone '%s' not found", zone_id)
        return False

    # Remove from all current zones, add to target
    updated: list[HabitusZoneV2] = []
    for z in zones:
        if z.zone_id == zone_id:
            updated.append(_rebuild_zone_with_entity(z, entity_id, add=True))
        elif entity_id in z.get_all_entities():
            updated.append(_rebuild_zone_with_entity(z, entity_id, add=False))
        else:
            updated.append(z)

    await async_set_zones_v2(hass, entry_id, updated, validate=False)
    _LOGGER.info("Entity '%s' assigned to zone '%s'", entity_id, zone_id)
    return True


async def async_remove_entity_from_zone(
    hass: HomeAssistant,
    entity_id: str,
    entry_id: str | None = None,
) -> bool:
    """Remove an entity from all zones.

    Returns True if the entity was found and removed.
    """
    entry_id = entry_id or _find_entry_id(hass)
    if not entry_id:
        _LOGGER.warning("No config entry found for zone removal")
        return False

    zones = await async_get_zones_v2(hass, entry_id)
    if not zones:
        return False

    found = False
    updated: list[HabitusZoneV2] = []
    for z in zones:
        if entity_id in z.get_all_entities():
            updated.append(_rebuild_zone_with_entity(z, entity_id, add=False))
            found = True
        else:
            updated.append(z)

    if found:
        await async_set_zones_v2(hass, entry_id, updated, validate=False)
        _LOGGER.info("Entity '%s' removed from all zones", entity_id)

    return found


async def async_get_entity_zone(
    hass: HomeAssistant,
    entity_id: str,
    entry_id: str | None = None,
) -> str | None:
    """Get the zone_id an entity currently belongs to. None if unassigned."""
    entry_id = entry_id or _find_entry_id(hass)
    if not entry_id:
        return None

    zones = await async_get_zones_v2(hass, entry_id)
    for z in zones:
        if entity_id in z.get_all_entities():
            return z.zone_id
    return None
