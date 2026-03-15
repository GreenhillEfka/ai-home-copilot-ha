"""PilotSuite Frontend Entities — Dashboard view toggles + rebuild button."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory

from .const import DOMAIN, INTEGRATION_UNIQUE_ID
from .entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

# View definitions: (path, label_de, icon)
DASHBOARD_VIEWS = [
    ("haushalt", "Haushalt", "mdi:home-heart"),
    ("zonen", "Zonen", "mdi:map-marker-radius"),
    ("automation", "Automation", "mdi:robot"),
    ("energie", "Energie", "mdi:lightning-bolt"),
    ("musik", "Musik", "mdi:speaker-group"),
    ("module", "Module", "mdi:puzzle"),
    ("ki", "KI", "mdi:brain"),
    ("chat", "Chat", "mdi:chat-outline"),
]


class DashboardViewToggleSwitch(CopilotBaseEntity, SwitchEntity):
    """Switch to enable/disable a dashboard view."""

    _attr_has_entity_name = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        view_path: str,
        view_label: str,
        view_icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._view_path = view_path
        self._attr_unique_id = f"{INTEGRATION_UNIQUE_ID}_dashboard_view_{view_path}"
        self._attr_name = f"PilotSuite Dashboard: {view_label}"
        self._attr_icon = view_icon

    def _get_frontend_module(self):
        entry_store = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if isinstance(entry_store, dict):
            return entry_store.get("frontend_module")
        return None

    @property
    def is_on(self) -> bool:
        mod = self._get_frontend_module()
        if mod is None:
            return True
        return mod.get_view_states().get(self._view_path, True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        mod = self._get_frontend_module()
        if mod:
            await mod.async_set_view_enabled(self._view_path, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        mod = self._get_frontend_module()
        if mod:
            await mod.async_set_view_enabled(self._view_path, False)
        self.async_write_ha_state()


class DashboardRefreshButton(CopilotBaseEntity, ButtonEntity):
    """Button to manually rebuild the PilotSuite dashboard."""

    _attr_has_entity_name = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: Any, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{INTEGRATION_UNIQUE_ID}_dashboard_rebuild"
        self._attr_name = "PilotSuite Dashboard Rebuild"
        self._attr_icon = "mdi:view-dashboard-edit"

    async def async_press(self) -> None:
        entry_store = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if isinstance(entry_store, dict):
            mod = entry_store.get("frontend_module")
            if mod:
                await mod.async_rebuild_dashboard("button_press")


def create_frontend_entities(
    coordinator: Any,
    entry: ConfigEntry,
) -> dict[str, list]:
    """Create all frontend module entities.

    Returns {"switch": [...], "button": [...]}.
    """
    switches = [
        DashboardViewToggleSwitch(coordinator, entry, path, label, icon)
        for path, label, icon in DASHBOARD_VIEWS
    ]
    buttons = [
        DashboardRefreshButton(coordinator, entry),
    ]
    return {"switch": switches, "button": buttons}
