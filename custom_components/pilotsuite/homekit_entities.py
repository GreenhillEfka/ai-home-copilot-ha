"""HomeKit per-zone entities: toggle button, QR sensor, setup info.

Creates entities that allow enabling/disabling HomeKit per Habitus zone
and display the QR code + setup code for Apple Home pairing.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .connection_config import resolve_core_connection
from .const import DOMAIN
from .coordinator import CopilotDataUpdateCoordinator
from .entity import CopilotBaseEntity
from .core.modules.homekit_bridge import (
    SIGNAL_HOMEKIT_ZONE_TOGGLED,
    get_homekit_bridge,
)

_LOGGER = logging.getLogger(__name__)


class HomeKitZoneToggleButton(CopilotBaseEntity, ButtonEntity):
    """Button to toggle HomeKit exposure for a Habitus zone."""

    _attr_icon = "mdi:apple"

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        entry: ConfigEntry,
        zone_id: str,
        zone_name: str,
        entity_ids: list[str],
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._entity_ids = entity_ids
        self._attr_has_entity_name = False
        self._attr_name = f"PilotSuite HomeKit — {zone_name}"
        self._attr_unique_id = f"pilotsuite_homekit_toggle_{zone_id}"

    async def async_press(self) -> None:
        """Toggle HomeKit for this zone."""
        bridge = get_homekit_bridge(self.hass, self._entry.entry_id)
        if not bridge:
            _LOGGER.warning("HomeKit bridge module not available")
            return

        if bridge.is_zone_enabled(self._zone_id):
            await bridge.async_disable_zone(self._zone_id)
            _LOGGER.info("HomeKit disabled for zone %s", self._zone_name)
        else:
            await bridge.async_enable_zone(
                self._zone_id, self._zone_name, self._entity_ids
            )
            _LOGGER.info("HomeKit enabled for zone %s", self._zone_name)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bridge = get_homekit_bridge(self.hass, self._entry.entry_id)
        if not bridge:
            return {"homekit_enabled": False}

        enabled = bridge.is_zone_enabled(self._zone_id)
        setup_info = bridge.get_zone_setup_info(self._zone_id)
        host, port, _token = resolve_core_connection(self._entry)

        attrs: dict[str, Any] = {
            "homekit_enabled": enabled,
            "zone_id": self._zone_id,
            "zone_name": self._zone_name,
            "entity_count": len(self._entity_ids),
        }

        if enabled and setup_info:
            attrs["setup_code"] = setup_info.get("setup_code", "")
            attrs["serial"] = setup_info.get("serial", "")
            attrs["manufacturer"] = setup_info.get("manufacturer", "PilotSuite")
            attrs["model"] = setup_info.get("model", "Styx HomeKit Bridge")
            attrs["qr_svg_url"] = f"http://{host}:{port}/api/v1/homekit/qr/{self._zone_id}.svg"
            attrs["qr_png_url"] = f"http://{host}:{port}/api/v1/homekit/qr/{self._zone_id}.png"

        return attrs


class HomeKitZoneQRSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing HomeKit setup code + QR URL for a zone.

    The state is the setup code (XXX-XX-XXX).
    Attributes contain QR image URLs and device info.
    """

    _attr_icon = "mdi:qrcode"

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        entry: ConfigEntry,
        zone_id: str,
        zone_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_has_entity_name = False
        self._attr_name = f"PilotSuite HomeKit QR — {zone_name}"
        self._attr_unique_id = f"pilotsuite_homekit_qr_{zone_id}"

    @property
    def native_value(self) -> str:
        """Return the setup code as state."""
        bridge = get_homekit_bridge(self.hass, self._entry.entry_id)
        if not bridge or not bridge.is_zone_enabled(self._zone_id):
            return "nicht aktiv"

        setup_info = bridge.get_zone_setup_info(self._zone_id)
        return setup_info.get("setup_code", "---")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bridge = get_homekit_bridge(self.hass, self._entry.entry_id)
        if not bridge:
            return {}

        enabled = bridge.is_zone_enabled(self._zone_id)
        setup_info = bridge.get_zone_setup_info(self._zone_id)
        host, port, _token = resolve_core_connection(self._entry)

        attrs: dict[str, Any] = {
            "homekit_enabled": enabled,
            "zone_id": self._zone_id,
            "zone_name": self._zone_name,
        }

        if enabled:
            attrs["setup_code"] = setup_info.get("setup_code", "")
            attrs["homekit_uri"] = setup_info.get("homekit_uri", "")
            attrs["qr_svg_url"] = f"http://{host}:{port}/api/v1/homekit/qr/{self._zone_id}.svg"
            attrs["qr_png_url"] = f"http://{host}:{port}/api/v1/homekit/qr/{self._zone_id}.png"
            attrs["serial"] = setup_info.get("serial", "")
            attrs["manufacturer"] = setup_info.get("manufacturer", "PilotSuite")
            attrs["model"] = setup_info.get("model", "Styx HomeKit Bridge")
            # Apple Home display name
            attrs["apple_home_name"] = f"{self._zone_name} by Styx"

        return attrs


async def _load_homekit_zones(hass: HomeAssistant, entry_id: str) -> list:
    """Load active habitus zones for HomeKit entity creation."""
    try:
        from .habitus_zones_store_v2 import async_get_zones_v2
        zones = await async_get_zones_v2(hass, entry_id)
        return [z for z in zones if z.current_state != "disabled"]
    except Exception:
        _LOGGER.debug("Could not load zones for HomeKit entities")
        return []


async def async_create_homekit_buttons(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: CopilotDataUpdateCoordinator,
) -> list[HomeKitZoneToggleButton]:
    """Create HomeKit toggle buttons for each habitus zone.

    Called from button.py async_setup_entry.
    """
    zones = await _load_homekit_zones(hass, entry.entry_id)
    buttons: list[HomeKitZoneToggleButton] = []
    for zone in zones:
        entity_ids = list(zone.entity_ids) if zone.entity_ids else []
        buttons.append(
            HomeKitZoneToggleButton(
                coordinator, entry,
                zone.zone_id, zone.name, entity_ids,
            )
        )
    if buttons:
        _LOGGER.info("Created %d HomeKit toggle buttons", len(buttons))
    return buttons


async def async_create_homekit_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: CopilotDataUpdateCoordinator,
) -> list[HomeKitZoneQRSensor]:
    """Create HomeKit QR sensors for each habitus zone.

    Called from sensor.py async_setup_entry.
    """
    zones = await _load_homekit_zones(hass, entry.entry_id)
    sensors: list[HomeKitZoneQRSensor] = []
    for zone in zones:
        sensors.append(
            HomeKitZoneQRSensor(
                coordinator, entry,
                zone.zone_id, zone.name,
            )
        )
    if sensors:
        _LOGGER.info("Created %d HomeKit QR sensors", len(sensors))
    return sensors


async def async_create_homekit_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: CopilotDataUpdateCoordinator,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create HomeKit QR sensor entities for each habitus zone.

    Called from sensor.py async_setup_entry.
    NOTE: Only creates QR sensors here. Toggle buttons are in button.py.
    """
    sensors = await async_create_homekit_sensors(hass, entry, coordinator)
    if sensors:
        async_add_entities(sensors, update_before_add=False)
