from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, SIGNAL_CONTEXT_ENTITIES_REFRESH
from .coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
from .entity import CopilotBaseEntity
from .entity_profile import is_full_entity_profile
from .media_entities import MusicActiveBinarySensor, TvActiveBinarySensor
from .forwarder_quality_entities import EventsForwarderConnectedBinarySensor
from .mesh_monitoring import ZWaveMeshStatusBinarySensor, ZigbeeMeshStatusBinarySensor
from .camera_entities import (
    MotionDetectionCamera,
    PresenceCamera,
)
from .unifi_context_entities import build_unifi_binary_entities
from .sensors.zone_presence_trigger import (
    ZonePresenceTriggerSensor,
    ZonePresenceOverviewSensor,
)
from .habitus_zones_store_v2 import HabitusZoneV2, async_get_zones_v2


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for %s, skipping binary_sensor setup", entry.entry_id)
        return

    if not is_full_entity_profile(entry):
        async_add_entities([CopilotOnlineBinarySensor(coordinator, entry)], True)
        return

    dynamic_context_unique_ids: set[str] = set()

    def _collect_dynamic_context_binaries() -> list[BinarySensorEntity]:
        entities_out: list[BinarySensorEntity] = []
        unifi_coordinator = data.get("unifi_context_coordinator") if isinstance(data, dict) else None
        if unifi_coordinator is None:
            return entities_out
        try:
            for entity in build_unifi_binary_entities(unifi_coordinator):
                unique_id = str(getattr(entity, "unique_id", "") or "")
                if unique_id and unique_id in dynamic_context_unique_ids:
                    continue
                if unique_id:
                    dynamic_context_unique_ids.add(unique_id)
                entities_out.append(entity)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to create UniFi context binary entities")
        return entities_out

    entities = [
        CopilotOnlineBinarySensor(coordinator, entry),
        CoreApiHealthyBinarySensor(coordinator, entry),
        CopilotSyncStatusBinarySensor(coordinator, entry),
    ]

    # Events Forwarder quality binary sensor (v0.1 kernel)
    if isinstance(data, dict) and data.get("events_forwarder_state") is not None:
        entities.append(EventsForwarderConnectedBinarySensor(coordinator, entry))

    media_coordinator = data.get("media_coordinator") if isinstance(data, dict) else None
    if media_coordinator is not None:
        entities.extend(
            [
                MusicActiveBinarySensor(media_coordinator),
                TvActiveBinarySensor(media_coordinator),
            ]
        )

    # Media Context v2 doesn't have binary sensor entities currently

    # Mesh Monitoring Binary Sensors (Z-Wave / Zigbee)
    entities.extend([
        ZWaveMeshStatusBinarySensor(hass, entry),
        ZigbeeMeshStatusBinarySensor(hass, entry),
    ])

    # Zone Presence Trigger Sensors — Multi-Source Aggregation (PS-135)
    # Creates binary_sensor.pilotsuite_zone_presence_{zone_id}
    # and binary_sensor.pilotsuite_zone_presence_overview.
    # Powered by Core /api/v1/zone-automation/dashboard with
    # any-on source aggregation, timeout-reset, and hold-switch.
    try:
        zones: list[HabitusZoneV2] = await async_get_zones_v2(hass, entry.entry_id)
        entities.append(ZonePresenceOverviewSensor(coordinator))
        for zone in zones:
            zone_short = zone.zone_id.replace("zone:", "")
            entities.append(
                ZonePresenceTriggerSensor(
                    coordinator=coordinator,
                    zone_id=zone_short,
                    zone_name=zone.name,
                )
            )
        _LOGGER.info(
            "Zone presence trigger sensors registered: %d zones + 1 overview",
            len(zones),
        )
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Zone presence trigger sensor setup failed, continuing without",
            exc_info=True,
        )

    # UniFi context binary sensors
    entities.extend(_collect_dynamic_context_binaries())

    # Camera Context Binary Sensors (Habitus Camera Integration)
    # Auto-discover cameras from HA and create entities
    camera_entities = await _discover_camera_entities(hass)
    for cam_id, cam_name in camera_entities:
        entities.append(MotionDetectionCamera(coordinator, entry, cam_id, cam_name))
        entities.append(PresenceCamera(coordinator, entry, cam_id, cam_name))

    @callback
    def _async_handle_context_refresh(updated_entry_id: str) -> None:
        if str(updated_entry_id) != entry.entry_id:
            return
        new_entities = _collect_dynamic_context_binaries()
        if new_entities:
            async_add_entities(new_entities, True)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            SIGNAL_CONTEXT_ENTITIES_REFRESH,
            _async_handle_context_refresh,
        )
    )

    async_add_entities(entities, True)


async def _discover_camera_entities(hass: HomeAssistant) -> list[tuple[str, str]]:
    """Discover camera entities from Home Assistant."""
    from homeassistant.helpers import entity_registry
    er = entity_registry.async_get(hass)
    cameras = []

    for entity_id, entry in er.entities.items():
        if entry.domain == "camera":
            camera_name = entry.name or entry.original_name or entity_id.split(".")[-1]
            cameras.append((entity_id, camera_name))

    return cameras


class CopilotOnlineBinarySensor(CopilotBaseEntity, BinarySensorEntity):
    _attr_name = "Online"
    _attr_unique_id = "copilot_ha_online"
    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: CopilotDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        if isinstance(self.coordinator.data, dict):
            ok = self.coordinator.data.get("ok")
            if ok is None:
                return None
            return bool(ok)
        return bool(getattr(self.coordinator.data, "ok", False))


class CopilotSyncStatusBinarySensor(CopilotBaseEntity, BinarySensorEntity):
    """Binary sensor: is the integration in sync (no errors/warnings in digest)."""

    _attr_name = "Sync Status"
    _attr_unique_id = "copilot_ha_sync_status"
    _attr_icon = "mdi:check-circle-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CopilotDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def is_on(self) -> bool | None:
        entry_data = self._hass_entry_data()
        if entry_data is None:
            return None
        digest = entry_data.get("error_digest")
        if not hasattr(digest, "as_dict"):
            return None
        d = digest.as_dict()
        return d.get("errors_total", 0) == 0 and d.get("warnings_total", 0) == 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        entry_data = self._hass_entry_data()
        if entry_data is None:
            return {}
        digest = entry_data.get("error_digest")
        if not hasattr(digest, "as_dict"):
            return {}
        d = digest.as_dict()
        return {
            "errors_total": d.get("errors_total", 0),
            "warnings_total": d.get("warnings_total", 0),
            "last_error_at": d.get("last_error_at"),
            "last_warning_at": d.get("last_warning_at"),
        }

    def _hass_entry_data(self) -> dict[str, Any] | None:
        return self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)


class CoreApiHealthyBinarySensor(CopilotBaseEntity, BinarySensorEntity):
    """Binary sensor: is the Core API endpoint reachable and responding?"""

    _attr_name = "Core API Healthy"
    _attr_unique_id = "copilot_ha_core_api_healthy"
    _attr_icon = "mdi:api"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CopilotDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        if isinstance(self.coordinator.data, dict):
            return bool(self.coordinator.data.get("ok"))
        return bool(getattr(self.coordinator.data, "ok", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self.coordinator.data and isinstance(self.coordinator.data, dict):
            attrs["version"] = self.coordinator.data.get("version")
            attrs["core_url"] = self.coordinator.data.get("core_url")
        return attrs
