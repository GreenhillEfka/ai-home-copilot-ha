"""System control buttons for PilotSuite."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .button_base import CopilotButtonBase
from .inventory import async_generate_ha_overview
from .inventory_publish import async_publish_last_overview
from .inventory_kernel import async_generate_and_publish_inventory
from .systemhealth_report import async_generate_and_publish_systemhealth_report
from .config_snapshot import async_generate_config_snapshot, async_publish_last_config_snapshot
from .habitus_dashboard import async_generate_habitus_zones_dashboard, async_publish_last_habitus_dashboard
from .pilotsuite_dashboard import async_generate_pilotsuite_dashboard, async_publish_last_pilotsuite_dashboard


class CopilotGenerateOverviewButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_name = "PilotSuite generate HA overview"
    _attr_unique_id = "copilot_ha_generate_ha_overview"
    _attr_icon = "mdi:map-search"

    async def async_press(self) -> None:
        await async_generate_ha_overview(self.hass)


class CopilotDownloadOverviewButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_name = "PilotSuite download HA overview"
    _attr_unique_id = "copilot_ha_download_ha_overview"
    _attr_icon = "mdi:download"

    async def async_press(self) -> None:
        await async_publish_last_overview(self.hass)


class CopilotGenerateInventoryButton(CopilotButtonBase):
    _attr_entity_registry_enabled_default = False
    _attr_name = "PilotSuite generate inventory"
    _attr_unique_id = "copilot_ha_generate_inventory"
    _attr_icon = "mdi:clipboard-list"

    async def async_press(self) -> None:
        await async_generate_and_publish_inventory(self.hass)


class CopilotSystemHealthReportButton(CopilotButtonBase):
    _attr_name = "SystemHealth report"
    _attr_unique_id = "copilot_ha_systemhealth_report"
    _attr_icon = "mdi:stethoscope"

    async def async_press(self) -> None:
        await self._press_with_notification(
            async_generate_and_publish_systemhealth_report(self.hass),
            title="PilotSuite SystemHealth",
            notification_id="copilot_ha_systemhealth",
            error_prefix="Failed to generate SystemHealth report",
        )


class CopilotGenerateConfigSnapshotButton(CopilotButtonBase):
    _attr_name = "PilotSuite generate config snapshot"
    _attr_unique_id = "copilot_ha_generate_config_snapshot"
    _attr_icon = "mdi:content-save-cog"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry)

    async def async_press(self) -> None:
        await async_generate_config_snapshot(self.hass, self._entry)


class CopilotDownloadConfigSnapshotButton(CopilotButtonBase):
    _attr_name = "PilotSuite download config snapshot"
    _attr_unique_id = "copilot_ha_download_config_snapshot"
    _attr_icon = "mdi:download"

    async def async_press(self) -> None:
        await self._press_with_notification(
            async_publish_last_config_snapshot(self.hass),
            title="PilotSuite config snapshot",
            notification_id="copilot_ha_config_snapshot",
            error_prefix="Failed to publish config snapshot",
        )


class CopilotReloadConfigEntryButton(CopilotButtonBase):
    _attr_name = "PilotSuite reload"
    _attr_unique_id = "copilot_ha_reload_config_entry"
    _attr_icon = "mdi:reload"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id

    async def async_press(self) -> None:
        await self.hass.config_entries.async_reload(self._entry_id)


class CopilotGenerateHabitusDashboardButton(CopilotButtonBase):
    _attr_name = "PilotSuite generate habitus dashboard"
    _attr_unique_id = "copilot_ha_generate_habitus_dashboard"
    _attr_icon = "mdi:view-dashboard-outline"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry)

    async def async_press(self) -> None:
        await async_generate_habitus_zones_dashboard(self.hass, self._entry.entry_id)


class CopilotDownloadHabitusDashboardButton(CopilotButtonBase):
    _attr_name = "PilotSuite download habitus dashboard"
    _attr_unique_id = "copilot_ha_download_habitus_dashboard"
    _attr_icon = "mdi:download"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry)

    async def async_press(self) -> None:
        await self._press_with_notification(
            async_publish_last_habitus_dashboard(self.hass),
            title="PilotSuite Habitus dashboard",
            notification_id="copilot_ha_habitus_dashboard_download",
            error_prefix="Failed to publish habitus dashboard",
        )


class CopilotGeneratePilotSuiteDashboardButton(CopilotButtonBase):
    _attr_name = "PilotSuite generate PilotSuite dashboard"
    _attr_unique_id = "copilot_ha_generate_pilotsuite_dashboard"
    _attr_icon = "mdi:view-dashboard"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry)

    async def async_press(self) -> None:
        await async_generate_pilotsuite_dashboard(self.hass, self._entry)


class CopilotDownloadPilotSuiteDashboardButton(CopilotButtonBase):
    _attr_name = "PilotSuite download PilotSuite dashboard"
    _attr_unique_id = "copilot_ha_download_pilotsuite_dashboard"
    _attr_icon = "mdi:download"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry)

    async def async_press(self) -> None:
        await self._press_with_notification(
            async_publish_last_pilotsuite_dashboard(self.hass),
            title="PilotSuite PilotSuite dashboard",
            notification_id="copilot_ha_pilotsuite_dashboard_download",
            error_prefix="Failed to publish PilotSuite dashboard",
        )
