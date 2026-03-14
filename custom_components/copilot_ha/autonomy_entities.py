"""PilotSuite — Autonomy Zone Control Entities (v14.2.0)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback

from .entity import CopilotBaseEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Module IDs that can be controlled per zone
AUTONOMY_MODULES = [
    ("licht", "Licht", "mdi:lightbulb-group"),
    ("musik", "Musik", "mdi:music"),
    ("bewegung", "Bewegung", "mdi:motion-sensor"),
    ("mood", "Stimmung", "mdi:emoticon"),
    ("klima", "Klima", "mdi:thermostat"),
    ("rollladen", "Rollladen", "mdi:blinds"),
]

MODULE_STATES = ["active", "learning", "off"]
MODULE_STATE_LABELS = {
    "active": "Aktiv",
    "learning": "Lernend",
    "off": "Aus",
}


class ZoneModuleStateSelect(CopilotBaseEntity, SelectEntity):
    """Per-zone module state control (active/learning/off)."""

    _attr_has_entity_name = False
    _attr_options = MODULE_STATES

    def __init__(self, coordinator, zone_id: str, zone_name: str, module_id: str, module_name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._module_id = module_id
        self._attr_unique_id = f"copilot_ha_zone_{zone_id}_{module_id}_state"
        self._attr_name = f"PilotSuite {zone_name} {module_name}"
        self._attr_icon = icon
        self._attr_current_option = "active"

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        zone_module_states = data.get("zone_module_states", {})
        zone_states = zone_module_states.get(self._zone_id, {})
        state = zone_states.get(self._module_id, "active")
        if state in MODULE_STATES:
            self._attr_current_option = state
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Set zone module state via Core API."""
        if option not in MODULE_STATES:
            return
        coordinator = self.coordinator
        if hasattr(coordinator, "async_set_zone_module_state"):
            result = await coordinator.async_set_zone_module_state(
                self._zone_id, self._module_id, option
            )
            if not isinstance(result, dict) or not result.get("ok"):
                _LOGGER.warning(
                    "Failed to set module state %s/%s to %s: %s",
                    self._zone_id, self._module_id, option, result,
                )
                return
        self._attr_current_option = option
        self.async_write_ha_state()


class ZoneSceneCaptureButton(CopilotBaseEntity, ButtonEntity):
    """Button to capture current zone state as scene."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:camera-plus"

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_unique_id = f"copilot_ha_zone_{zone_id}_scene_capture"
        self._attr_name = f"PilotSuite {zone_name} Szene Speichern"

    async def async_press(self) -> None:
        """Capture current zone state as scene."""
        import time
        scene_name = f"{self._zone_name} Szene {int(time.time())}"
        coordinator = self.coordinator
        if hasattr(coordinator, "async_capture_zone_scene"):
            result = await coordinator.async_capture_zone_scene(self._zone_id, scene_name)
            if result.get("ok"):
                _LOGGER.info("Zone scene captured: %s in %s", scene_name, self._zone_id)
            else:
                _LOGGER.warning("Failed to capture zone scene in %s", self._zone_id)


def create_zone_autonomy_entities(coordinator, zones: list[dict]) -> list:
    """Create per-zone autonomy control entities.

    Args:
        coordinator: The data coordinator
        zones: List of zone dicts with zone_id and name keys

    Returns:
        List of entity instances
    """
    entities = []
    for zone in zones:
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("name", zone_id)
        if not zone_id:
            continue

        # Module state selects
        for module_id, module_name, icon in AUTONOMY_MODULES:
            entities.append(ZoneModuleStateSelect(
                coordinator, zone_id, zone_name, module_id, module_name, icon
            ))

        # Scene capture button
        entities.append(ZoneSceneCaptureButton(coordinator, zone_id, zone_name))

    return entities
