from __future__ import annotations

from .button_base import CopilotButtonBase


class CopilotEnableDebug30mButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = None
    _attr_name = "PilotSuite enable debug for 30m"
    _attr_unique_id = "copilot_ha_enable_debug_30m"
    _attr_icon = "mdi:bug"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id

    async def async_press(self) -> None:
        await self._call_service(
            "enable_debug_for",
            {"entry_id": self._entry_id, "minutes": 30},
        )
        self._notify(
            "Debug enabled for 30 minutes (auto-disable).",
            title="PilotSuite debug",
            notification_id="copilot_ha_debug",
        )


class CopilotDisableDebugButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = None
    _attr_name = "PilotSuite disable debug"
    _attr_unique_id = "copilot_ha_disable_debug"
    _attr_icon = "mdi:bug-off"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id

    async def async_press(self) -> None:
        await self._call_service(
            "disable_debug",
            {"entry_id": self._entry_id},
        )
        self._notify(
            "Debug disabled.",
            title="PilotSuite debug",
            notification_id="copilot_ha_debug",
        )


class CopilotClearErrorDigestButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = None
    _attr_name = "PilotSuite clear error digest"
    _attr_unique_id = "copilot_ha_clear_error_digest"
    _attr_icon = "mdi:broom"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id

    async def async_press(self) -> None:
        await self._call_service(
            "clear_error_digest",
            {"entry_id": self._entry_id},
        )
        self._notify(
            "Error digest cleared.",
            title="PilotSuite dev surface",
            notification_id="copilot_ha_dev_surface",
        )


class CopilotClearAllLogsButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = None
    _attr_name = "PilotSuite clear all logs"
    _attr_unique_id = "copilot_ha_clear_all_logs"
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id

    async def async_press(self) -> None:
        await self._call_service(
            "clear_all_logs",
            {"entry_id": self._entry_id},
        )
        self._notify(
            "All logs cleared (devlog + error digest).",
            title="PilotSuite dev surface",
            notification_id="copilot_ha_dev_surface",
        )
