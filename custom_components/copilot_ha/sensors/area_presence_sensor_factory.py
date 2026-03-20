"""Area Presence Sensor Factory — built from Habitus zone entity roles.

Auto-creates AreaPresenceSensor entities for each zone, discovering
mmWave / motion / BLE / person entities from the zone's role assignments.

Called by async_setup_entry → sensor setup after zone data is available.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant

from ..habitus_zones_store_v2 import HabitusZoneV2, async_get_zones_v2

if TYPE_CHECKING:
    from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Import here to avoid circular at runtime
_presence_sensor_module = None


def _get_area_presence_sensor_class():
    global _presence_sensor_module
    if _presence_sensor_module is None:
        from . import area_presence_sensor as mod
        _presence_sensor_module = mod
    return _presence_sensor_module


async def async_build_area_presence_sensors(
    hass: HomeAssistant,
    entry_id: str,
    coordinator: "CopilotDataUpdateCoordinator",
    entry,
) -> list:
    """Build AreaPresenceSensor entities for all zones.

    Auto-detects source entities from zone role assignments:
      - mmwave_entities:  role "motion" + device_class "presence"
      - motion_entities:  role "motion" + device_class "motion"
      - ble_entities:     device_tracker with source_type bluetooth
      - person_entities:  person entities linked to the zone

    Returns list of AreaPresenceSensor instances (may be empty).
    """
    zones: list[HabitusZoneV2] = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.debug("No zones found for area presence sensor creation")
        return []

    AreaPresenceSensor = _get_area_presence_sensor_class()

    sensors = []
    for zone in zones:
        zone_id = zone.zone_id.replace("zone:", "")
        zone_name = zone.name

        # Resolve entity IDs from zone's role assignments
        entities: dict[str, list[str]] = zone.entities or {}
        if isinstance(zone.entity_ids, (list, tuple)):
            # Flat: zone.entity_ids contains all entity IDs directly
            all_entity_ids = list(zone.entity_ids)
        else:
            all_entity_ids = []

        mmwave_entities, motion_entities, ble_entities, person_entities = [], [], [], []

        for role, eids in entities.items():
            if not isinstance(eids, (list, tuple)):
                continue
            eid_list = list(eids)
            if role == "motion":
                # Separate mmWave vs PIR by device_class lookup
                mm, mo = await _split_mmwave_motion(hass, eid_list)
                mmwave_entities.extend(mm)
                motion_entities.extend(mo)
            elif role in ("door", "window", "lock"):
                pass  # not presence sources
            else:
                # Other roles — include as motion if they look like motion sensors
                extra_mm, extra_mo = await _split_mmwave_motion(hass, eid_list)
                motion_entities.extend(extra_mo)

        # BLE / device_tracker discovery
        ble_entities = await _discover_ble_trackers(hass, zone)

        # Person entities linked to this zone
        person_entities = await _discover_persons_for_zone(hass, zone)

        # Skip zones with no presence sources
        has_sources = (
            mmwave_entities or motion_entities or ble_entities or person_entities
        )
        if not has_sources:
            _LOGGER.debug(
                "Zone %s has no presence sources, skipping area presence sensor",
                zone_name,
            )
            continue

        sensor = AreaPresenceSensor(
            coordinator=coordinator,
            entry=entry,
            zone_id=zone_id,
            zone_name=zone_name,
            mmwave_entities=mmwave_entities,
            motion_entities=motion_entities,
            ble_entities=ble_entities,
            person_entities=person_entities,
        )
        sensors.append(sensor)
        _LOGGER.info(
            "AreaPresenceSensor created: zone=%s, mmwave=%d, motion=%d, ble=%d, persons=%d",
            zone_name,
            len(mmwave_entities),
            len(motion_entities),
            len(ble_entities),
            len(person_entities),
        )

    return sensors


async def _split_mmwave_motion(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> tuple[list[str], list[str]]:
    """Split entity IDs into mmWave (device_class=presence) vs PIR motion."""
    mmwave, motion = [], []
    for eid in entity_ids:
        state = hass.states.get(eid)
        if state is None:
            continue
        dc = str(state.attributes.get("device_class", "")).lower()
        if dc == "presence":
            mmwave.append(eid)
        elif dc in ("motion", ""):
            motion.append(eid)
        else:
            # Unknown device_class — treat as motion for safety
            motion.append(eid)
    return mmwave, motion


async def _discover_ble_trackers(
    hass: HomeAssistant,
    zone: HabitusZoneV2,
) -> list[str]:
    """Find device_tracker entities with source_type=bluetooth in the zone."""
    ble = []
    all_ids = set(zone.entity_ids) if zone.entity_ids else set()
    # Also collect from entities dict
    if isinstance(zone.entities, dict):
        for eids in zone.entities.values():
            if isinstance(eids, (list, tuple)):
                all_ids.update(eids)

    for eid in all_ids:
        if not eid.startswith("device_tracker."):
            continue
        state = hass.states.get(eid)
        if state is None:
            continue
        attrs = dict(state.attributes)
        source_type = str(attrs.get("source_type", "")).lower()
        if source_type == "bluetooth":
            ble.append(eid)

    return ble


async def _discover_persons_for_zone(
    hass: HomeAssistant,
    zone: HabitusZoneV2,
) -> list[str]:
    """Find person entities whose home_zone or area matches this zone."""
    persons = []
    ha_area_ids: set[str] = set()

    # Get HA area IDs from zone metadata
    if isinstance(zone.metadata, dict):
        ha_area_ids.update(zone.metadata.get("ha_area_ids", []))

    for state in hass.states.async_all("person"):
        if str(state.state).lower() != "home":
            continue
        attrs = dict(state.attributes)
        # Check if person's zone matches this zone's areas
        person_zone = str(attrs.get("zone", "")).lower()
        person_area = str(attrs.get("area_id", "")).lower()

        matched = False
        if person_zone and any(
            a.lower() in person_zone or person_zone in a.lower()
            for a in ha_area_ids
        ):
            matched = True
        if not matched and person_area and person_area in ha_area_ids:
            matched = True

        if matched:
            persons.append(state.entity_id)

    return persons
