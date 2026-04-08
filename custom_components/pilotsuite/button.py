"""PilotSuite Buttons (wrapper for backward compatibility)."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_TEST_LIGHT,
    DEFAULT_TEST_LIGHT,
    DOMAIN,
    SIGNAL_FRONTEND_MODULE_READY,
)
from .entity_profile import is_full_entity_profile
from .habitus_zones_entities_v2 import (
    HabitusZonesV2ValidateButton,
    HabitusZonesV2SyncGraphButton,
    HabitusZonesV2ReloadButton,
)
from .button_camera import (
    CopilotGenerateCameraDashboardButton,
    CopilotDownloadCameraDashboardButton,
)
from .button_tag_registry import CopilotTagRegistrySyncLabelsNowButton
from .button_update_rollback import CopilotUpdateRollbackReportButton
from .button_update_check import (
    CheckHAUpdateButton,
    CheckCoreUpdateButton,
    PilotSuiteHAVersionSensor,
    PilotSuiteCoreVersionSensor,
)
from .button_media import (
    VolumeUpButton,
    VolumeDownButton,
    VolumeMuteButton,
    ClearOverridesButton,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not available for %s, skipping button setup", entry.entry_id)
        return
    cfg = entry.data | entry.options

    if not is_full_entity_profile(entry):
        # Create version sensors for update check buttons.
        ha_ver_sensor = PilotSuiteHAVersionSensor(coordinator)
        core_ver_sensor = PilotSuiteCoreVersionSensor(coordinator)
        # Store sensors in hass.data for sensor platform to pick up.
        data["_ha_version_sensor"] = ha_ver_sensor
        data["_core_version_sensor"] = core_ver_sensor
        async_add_entities(
            [
                CopilotReloadConfigEntryButton(coordinator, entry.entry_id),
                CopilotPingCoreButton(coordinator, entry),
                HabitusZonesV2ValidateButton(coordinator, entry),
                CopilotGenerateHabitusDashboardButton(coordinator, entry),
                CopilotDownloadHabitusDashboardButton(coordinator, entry),
                CopilotGeneratePilotSuiteDashboardButton(coordinator, entry),
                CopilotDownloadPilotSuiteDashboardButton(coordinator, entry),
                CheckHAUpdateButton(coordinator, ha_ver_sensor),
                CheckCoreUpdateButton(coordinator, core_ver_sensor),
            ],
            True,
        )
        return
    
    # Create version sensors for update check buttons.
    ha_ver_sensor = PilotSuiteHAVersionSensor(coordinator)
    core_ver_sensor = PilotSuiteCoreVersionSensor(coordinator)
    data["_ha_version_sensor"] = ha_ver_sensor
    data["_core_version_sensor"] = core_ver_sensor

    entities = [
        # System buttons
        CopilotGenerateOverviewButton(coordinator),
        CopilotDownloadOverviewButton(coordinator),
        CopilotGenerateInventoryButton(coordinator),
        CopilotSystemHealthReportButton(coordinator),
        CopilotGenerateConfigSnapshotButton(coordinator, entry),
        CopilotDownloadConfigSnapshotButton(coordinator),
        CopilotReloadConfigEntryButton(coordinator, entry.entry_id),
        CopilotGenerateHabitusDashboardButton(coordinator, entry),
        CopilotDownloadHabitusDashboardButton(coordinator, entry),
        CopilotGeneratePilotSuiteDashboardButton(coordinator, entry),
        CopilotDownloadPilotSuiteDashboardButton(coordinator, entry),
        # Safety buttons
        CopilotSafetyBackupCreateButton(coordinator, entry),
        CopilotSafetyBackupStatusButton(coordinator, entry),
        # Debug buttons
        CopilotToggleLightButton(
            coordinator, cfg.get(CONF_TEST_LIGHT, DEFAULT_TEST_LIGHT)
        ),
        CopilotCreateDemoSuggestionButton(coordinator, entry.entry_id),
        CopilotAnalyzeLogsButton(coordinator),
        CopilotRollbackLastFixButton(coordinator),
        CopilotDevLogTestPushButton(coordinator, entry),
        CopilotDevLogPushLatestButton(coordinator, entry),
        CopilotDevLogsFetchButton(coordinator, entry),
        CopilotCoreCapabilitiesFetchButton(coordinator, entry),
        CopilotCoreEventsFetchButton(coordinator, entry),
        CopilotCoreGraphStateFetchButton(coordinator, entry),
        CopilotCoreGraphCandidatesPreviewButton(coordinator, entry),
        CopilotCoreGraphCandidatesOfferButton(coordinator, entry),
        CopilotPublishBrainGraphVizButton(coordinator, entry),
        CopilotPublishBrainGraphPanelButton(coordinator, entry),
        CopilotForwarderStatusButton(coordinator, entry),
        CopilotHaErrorsFetchButton(coordinator, entry),
        CopilotPingCoreButton(coordinator, entry),
        CopilotEnableDebug30mButton(coordinator, entry.entry_id),
        CopilotDisableDebugButton(coordinator, entry.entry_id),
        CopilotClearErrorDigestButton(coordinator, entry.entry_id),
        CopilotClearAllLogsButton(coordinator, entry.entry_id),
        # Habitus Zones v2 buttons
        HabitusZonesV2ValidateButton(coordinator, entry),
        HabitusZonesV2SyncGraphButton(coordinator, entry),
        HabitusZonesV2ReloadButton(coordinator, entry),
        CopilotTagRegistrySyncLabelsNowButton(coordinator),
        CopilotUpdateRollbackReportButton(coordinator),
        # Brain dashboard summary
        CopilotBrainDashboardSummaryButton(coordinator, entry),
        # Update check buttons
        CheckHAUpdateButton(coordinator, ha_ver_sensor),
        CheckCoreUpdateButton(coordinator, core_ver_sensor),
        # Camera Dashboard buttons
        CopilotGenerateCameraDashboardButton(hass, entry),
        CopilotDownloadCameraDashboardButton(hass, entry),
    ]

    # Media Context v2 button entities
    media_coordinator_v2 = data.get("media_coordinator_v2") if isinstance(data, dict) else None
    if media_coordinator_v2 is not None:
        entities.extend([
            VolumeUpButton(media_coordinator_v2),
            VolumeDownButton(media_coordinator_v2),
            VolumeMuteButton(media_coordinator_v2),
            ClearOverridesButton(media_coordinator_v2),
        ])

    async_add_entities(entities, True)

    # Zone scene capture buttons (v14.2.0)
    try:
        from .autonomy_entities import create_zone_autonomy_entities, ZoneSceneCaptureButton
        from .habitus_zones_store_v2 import async_get_zones_v2
        zones = await async_get_zones_v2(hass, entry.entry_id)
        zone_list = [{"zone_id": z.zone_id, "name": getattr(z, "name_de", None) or z.name} for z in zones]
        scene_buttons = [e for e in create_zone_autonomy_entities(coordinator, zone_list) if isinstance(e, ZoneSceneCaptureButton)]
        if scene_buttons:
            async_add_entities(scene_buttons, True)
    except Exception:
        _LOGGER.debug("Zone scene buttons skipped (zones not configured)")

    # HomeKit per-zone toggle buttons (v14.4.2)
    try:
        from .homekit_entities import async_create_homekit_buttons
        hk_buttons = await async_create_homekit_buttons(hass, entry, coordinator)
        if hk_buttons:
            async_add_entities(hk_buttons, True)
    except Exception:
        _LOGGER.debug("HomeKit toggle buttons skipped")

    # Dashboard rebuild button (if frontend_module already loaded)
    try:
        frontend_mod = data.get("frontend_module") if isinstance(data, dict) else None
        if frontend_mod is not None:
            from .frontend_entities import DashboardRefreshButton
            async_add_entities([DashboardRefreshButton(coordinator, entry)], True)
    except Exception:
        _LOGGER.debug("Dashboard rebuild button skipped")

    # Lazy creation via dispatcher signal
    @callback
    def _on_frontend_ready(ready_entry_id: str) -> None:
        if ready_entry_id != entry.entry_id:
            return
        try:
            from .frontend_entities import DashboardRefreshButton
            async_add_entities([DashboardRefreshButton(coordinator, entry)], True)
        except Exception:
            _LOGGER.debug("Failed to add dashboard rebuild button on signal")

    async_dispatcher_connect(hass, SIGNAL_FRONTEND_MODULE_READY, _on_frontend_ready)


# Re-export all button classes
# button_debug.py is the canonical source for debug/dev buttons
from .button_safety_backup import (
    CopilotSafetyBackupCreateButton,
    CopilotSafetyBackupStatusButton,
)
from .button_system import (
    CopilotGenerateOverviewButton,
    CopilotDownloadOverviewButton,
    CopilotGenerateInventoryButton,
    CopilotSystemHealthReportButton,
    CopilotGenerateConfigSnapshotButton,
    CopilotDownloadConfigSnapshotButton,
    CopilotReloadConfigEntryButton,
    CopilotGenerateHabitusDashboardButton,
    CopilotDownloadHabitusDashboardButton,
    CopilotGeneratePilotSuiteDashboardButton,
    CopilotDownloadPilotSuiteDashboardButton,
)
from .button_debug import (
    CopilotToggleLightButton,
    CopilotCreateDemoSuggestionButton,
    CopilotAnalyzeLogsButton,
    CopilotRollbackLastFixButton,
    CopilotDevLogTestPushButton,
    CopilotDevLogPushLatestButton,
    CopilotDevLogsFetchButton,
    CopilotCoreCapabilitiesFetchButton,
    CopilotCoreEventsFetchButton,
    CopilotCoreGraphStateFetchButton,
    CopilotCoreGraphCandidatesPreviewButton,
    CopilotCoreGraphCandidatesOfferButton,
    CopilotPublishBrainGraphVizButton,
    CopilotPublishBrainGraphPanelButton,
    CopilotForwarderStatusButton,
    CopilotHaErrorsFetchButton,
    CopilotPingCoreButton,
    CopilotEnableDebug30mButton,
    CopilotDisableDebugButton,
    CopilotClearErrorDigestButton,
    CopilotClearAllLogsButton,
    CopilotBrainDashboardSummaryButton,
)
