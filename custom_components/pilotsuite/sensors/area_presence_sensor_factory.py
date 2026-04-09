"""Area Presence Sensor Factory — built from Habitus zone entity roles.

Auto-creates AreaPresenceSensor entities for each zone by resolving source
entities from Habitus zone metadata.

Factory contract:
- stateless builder shell, no runtime presence state is stored here
- source resolution + validation happen before entity construction
- built entities keep the runtime state and lifecycle behavior
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import TYPE_CHECKING, Literal

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant

from ..habitus_zones_store_v2 import HabitusZoneV2, async_get_zones_v2

if TYPE_CHECKING:
    from ..coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SensorDomain = Literal["binary_sensor", "sensor", "number"]
ResolutionStrategy = Literal["union", "intersection", "weighted", "temporal"]

# Import here to avoid circular at runtime
_presence_sensor_module = None


@dataclass(frozen=True)
class SensorFactoryConfig:
    """Immutable builder configuration for area presence sensors."""

    sensor_domain: SensorDomain = "binary_sensor"
    name_template: str = "Praesenz {zone_name}"
    unique_id_template: str = "area_presence_{zone_id}"
    resolution_strategy: ResolutionStrategy = "union"
    temporal_window_seconds: int | None = None
    device_class: str | None = str(BinarySensorDeviceClass.OCCUPANCY)
    unit_of_measurement: str | None = None
    icon: str | None = "mdi:motion-sensor"
    min_sources: int = 1
    max_sources: int | None = None
    required_source_domains: tuple[str, ...] = (
        "binary_sensor",
        "device_tracker",
        "person",
    )


@dataclass(frozen=True)
class ValidatedSourceSet:
    """Resolved and validated source entities for one zone."""

    mmwave_entities: tuple[str, ...] = ()
    motion_entities: tuple[str, ...] = ()
    ble_entities: tuple[str, ...] = ()
    person_entities: tuple[str, ...] = ()
    missing_entities: tuple[str, ...] = ()
    candidate_entities: tuple[str, ...] = ()
    degraded: bool = False
    resolution_strategy: ResolutionStrategy = "union"
    notes: tuple[str, ...] = ()

    @property
    def total_sources(self) -> int:
        return (
            len(self.mmwave_entities)
            + len(self.motion_entities)
            + len(self.ble_entities)
            + len(self.person_entities)
        )

    def as_dict(self) -> dict:
        return {
            "resolution_strategy": self.resolution_strategy,
            "candidate_entities": list(self.candidate_entities),
            "resolved_sources": {
                "mmwave": list(self.mmwave_entities),
                "motion": list(self.motion_entities),
                "ble": list(self.ble_entities),
                "person": list(self.person_entities),
            },
            "missing_entities": list(self.missing_entities),
            "degraded": self.degraded,
            "notes": list(self.notes),
            "total_sources": self.total_sources,
        }


def _get_area_presence_sensor_class():
    global _presence_sensor_module
    if _presence_sensor_module is None:
        from . import area_presence_sensor as mod
        _presence_sensor_module = mod
    return _presence_sensor_module


def _build_factory_config(zone: HabitusZoneV2) -> SensorFactoryConfig:
    """Build immutable factory config for one zone.

    Area presence uses union/any-on semantics. Runtime hold/timeout behavior
    remains inside AreaPresenceSensor.
    """
    temporal_window_seconds = None
    metadata = zone.metadata if isinstance(zone.metadata, dict) else {}
    if isinstance(metadata.get("presence_temporal_window_seconds"), int):
        temporal_window_seconds = metadata["presence_temporal_window_seconds"]

    return SensorFactoryConfig(
        sensor_domain="binary_sensor",
        name_template="Praesenz {zone_name}",
        unique_id_template="area_presence_{zone_id}",
        resolution_strategy="union",
        temporal_window_seconds=temporal_window_seconds,
        device_class=str(BinarySensorDeviceClass.OCCUPANCY),
        icon="mdi:motion-sensor",
        min_sources=1,
    )


def _collect_candidate_entity_ids(zone: HabitusZoneV2) -> list[str]:
    """Collect all candidate source entities declared on a zone."""
    seen: set[str] = set()
    ordered: list[str] = []

    if isinstance(zone.entity_ids, (list, tuple)):
        for eid in zone.entity_ids:
            if isinstance(eid, str) and eid not in seen:
                seen.add(eid)
                ordered.append(eid)

    if isinstance(zone.entities, dict):
        for eids in zone.entities.values():
            if not isinstance(eids, (list, tuple)):
                continue
            for eid in eids:
                if isinstance(eid, str) and eid not in seen:
                    seen.add(eid)
                    ordered.append(eid)

    return ordered


async def async_build_area_presence_sensors(
    hass: HomeAssistant,
    entry_id: str,
    coordinator: "CopilotDataUpdateCoordinator",
    entry,
) -> list:
    """Build AreaPresenceSensor entities for all zones."""
    zones: list[HabitusZoneV2] = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.debug("No zones found for area presence sensor creation")
        return []

    area_presence_sensor = _get_area_presence_sensor_class()
    sensors = []

    for zone in zones:
        zone_id = zone.zone_id.replace("zone:", "")
        zone_name = zone.name
        config = _build_factory_config(zone)
        sources = await _resolve_presence_sources(hass, zone, config)

        if sources.total_sources < config.min_sources:
            _LOGGER.debug(
                "Zone %s has no resolved presence sources, skipping area presence sensor",
                zone_name,
            )
            continue

        sensor_cls = getattr(area_presence_sensor, "AreaPresenceSensor", area_presence_sensor)
        sensor = sensor_cls(
            coordinator=coordinator,
            entry=entry,
            zone_id=zone_id,
            zone_name=zone_name,
            mmwave_entities=list(sources.mmwave_entities),
            motion_entities=list(sources.motion_entities),
            ble_entities=list(sources.ble_entities),
            person_entities=list(sources.person_entities),
            factory_config=config,
            source_summary=sources.as_dict(),
        )
        sensors.append(sensor)
        _LOGGER.info(
            "AreaPresenceSensor created: zone=%s, strategy=%s, sources=%d, degraded=%s",
            zone_name,
            config.resolution_strategy,
            sources.total_sources,
            sources.degraded,
        )

    return sensors


async def _resolve_presence_sources(
    hass: HomeAssistant,
    zone: HabitusZoneV2,
    config: SensorFactoryConfig,
) -> ValidatedSourceSet:
    """Resolve and validate source entities for an area presence sensor."""
    entities: dict[str, list[str]] = zone.entities or {}
    mmwave_entities: list[str] = []
    motion_entities: list[str] = []
    missing_entities: list[str] = []
    notes: list[str] = []

    for role, eids in entities.items():
        if not isinstance(eids, (list, tuple)):
            continue
        eid_list = [eid for eid in eids if isinstance(eid, str)]
        missing_entities.extend([eid for eid in eid_list if hass.states.get(eid) is None])
        if role == "motion":
            mm, mo = await _split_mmwave_motion(hass, eid_list)
            mmwave_entities.extend(mm)
            motion_entities.extend(mo)
        elif role in ("door", "window", "lock"):
            continue
        else:
            _extra_mm, extra_mo = await _split_mmwave_motion(hass, eid_list)
            motion_entities.extend(extra_mo)

    ble_entities = await _discover_ble_trackers(hass, zone)
    person_entities = await _discover_persons_for_zone(hass, zone)
    candidate_entities = tuple(_collect_candidate_entity_ids(zone))
    degraded = bool(missing_entities)
    if degraded:
        notes.append("Some configured source entities are currently missing")

    source_set = ValidatedSourceSet(
        mmwave_entities=tuple(mmwave_entities),
        motion_entities=tuple(motion_entities),
        ble_entities=tuple(ble_entities),
        person_entities=tuple(person_entities),
        missing_entities=tuple(dict.fromkeys(missing_entities)),
        candidate_entities=candidate_entities,
        degraded=degraded,
        resolution_strategy=config.resolution_strategy,
        notes=tuple(notes),
    )
    return _validate_source_set(source_set, config)


def _validate_source_set(
    source_set: ValidatedSourceSet,
    config: SensorFactoryConfig,
) -> ValidatedSourceSet:
    """Apply builder-level validation to a resolved source set."""
    notes = list(source_set.notes)

    if config.max_sources is not None and source_set.total_sources > config.max_sources:
        notes.append("Resolved sources exceed configured max_sources")

    missing_domains = []
    for domain in config.required_source_domains:
        if domain == "binary_sensor" and not (
            source_set.mmwave_entities or source_set.motion_entities
        ):
            missing_domains.append(domain)
        elif domain == "device_tracker" and not source_set.ble_entities:
            continue
        elif domain == "person" and not source_set.person_entities:
            continue

    if missing_domains:
        notes.append(f"Required source domains not present: {', '.join(missing_domains)}")

    return ValidatedSourceSet(
        mmwave_entities=source_set.mmwave_entities,
        motion_entities=source_set.motion_entities,
        ble_entities=source_set.ble_entities,
        person_entities=source_set.person_entities,
        missing_entities=source_set.missing_entities,
        candidate_entities=source_set.candidate_entities,
        degraded=source_set.degraded,
        resolution_strategy=source_set.resolution_strategy,
        notes=tuple(notes),
    )


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
            motion.append(eid)
    return mmwave, motion


async def _discover_ble_trackers(
    hass: HomeAssistant,
    zone: HabitusZoneV2,
) -> list[str]:
    """Find device_tracker entities with source_type=bluetooth in the zone."""
    ble = []
    all_ids = set(zone.entity_ids) if zone.entity_ids else set()
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

    if isinstance(zone.metadata, dict):
        ha_area_ids.update(zone.metadata.get("ha_area_ids", []))

    for state in hass.states.async_all("person"):
        if str(state.state).lower() != "home":
            continue
        attrs = dict(state.attributes)
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
