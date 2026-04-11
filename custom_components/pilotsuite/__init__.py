from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later

from .blueprints import async_install_blueprints
from .config_helpers import discover_reachable_core_endpoint, fetch_setup_token
from .connection_config import merged_entry_config, resolve_core_connection_from_mapping
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
    INTEGRATION_UNIQUE_ID,
    MAIN_DEVICE_IDENTIFIER,
)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
from .core.runtime import CopilotRuntime
from .entity import build_main_device_identifiers
from .services_setup import async_register_all_services

_LOGGER = logging.getLogger(__name__)

_LEGACY_CONNECTION_KEYS = ("core_url", "auth_token", "access_token", "api_token")
_LEGACY_TEXT_ENTITY_SUFFIXES = (
    "media_music_players_csv",
    "media_tv_players_csv",
    "seed_sensors_csv",
    "test_light_entity_id",
)

_MODULE_IMPORTS = {
    "legacy": (".core.modules.legacy", "LegacyModule"),
    "performance_scaling": (".core.modules.performance_scaling", "PerformanceScalingModule"),
    "events_forwarder": (".core.modules.events_forwarder", "EventsForwarderModule"),
    "history_backfill": (".core.modules.history_backfill", "HistoryBackfillModule"),
    "dev_surface": (".core.modules.dev_surface", "DevSurfaceModule"),
    "habitus_miner": (".core.modules.habitus_miner", "HabitusMinerModule"),
    "ops_runbook": (".core.modules.ops_runbook", "OpsRunbookModule"),
    "unifi_module": (".core.modules.unifi_module", "UniFiModule"),
    "brain_graph_sync": (".core.modules.brain_graph_sync", "BrainGraphSyncModule"),
    "candidate_poller": (".core.modules.candidate_poller", "CandidatePollerModule"),
    "media_zones": (".core.modules.media_context_module", "MediaContextModule"),
    "mood": (".core.modules.mood_module", "MoodModule"),
    "mood_context": (".core.modules.mood_context_module", "MoodContextModule"),
    "energy_context": (".core.modules.energy_context_module", "EnergyContextModule"),
    "network": (".core.modules.unifi_context_module", "UnifiContextModule"),
    "weather_context": (".core.modules.weather_context_module", "WeatherContextModule"),
    "knowledge_graph_sync": (".core.modules.knowledge_graph_sync", "KnowledgeGraphSyncModule"),
    "ml_context": (".core.modules.ml_context_module", "MLContextModule"),
    "camera_context": (".core.modules.camera_context_module", "CameraContextModule"),
    "quick_search": (".core.modules.quick_search", "QuickSearchModule"),
    "voice_context": (".core.modules.voice_context", "VoiceContextModule"),
    "home_alerts": (".core.modules.home_alerts_module", "HomeAlertsModule"),
    "character_module": (".core.modules.character_module", "CharacterModule"),
    "waste_reminder": (".core.modules.waste_reminder_module", "WasteReminderModule"),
    "birthday_reminder": (".core.modules.birthday_reminder_module", "BirthdayReminderModule"),
    "entity_tags": (".core.modules.entity_tags_module", "EntityTagsModule"),
    "person_tracking": (".core.modules.person_tracking_module", "PersonTrackingModule"),
    "frigate_bridge": (".core.modules.frigate_bridge", "FrigateBridgeModule"),
    "scene_module": (".core.modules.scene_module", "SceneModule"),
    "homekit_bridge": (".core.modules.homekit_bridge", "HomeKitBridgeModule"),
    "calendar_module": (".core.modules.calendar_module", "CalendarModule"),
    "licht_module": (".core.modules.licht_module", "LichtModule"),
    "helligkeit_module": (".core.modules.helligkeit_module", "HelligkeitModule"),
    "heiz_module": (".core.modules.heiz_module", "HeizModule"),
    "bewegung_module": (".core.modules.bewegung_module", "BewegungModule"),
    "praesenz_module": (".core.modules.praesenz_module", "PraesenzModule"),
    "frontend_module": (".core.modules.frontend_module", "FrontendModule"),
}

_MODULES = [
    "legacy",
    "performance_scaling",
    "events_forwarder",
    "history_backfill",
    "dev_surface",
    "habitus_miner",
    "ops_runbook",
    "unifi_module",
    "brain_graph_sync",
    "candidate_poller",
    "media_zones",
    "mood",
    "mood_context",
    "energy_context",
    "network",
    "weather_context",
    "knowledge_graph_sync",
    "ml_context",
    "camera_context",
    "quick_search",
    "voice_context",
    "home_alerts",
    "character_module",
    "waste_reminder",
    "birthday_reminder",
    "entity_tags",
    "person_tracking",
    "frigate_bridge",
    "scene_module",
    "homekit_bridge",
    "calendar_module",
    "licht_module",
    "helligkeit_module",
    "heiz_module",
    "bewegung_module",
    "praesenz_module",
    "frontend_module",
]

_LEGACY_SENSOR_UNIQUE_ID_MIGRATIONS: dict[str, str] = {
    "_automation_suggestions": "copilot_automation_suggestions",
    "_comfort_index": "copilot_comfort_index",
    "_energy_cost": "copilot_energy_cost",
    "_energy_schedule": "copilot_energy_schedule",
    "_energy_sankey_flow": "copilot_energy_sankey_flow",
    "_notifications": "copilot_notifications",
    "_home_alerts_count": "pilotsuite_home_alerts_count",
    "_home_health_score": "pilotsuite_home_health_score",
}


async def _async_migrate_entry_identity(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate entry/device identity to a stable, single-instance setup."""
    entries = hass.config_entries.async_entries(DOMAIN)
    has_primary_unique = any(
        e.entry_id != entry.entry_id and e.unique_id == INTEGRATION_UNIQUE_ID for e in entries
    )
    if not entry.unique_id and not has_primary_unique:
        hass.config_entries.async_update_entry(entry, unique_id=INTEGRATION_UNIQUE_ID)
    elif not entry.unique_id and has_primary_unique:
        _LOGGER.warning(
            "Multiple PilotSuite entries detected. Entry %s kept without unique_id to avoid collision.",
            entry.entry_id,
        )

    cfg = merged_entry_config(entry)
    identifiers = build_main_device_identifiers(cfg)
    canonical_id = next((item for item in identifiers if item[1] == MAIN_DEVICE_IDENTIFIER), None)
    if canonical_id is None:
        return

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_device(identifiers={canonical_id})
    if device is None:
        # Try legacy host:port identifier and add canonical alias when found.
        legacy_ids = {ident for ident in identifiers if ident != canonical_id}
        for legacy_id in legacy_ids:
            device = dev_reg.async_get_device(identifiers={legacy_id})
            if device is not None:
                break

    if device is None:
        # Last-resort: pick an existing PilotSuite-related device from this entry's entities.
        for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            if not entity_entry.device_id:
                continue
            probe = dev_reg.async_get(entity_entry.device_id)
            if probe is None:
                continue
            has_domain_identifier = any(ns == DOMAIN for ns, _val in probe.identifiers)
            manufacturer = str(probe.manufacturer or "").lower()
            if has_domain_identifier or manufacturer in ("pilotsuite", "ai home copilot"):
                device = probe
                break

    if device is None:
        return

    if canonical_id in device.identifiers and identifiers.issubset(set(device.identifiers)):
        return

    new_ids = set(device.identifiers)
    new_ids.update(identifiers)
    dev_reg.async_update_device(
        device.id,
        new_identifiers=new_ids,
        manufacturer="PilotSuite",
        model="Home Assistant Integration",
        name_by_user=device.name_by_user,
    )

    # Consolidate entities from legacy PilotSuite devices into the canonical hub.
    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if not entity_entry.device_id or entity_entry.device_id == device.id:
            continue
        probe = dev_reg.async_get(entity_entry.device_id)
        if probe is None:
            continue
        if not any(ns == DOMAIN for ns, _val in probe.identifiers):
            continue
        ent_reg.async_update_entity(entity_entry.entity_id, new_device_id=device.id)

    # Remove stale legacy PilotSuite devices that no longer have entities attached.
    # This keeps the device list stable across updates/migrations.
    try:
        attached_device_ids = {
            e.device_id
            for e in er.async_entries_for_config_entry(ent_reg, entry.entry_id)
            if e.device_id
        }
        remove_device = getattr(dev_reg, "async_remove_device", None)
        devices = getattr(dev_reg, "devices", None)
        removed_orphans = 0
        if callable(remove_device) and isinstance(devices, dict):
            for probe in list(devices.values()):
                if probe.id == device.id:
                    continue
                if probe.id in attached_device_ids:
                    continue
                config_entries = set(getattr(probe, "config_entries", set()) or set())
                if entry.entry_id not in config_entries:
                    continue
                identifiers = set(getattr(probe, "identifiers", set()) or set())
                if not identifiers or not any(ns == DOMAIN for ns, _ in identifiers):
                    continue
                # Be conservative: only auto-remove pure PilotSuite devices.
                if any(ns != DOMAIN for ns, _ in identifiers):
                    continue
                if remove_device(probe.id):
                    removed_orphans += 1
        if removed_orphans:
            _LOGGER.info("Removed %d orphaned PilotSuite legacy devices", removed_orphans)
    except Exception:
        _LOGGER.debug("Could not clean up orphaned legacy devices", exc_info=True)


async def _async_migrate_legacy_sensor_unique_ids(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Migrate legacy host:port based unique_ids to stable IDs."""
    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)

    for entity_entry in entries:
        current_unique_id = str(entity_entry.unique_id or "")
        if not current_unique_id:
            continue

        replacement: str | None = None
        for legacy_suffix, stable_unique_id in _LEGACY_SENSOR_UNIQUE_ID_MIGRATIONS.items():
            if current_unique_id == stable_unique_id:
                replacement = None
                break
            if current_unique_id.endswith(legacy_suffix):
                replacement = stable_unique_id
                break

        if replacement is None and current_unique_id.startswith("copilot_ha_home_alerts_"):
            category_suffix = current_unique_id.removeprefix("copilot_ha_home_alerts_")
            replacement = f"pilotsuite_home_alerts_{category_suffix}"

        if replacement is None:
            continue

        existing_entity_id = ent_reg.async_get_entity_id(
            entity_entry.domain,
            DOMAIN,
            replacement,
        )
        if existing_entity_id and existing_entity_id != entity_entry.entity_id:
            _LOGGER.warning(
                "Skipping unique_id migration for %s -> %s (already used by %s)",
                entity_entry.entity_id,
                replacement,
                existing_entity_id,
            )
            continue

        ent_reg.async_update_entity(
            entity_entry.entity_id,
            new_unique_id=replacement,
        )


async def _async_migrate_connection_config(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Normalize host/port/token from data+options into canonical keys."""
    merged = merged_entry_config(entry)
    host, port, token = resolve_core_connection_from_mapping(merged)

    new_data = dict(entry.data) if isinstance(entry.data, Mapping) else {}
    changed = False

    if new_data.get(CONF_HOST) != host:
        new_data[CONF_HOST] = host
        changed = True
    if new_data.get(CONF_PORT) != port:
        new_data[CONF_PORT] = port
        changed = True
    if str(new_data.get(CONF_TOKEN, "") or "").strip() != token:
        new_data[CONF_TOKEN] = token
        changed = True

    for legacy_key in _LEGACY_CONNECTION_KEYS:
        if legacy_key in new_data:
            new_data.pop(legacy_key, None)
            changed = True

    if not changed:
        return

    hass.config_entries.async_update_entry(entry, data=new_data)
    _LOGGER.info(
        "Normalized PilotSuite connection config for %s to %s:%s",
        entry.entry_id,
        host,
        port,
    )


async def _async_cleanup_legacy_config_text_entities(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Remove obsolete config text entities that were replaced by selectors."""
    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    removed = 0

    for entity_entry in entries:
        if entity_entry.domain != "text":
            continue
        uid = str(entity_entry.unique_id or "").lower()
        eid = str(entity_entry.entity_id or "").lower()
        if not any(uid.endswith(suffix) or eid.endswith(suffix) for suffix in _LEGACY_TEXT_ENTITY_SUFFIXES):
            continue
        ent_reg.async_remove(entity_entry.entity_id)
        removed += 1

    if removed:
        _LOGGER.info("Removed %d obsolete PilotSuite legacy text entities", removed)


async def _async_cleanup_duplicate_entities(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Remove stale duplicate entities with _2, _3, … suffix.

    When entities are re-created after a code update, HA sometimes appends _2
    to the entity_id because the old (now stale) entry still occupies the
    original entity_id with a different unique_id.  This migration detects
    such duplicates and removes the stale entry so the canonical entity gets
    the clean entity_id on next reload.
    """
    import re as _re

    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)

    # Build unique_id → entity map
    uid_map: dict[str, list] = {}
    for entity_entry in entries:
        uid = str(entity_entry.unique_id or "")
        if not uid:
            continue
        uid_map.setdefault(uid, []).append(entity_entry)

    # Detect entity_ids ending with _2, _3, … whose unique_id also exists
    # under a different (non-suffixed) entity
    _suffix_re = _re.compile(r"_(\d+)$")
    removed = 0
    for entity_entry in entries:
        eid = entity_entry.entity_id or ""
        m = _suffix_re.search(eid)
        if not m:
            continue
        # Check if a canonical entity (without suffix) exists with same unique_id
        base_eid = eid[: m.start()]
        canonical = ent_reg.async_get(base_eid)
        if canonical is None:
            # No canonical entity → this _2 entity IS the only one, rename it
            # by removing the stale original if it exists with different unique_id
            continue
        if canonical.unique_id == entity_entry.unique_id:
            # Same unique_id on both → remove the suffixed duplicate
            ent_reg.async_remove(entity_entry.entity_id)
            removed += 1
        elif canonical.config_entry_id != entry.entry_id:
            # Canonical belongs to a different integration, skip
            continue
        else:
            # Both belong to us but different unique_ids — the suffixed one
            # is the stale leftover from a previous unique_id scheme
            uid = str(entity_entry.unique_id or "")
            if uid.startswith("copilot_ha_zone_") or uid.startswith(f"{DOMAIN}_zone_"):
                ent_reg.async_remove(entity_entry.entity_id)
                removed += 1

    if removed:
        _LOGGER.info("Removed %d duplicate PilotSuite entities (with _2/_3 suffix)", removed)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    async_register_all_services(hass)

    # Register Quick Search services (best-effort)
    try:
        from .search_integration import async_register_services as register_search_services
        await register_search_services(hass)
    except Exception:
        _LOGGER.exception("Failed to register quick search services")
    
    return True


async def _get_runtime(hass: HomeAssistant) -> CopilotRuntime:
    runtime = CopilotRuntime.get(hass)

    for name, (module_path, class_name) in _MODULE_IMPORTS.items():
        if name not in runtime.registry.names():
            try:
                module = await hass.async_add_executor_job(import_module, module_path, __package__)
                cls = getattr(module, class_name)
                runtime.registry.register(name, cls)
            except Exception:
                _LOGGER.exception(
                    "Failed to register module '%s' (%s:%s) — skipping",
                    name,
                    module_path,
                    class_name,
                )
    return runtime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PilotSuite from a config entry with enhanced error handling."""
    try:
        await _async_migrate_connection_config(hass, entry)
    except Exception as e:
        _LOGGER.warning("Failed to normalize connection config: %s", e)

    # Auto-discover Core endpoint + fetch token if missing (1-Key-Flow)
    async def _discover_and_persist() -> bool:
        """Discover Core endpoint and persist to config entry. Returns True if config was updated."""
        merged = merged_entry_config(entry)
        token = str(merged.get(CONF_TOKEN, "") or "").strip()
        host = str(merged.get(CONF_HOST, "") or "").strip()
        port = int(merged.get(CONF_PORT, DEFAULT_PORT) or DEFAULT_PORT)

        # Run discovery if host is missing, default, or token is empty
        if not token or not host or host == DEFAULT_HOST:
            discovered = await discover_reachable_core_endpoint(
                hass,
                preferred_host=host or DEFAULT_HOST,
                preferred_port=port,
            )
            if discovered:
                host, port = discovered
                _LOGGER.info("Auto-discovered Core at %s:%s", host, port)

        # Fetch token if still missing
        if not token:
            token = await fetch_setup_token(hass, host or DEFAULT_HOST, port)

        # Persist discovered host/port/token into config entry
        new_data = dict(entry.data) if isinstance(entry.data, Mapping) else {}
        changed = False
        if host and new_data.get(CONF_HOST) != host:
            new_data[CONF_HOST] = host
            changed = True
        if new_data.get(CONF_PORT) != port:
            new_data[CONF_PORT] = port
            changed = True
        if token and new_data.get(CONF_TOKEN) != token:
            new_data[CONF_TOKEN] = token
            changed = True
        if changed:
            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.info(
                "PilotSuite connection config updated: %s:%s (token=%s)",
                host, port, "set" if token else "missing",
            )
        if not token:
            _LOGGER.warning(
                "No token configured and auto-fetch from Core failed — "
                "API calls will fail with 401. Configure token via "
                "Settings > Integrations > PilotSuite > Configure",
            )
        return changed

    try:
        config_updated = await _discover_and_persist()
        # If discovery failed (no config change), schedule a delayed retry.
        # Core addon may not be up yet during HA boot.
        if not config_updated:
            merged = merged_entry_config(entry)
            current_host = str(merged.get(CONF_HOST, "") or "").strip()
            if not current_host or current_host == DEFAULT_HOST:
                async def _delayed_discovery(_now=None):
                    try:
                        await _discover_and_persist()
                    except Exception:
                        _LOGGER.debug("Delayed Core discovery also failed")

                async_call_later(hass, 30, _delayed_discovery)
                _LOGGER.info("Core discovery scheduled for retry in 30s (addon may still be starting)")
    except Exception:
        _LOGGER.exception("Failed to auto-discover Core / fetch token")

    try:
        await _async_migrate_entry_identity(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to migrate entry/device identity")

    try:
        await _async_migrate_legacy_sensor_unique_ids(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to migrate legacy sensor unique_ids")

    try:
        await _async_cleanup_legacy_config_text_entities(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to clean up legacy config text entities")

    try:
        await _async_cleanup_duplicate_entities(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to clean up duplicate entities")

    try:
        await async_install_blueprints(hass)
    except Exception:
        _LOGGER.exception("Failed to install blueprints during setup")

    runtime = await _get_runtime(hass)
    try:
        await runtime.async_setup_entry(entry, modules=_MODULES)
    except Exception:
        _LOGGER.exception("Runtime setup failed")

    # Signal coordinator that modules have been loaded (suppresses spurious warnings)
    try:
        entry_store = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        coord = entry_store.get("coordinator") if isinstance(entry_store, dict) else None
        if coord is not None:
            coord.modules_ready = True
    except Exception:
        pass

    # Set up User Preference Module separately (not a CopilotModule)
    try:
        from .user_preference_module import UserPreferenceModule
        from .const import CONF_USER_PREFERENCE_ENABLED

        config = merged_entry_config(entry)
        if config.get(CONF_USER_PREFERENCE_ENABLED, False):
            user_pref_module = UserPreferenceModule(hass, entry)
            await user_pref_module.async_setup()

            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            if entry.entry_id not in hass.data[DOMAIN]:
                hass.data[DOMAIN][entry.entry_id] = {}
            hass.data[DOMAIN][entry.entry_id]["user_preference_module"] = user_pref_module
    except Exception:
        _LOGGER.exception("Failed to set up UserPreferenceModule")
    
    # Set up Multi-User Preference Learning Module (v0.8.0)
    try:
        from .multi_user_preferences import MultiUserPreferenceModule, set_mupl_module
        from .const import CONF_MUPL_ENABLED, DEFAULT_MUPL_ENABLED

        config = merged_entry_config(entry)
        if config.get(CONF_MUPL_ENABLED, DEFAULT_MUPL_ENABLED):
            mupl_module = MultiUserPreferenceModule(hass, entry)
            await mupl_module.async_setup()
            set_mupl_module(hass, entry.entry_id, mupl_module)
            _LOGGER.info("Multi-User Preference Learning Module initialized")
    except Exception:
        _LOGGER.exception("Failed to set up MultiUserPreferenceModule")

    # Set up Zone Detector with Core addon forwarding (v3.1.0)
    try:
        from .zone_detector import ZoneDetector
        entry_store = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        coord = entry_store.get("coordinator") if isinstance(entry_store, dict) else None
        api_client = getattr(coord, "api", None) if coord else None
        zone_detector = ZoneDetector(hass, entry, api_client=api_client)
        await zone_detector.async_setup()
        if isinstance(entry_store, dict):
            entry_store["zone_detector"] = zone_detector
        _LOGGER.info("ZoneDetector initialized (proactive zone-entry forwarding active)")
    except Exception:
        _LOGGER.exception("Failed to set up ZoneDetector")

    # Pattern Proposal Engine (PS-085)
    try:
        from .pattern_proposal import async_setup_pattern_proposal
        await async_setup_pattern_proposal(hass)
        _LOGGER.info("Pattern proposal engine initialized")
    except Exception:
        _LOGGER.exception("Failed to set up pattern proposal engine")

    # Auto-create Habitus Zones from HA areas (ZeroConfig, v14.4.0)
    try:
        from .zone_auto_setup import async_auto_create_habitus_zones
        zones_created = await async_auto_create_habitus_zones(hass, entry.entry_id)
        if zones_created:
            _LOGGER.info(
                "Zone auto-setup: %d Habitus Zones created from HA areas "
                "(smart aggregation: Badbereich, Gangbereich, etc.)",
                zones_created,
            )
    except Exception:
        _LOGGER.exception("Failed to auto-create Habitus Zones")

    # Register Core → HA webhook receiver for real-time push events (mood, neuron, suggestion)
    try:
        from .webhook import async_register_webhook
        entry_store = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        coord = entry_store.get("coordinator") if isinstance(entry_store, dict) else None
        if coord:
            webhook_id = await async_register_webhook(hass, entry, coord)
            if isinstance(entry_store, dict):
                entry_store["webhook_id"] = webhook_id
            _LOGGER.info("PilotSuite webhook receiver registered (id=%s)", webhook_id)
        else:
            _LOGGER.warning("Skipping webhook registration: coordinator not available")
    except Exception:
        _LOGGER.exception("Failed to register PilotSuite webhook receiver")

    # Register PilotSuite conversation agent (v3.10.0)
    try:
        from .conversation import async_setup_conversation
        await async_setup_conversation(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to set up conversation agent")

    # Auto-configure Styx as default conversation agent (v5.21.0)
    try:
        from .agent_auto_config import async_setup_agent_auto_config
        await async_setup_agent_auto_config(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to set up agent auto-config")

    # Register suggestion panel services (accept/reject/snooze)
    try:
        from .suggestion_panel import async_setup_suggestion_services
        await async_setup_suggestion_services(hass, entry.entry_id)
    except Exception:
        _LOGGER.exception("Failed to set up suggestion panel services")

    # Register Lovelace card resources from Core Add-on
    try:
        from .lovelace_resources import async_register_card_resources
        await async_register_card_resources(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to register Lovelace card resources")

    # Dashboard setup: always update wiring + ensure storage dashboard exists.
    try:
        from .dashboard_wiring import (
            async_ensure_lovelace_dashboard_wiring,
            async_ensure_storage_dashboard,
            async_hide_yaml_dashboards_from_sidebar,
        )

        # Always update YAML snippet (hides YAML dashboards from sidebar)
        wiring_state = await async_ensure_lovelace_dashboard_wiring(hass)
        # Storage-mode dashboard works immediately (no HA restart needed)
        storage_state = await async_ensure_storage_dashboard(hass)
        # Hide legacy YAML dashboards from sidebar at runtime
        await async_hide_yaml_dashboards_from_sidebar(hass)

        entry_store = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(entry_store, dict) and not entry_store.get("_dashboards_generated"):
            from .habitus_dashboard import async_generate_habitus_zones_dashboard
            from .pilotsuite_dashboard import async_generate_pilotsuite_dashboard
            await async_generate_pilotsuite_dashboard(hass, entry, notify=False)
            await async_generate_habitus_zones_dashboard(hass, entry.entry_id, notify=False)
            entry_store["_dashboards_generated"] = True

        _LOGGER.info(
            "PilotSuite dashboards setup (wiring=%s, storage=%s)",
            wiring_state,
            storage_state,
        )
    except Exception:
        _LOGGER.exception("Failed to auto-generate PilotSuite dashboards")

    # Dashboard auto-refresh on zone changes is handled by FrontendModule
    # (registered in _MODULES as "frontend_module").

    # Show onboarding notification on first setup (v3.12.0)
    try:
        entry_store = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(entry_store, dict) and not entry_store.get("_onboarding_shown"):
            from homeassistant.components.persistent_notification import async_create
            async_create(
                hass,
                title="PilotSuite ready",
                message=(
                    "Your local AI assistant **Styx** is set up and running.\n\n"
                    "**Quick start:**\n"
                    "- Open **Settings > Voice assistants** and select **PilotSuite** as your conversation agent\n"
                    "- Use the PilotSuite dashboard for Mood, Neurons, and Habitus cards\n"
                    "- Configure Habitus zones via **Settings > Integrations > PilotSuite > Configure**\n\n"
                    "All processing runs locally on your Home Assistant — no cloud required."
                ),
                notification_id=f"pilotsuite_onboarding_{entry.entry_id}",
            )
            entry_store["_onboarding_shown"] = True
    except Exception:
        _LOGGER.debug("Onboarding notification skipped", exc_info=True)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = await _get_runtime(hass)

    # Unload User Preference Module
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})

    # Dashboard refresh cleanup is handled by FrontendModule.async_unload_entry

    user_pref_module = entry_data.get("user_preference_module")
    if user_pref_module:
        await user_pref_module.async_unload()
    
    # Unload Multi-User Preference Learning Module
    from .multi_user_preferences import _MUPL_MODULE_KEY
    mupl_module = entry_data.get(_MUPL_MODULE_KEY)
    if mupl_module:
        await mupl_module.async_unload()

    # Unload Zone Detector (v3.1.0)
    zone_detector = entry_data.get("zone_detector")
    if zone_detector:
        await zone_detector.async_unload()

    # Unregister webhook receiver
    webhook_id = entry_data.get("webhook_id")
    if webhook_id:
        try:
            from .webhook import async_unregister_webhook
            await async_unregister_webhook(hass, webhook_id)
        except Exception:
            _LOGGER.exception("Failed to unregister webhook")

    # Unregister conversation agent (v3.10.0)
    try:
        from .conversation import async_unload_conversation
        await async_unload_conversation(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to unload conversation agent")

    # Unload agent auto-config services (v5.21.0)
    try:
        from .agent_auto_config import async_unload_agent_auto_config
        await async_unload_agent_auto_config(hass, entry)
    except Exception:
        _LOGGER.exception("Failed to unload agent auto-config")

    result = await runtime.async_unload_entry(entry, modules=_MODULES)
    return bool(result)
