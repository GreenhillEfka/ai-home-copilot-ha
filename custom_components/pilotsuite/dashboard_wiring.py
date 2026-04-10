"""Lovelace dashboard wiring helper for PilotSuite.

This module keeps dashboard YAML files and Lovelace wiring aligned:
- writes a stable include snippet file under `pilotsuite-styx/`
- auto-appends a minimal Lovelace block only when `configuration.yaml` has no `lovelace:` section
- falls back to a clear manual instruction when merge is required
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from .const import LEGACY_DASHBOARD_DIR, PRIMARY_DASHBOARD_DIR

try:
    from homeassistant.components import persistent_notification
    from homeassistant.core import HomeAssistant
except ImportError:  # pragma: no cover - test fallback when HA runtime is not installed
    HomeAssistant = Any  # type: ignore[misc,assignment]

    class _PersistentNotificationStub:
        @staticmethod
        def async_create(*_args: Any, **_kwargs: Any) -> None:
            return None

    persistent_notification = _PersistentNotificationStub()  # type: ignore[assignment]


_LOGGER = logging.getLogger(__name__)

SNIPPET_REL_PATH = f"{PRIMARY_DASHBOARD_DIR}/lovelace_pilotsuite_dashboards.yaml"
_LEGACY_SNIPPET_REL_PATH = f"{LEGACY_DASHBOARD_DIR}/lovelace_pilotsuite_dashboards.yaml"
_DASHBOARD_FILE_MARKERS = (
    f"{PRIMARY_DASHBOARD_DIR}/pilotsuite_dashboard_latest.yaml",
    f"{PRIMARY_DASHBOARD_DIR}/habitus_zones_dashboard_latest.yaml",
)
_LEGACY_DASHBOARD_FILE_MARKERS = (
    f"{LEGACY_DASHBOARD_DIR}/pilotsuite_dashboard_latest.yaml",
    f"{LEGACY_DASHBOARD_DIR}/habitus_zones_dashboard_latest.yaml",
)
_AUTOMATED_BLOCK_MARKER = "# PilotSuite dashboard wiring (managed by copilot_ha)"
_NOTIFICATION_ID = "copilot_ha_dashboard_wiring"


def _snippet_content() -> str:
    # Hide YAML dashboards from sidebar — storage-mode is the primary dashboard now.
    return (
        "copilot-pilotsuite:\n"
        "  mode: yaml\n"
        "  title: \"PilotSuite (Legacy)\"\n"
        "  icon: mdi:robot-outline\n"
        "  show_in_sidebar: false\n"
        f"  filename: \"{PRIMARY_DASHBOARD_DIR}/pilotsuite_dashboard_latest.yaml\"\n"
        "\n"
        "copilot-habitus-zones:\n"
        "  mode: yaml\n"
        "  title: \"PilotSuite Zones (Legacy)\"\n"
        "  icon: mdi:layers-outline\n"
        "  show_in_sidebar: false\n"
        f"  filename: \"{PRIMARY_DASHBOARD_DIR}/habitus_zones_dashboard_latest.yaml\"\n"
    )


def _include_block() -> str:
    return (
        f"{_AUTOMATED_BLOCK_MARKER}\n"
        "lovelace:\n"
        f"  dashboards: !include {SNIPPET_REL_PATH}\n"
    )


def _manual_help_message(config_path: Path) -> str:
    return (
        "PilotSuite hat die Dashboard-Dateien automatisch erzeugt, "
        "aber deine `configuration.yaml` enthaelt bereits einen `lovelace:`-Block.\n\n"
        "Bitte ergaenze dort **unter `lovelace:`**:\n"
        f"```\n"
        f"dashboards: !include {SNIPPET_REL_PATH}\n"
        f"```\n\n"
        f"Die Include-Datei wurde erstellt:\n`{config_path.parent / SNIPPET_REL_PATH}`\n\n"
        "Alternativ kannst du die Dashboard-Definitionen direkt einfuegen:\n"
        "```yaml\n"
        "dashboards:\n"
        f"{_snippet_content()}"
        "```\n\n"
        "Danach Home Assistant neu starten."
    )


def _has_lovelace_root(config_text: str) -> bool:
    return bool(re.search(r"(?m)^\s*lovelace\s*:", config_text))


def _is_dashboard_wired(config_text: str) -> bool:
    lowered = config_text.lower()
    if SNIPPET_REL_PATH.lower() in lowered or _LEGACY_SNIPPET_REL_PATH.lower() in lowered:
        return True
    if all(marker.lower() in lowered for marker in _DASHBOARD_FILE_MARKERS):
        return True
    return all(marker.lower() in lowered for marker in _LEGACY_DASHBOARD_FILE_MARKERS)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    with path.open("a", encoding="utf-8") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        if current and not current.endswith("\n\n"):
            handle.write("\n")
        handle.write(content)


def _merge_dashboards_into_existing_lovelace(config_text: str) -> tuple[str, bool]:
    """Try to inject missing PilotSuite dashboards into an existing lovelace:dashboards map.

    Returns (new_text, changed). If no safe merge is possible, changed=False.
    """
    lines = config_text.splitlines()
    if not lines:
        return config_text, False

    lovelace_idx: int | None = None
    lovelace_indent = 0
    for idx, line in enumerate(lines):
        m = re.match(r"^(\s*)lovelace\s*:\s*(?:#.*)?$", line)
        if m:
            lovelace_idx = idx
            lovelace_indent = len(m.group(1))
            break
    if lovelace_idx is None:
        return config_text, False

    dashboards_idx: int | None = None
    dashboards_indent = lovelace_indent + 2
    for idx in range(lovelace_idx + 1, len(lines)):
        line = lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= lovelace_indent:
            break
        m = re.match(r"^\s*dashboards\s*:\s*(.*)$", stripped)
        if indent == lovelace_indent + 2 and m:
            dashboards_idx = idx
            dashboards_indent = indent
            # Keep include-based dashboard maps untouched (manual merge required).
            if "!include" in (m.group(1) or ""):
                return config_text, False
            break
    if dashboards_idx is None:
        return config_text, False

    # Find end of current dashboards block.
    block_end = len(lines)
    for idx in range(dashboards_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if not stripped:
            continue
        indent = len(lines[idx]) - len(lines[idx].lstrip(" "))
        if indent <= dashboards_indent:
            block_end = idx
            break

    key_indent = " " * (dashboards_indent + 2)
    field_indent = " " * (dashboards_indent + 4)
    existing_keys: set[str] = set()
    key_pattern = re.compile(rf"^\s{{{dashboards_indent + 2}}}([A-Za-z0-9_-]+)\s*:\s*(?:#.*)?$")
    for idx in range(dashboards_idx + 1, block_end):
        m = key_pattern.match(lines[idx])
        if m:
            existing_keys.add(m.group(1))

    inserts: list[str] = []
    if "copilot-pilotsuite" not in existing_keys:
        inserts.extend(
            [
                f"{key_indent}copilot-pilotsuite:",
                f"{field_indent}mode: yaml",
                f'{field_indent}title: "PilotSuite - Styx"',
                f"{field_indent}icon: mdi:robot-outline",
                f"{field_indent}show_in_sidebar: false",
                f'{field_indent}filename: "{PRIMARY_DASHBOARD_DIR}/pilotsuite_dashboard_latest.yaml"',
            ]
        )
    if "copilot-habitus-zones" not in existing_keys:
        if inserts:
            inserts.append("")
        inserts.extend(
            [
                f"{key_indent}copilot-habitus-zones:",
                f"{field_indent}mode: yaml",
                f'{field_indent}title: "PilotSuite - Habitus Zones"',
                f"{field_indent}icon: mdi:layers-outline",
                f"{field_indent}show_in_sidebar: false",
                f'{field_indent}filename: "{PRIMARY_DASHBOARD_DIR}/habitus_zones_dashboard_latest.yaml"',
            ]
        )

    if not inserts:
        return config_text, False

    merged_lines = [*lines[:block_end], *inserts, *lines[block_end:]]
    merged = "\n".join(merged_lines)
    if config_text.endswith("\n"):
        merged += "\n"
    return merged, True


async def async_ensure_lovelace_dashboard_wiring(hass: HomeAssistant) -> str:
    """Ensure Lovelace can load PilotSuite YAML dashboards.

    Returns:
        One of: "wired", "auto_appended", "auto_merged", "manual_required", "error"
    """

    config_path = Path(hass.config.path("configuration.yaml"))
    snippet_path = Path(hass.config.path(SNIPPET_REL_PATH))
    legacy_snippet_path = Path(hass.config.path(_LEGACY_SNIPPET_REL_PATH))
    include_block = _include_block()

    try:
        await hass.async_add_executor_job(_write_text, snippet_path, _snippet_content())
        await hass.async_add_executor_job(_write_text, legacy_snippet_path, _snippet_content())

        config_text = await hass.async_add_executor_job(_read_text, config_path)
        if _is_dashboard_wired(config_text):
            return "wired"

        if not _has_lovelace_root(config_text):
            if _AUTOMATED_BLOCK_MARKER not in config_text:
                await hass.async_add_executor_job(_append_text, config_path, include_block)
                persistent_notification.async_create(
                    hass,
                    (
                        "PilotSuite hat Lovelace-Dashboard-Wiring automatisch ergaenzt.\n\n"
                        f"Datei: `{config_path}`\n\n"
                        "Bitte Home Assistant neu starten, damit die Sidebar-Dashboards erscheinen."
                    ),
                    title="PilotSuite Dashboard Wiring",
                    notification_id=_NOTIFICATION_ID,
                )
            return "auto_appended"

        merged_text, changed = _merge_dashboards_into_existing_lovelace(config_text)
        if changed:
            await hass.async_add_executor_job(_write_text, config_path, merged_text)
            persistent_notification.async_create(
                hass,
                (
                    "PilotSuite hat fehlende Dashboard-Eintraege in deinem bestehenden "
                    "`lovelace: dashboards:`-Block automatisch ergänzt.\n\n"
                    f"Datei: `{config_path}`\n\n"
                    "Bitte Home Assistant neu starten, damit die Sidebar-Dashboards erscheinen."
                ),
                title="PilotSuite Dashboard Wiring",
                notification_id=_NOTIFICATION_ID,
            )
            return "auto_merged"

        persistent_notification.async_create(
            hass,
            _manual_help_message(config_path),
            title="PilotSuite Dashboard Wiring",
            notification_id=_NOTIFICATION_ID,
        )
        return "manual_required"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to ensure PilotSuite Lovelace dashboard wiring")
        return "error"


_STORAGE_DASHBOARD_URL_PATH = "dashboard-pilotsuite"
_STORAGE_DASHBOARD_TITLE = "PilotSuite"
_STORAGE_DASHBOARD_ICON = "mdi:home-heart"


def _find_entity(entities: list[str], *patterns: str) -> str | None:
    """Find first entity matching any of the given substrings."""
    for pat in patterns:
        for e in entities:
            if pat in e:
                return e
    return None


def _filter_entities(entities: list[str], *patterns: str) -> list[str]:
    """Filter entities matching any of the given substrings."""
    return [e for e in entities if any(p in e for p in patterns)]


def _build_storage_dashboard_config(
    entities: list[str],
    *,
    enabled_views: set[str] | None = None,
) -> dict:
    """Build a storage-mode Lovelace dashboard config.

    HA frontend is "Sinne + Haende" (Thin Client):
    10 views covering all user-facing aspects with rich custom cards.
    """
    # ── Entity classification ──
    status_entities = [
        e for e in entities
        if e.startswith(("binary_sensor.pilotsuite", "sensor.pilotsuite_styx_",
                         "sensor.pilotsuite_core_"))
    ]
    zone_entities = _filter_entities(entities, "habitus_zones", "zones_v2")
    mood_entities = _filter_entities(entities, "mood")
    energy_entities = _filter_entities(entities, "energy", "power")
    media_entities = _filter_entities(
        entities, "media", "musikwolke", "sonos", "media_follow",
    )
    module_entities = _filter_entities(entities, "module", "autonomy")
    automation_entities = _filter_entities(entities, "automation", "zone_")
    neuron_entities = _filter_entities(entities, "neuron", "brain", "prediction")
    network_entities = _filter_entities(
        entities, "zwave", "zigbee", "mesh", "thread",
    )
    weather_entities = _filter_entities(entities, "weather")
    unifi_entities = _filter_entities(entities, "unifi")
    camera_entities = _filter_entities(entities, "camera", "motion", "activity")
    kg_entities = _filter_entities(entities, "kg_", "knowledge")
    debug_entities = [
        e for e in entities
        if e.startswith(("button.copilot_ha_", "button.pilotsuite_"))
        and not any(p in e for p in ("generate_", "download_", "validate_"))
    ]
    system_entities = _filter_entities(
        entities, "version", "online", "debug", "config_validation",
        "reload", "safety_backup",
    )
    # All classified entity IDs (for catch-all)
    _classified = set(
        status_entities + zone_entities + mood_entities + energy_entities
        + media_entities + module_entities + automation_entities
        + neuron_entities + network_entities + weather_entities
        + unifi_entities + camera_entities + kg_entities
        + debug_entities + system_entities
    )
    unassigned_entities = [e for e in entities if e not in _classified]

    # ── Resolve key entity IDs for custom cards ──
    mood_entity = _find_entity(
        entities, "sensor.pilotsuite_mood", "sensor.copilot_ha_mood",
    ) or "sensor.pilotsuite_mood"
    brain_nodes_entity = _find_entity(
        entities, "sensor.pilotsuite_brain_graph_nodes", "sensor.copilot_ha_brain_graph_nodes",
    ) or "sensor.pilotsuite_brain_graph_nodes"
    brain_edges_entity = _find_entity(
        entities, "sensor.pilotsuite_brain_graph_edges", "sensor.copilot_ha_brain_graph_edges",
    ) or "sensor.pilotsuite_brain_graph_edges"
    habitus_entity = _find_entity(
        entities, "sensor.pilotsuite_habitus_rules_count", "sensor.copilot_ha_habitus_rules_count",
    ) or "sensor.pilotsuite_habitus_rules_count"
    zones_entity = _find_entity(
        entities, "sensor.pilotsuite_habitus_zones", "sensor.copilot_ha_habitus_zones",
    ) or "sensor.pilotsuite_habitus_zones"

    views = [
        # ── 1. Styx (Start) ──
        {
            "title": "Styx",
            "path": "styx",
            "icon": "mdi:brain",
            "cards": [
                {
                    "type": "custom:styx-neural-card",
                    "title": "Neural Interface",
                    "show_history": True,
                },
                {
                    "type": "horizontal-stack",
                    "cards": [
                        {
                            "type": "custom:styx-mood-card",
                            "entity": mood_entity,
                        },
                        {
                            "type": "custom:styx-brain-card",
                            "entity": brain_nodes_entity,
                            "edge_entity": brain_edges_entity,
                        },
                    ],
                },
                {"type": "custom:styx-suggestions-card"},
                {"type": "custom:styx-error-card"},
            ],
        },
        # ── 2. Haushalt ──
        {
            "title": "Haushalt",
            "path": "haushalt",
            "icon": "mdi:home-heart",
            "cards": [
                {"type": "custom:styx-household-card"},
                *(
                    [{
                        "type": "entities",
                        "title": "PilotSuite Status",
                        "show_header_toggle": False,
                        "entities": status_entities[:8],
                    }] if status_entities else []
                ),
                *(
                    [{
                        "type": "custom:styx-mood-card",
                        "entity": mood_entity,
                    }] if mood_entities else []
                ),
            ],
        },
        # ── 3. Zonen ──
        {
            "title": "Zonen",
            "path": "zonen",
            "icon": "mdi:map-marker-radius",
            "cards": [
                {
                    "type": "custom:styx-habitus-card",
                    "entity": habitus_entity,
                    "max_rules": 8,
                },
                {
                    "type": "custom:styx-zone-card",
                    "entity": zones_entity,
                    "show_mood": True,
                    "show_neuron_activity": True,
                    "show_quick_actions": True,
                },
                *(
                    [{
                        "type": "entities",
                        "title": "Zonen-Entities",
                        "show_header_toggle": False,
                        "entities": zone_entities[:10],
                    }] if zone_entities else []
                ),
            ],
        },
        # ── 4. Automation ──
        {
            "title": "Automation",
            "path": "automation",
            "icon": "mdi:robot",
            "cards": [
                {"type": "custom:styx-suggestions-card"},
                {
                    "type": "custom:styx-habitus-card",
                    "entity": habitus_entity,
                    "max_rules": 10,
                },
                *(
                    [{
                        "type": "entities",
                        "title": "Automatisierungen",
                        "show_header_toggle": False,
                        "entities": automation_entities[:15],
                    }] if automation_entities else []
                ),
                {
                    "type": "grid",
                    "columns": 3,
                    "square": False,
                    "cards": [
                        {
                            "type": "button",
                            "name": "Brain Sync",
                            "icon": "mdi:brain",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.trigger_brain_sync",
                            },
                        },
                        {
                            "type": "button",
                            "name": "Muster Mining",
                            "icon": "mdi:magnify-scan",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.trigger_habitus_mining",
                            },
                        },
                        {
                            "type": "button",
                            "name": "Dashboard aktualisieren",
                            "icon": "mdi:refresh",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.refresh_dashboard",
                            },
                        },
                    ],
                },
            ],
        },
        # ── 5. Energie ──
        {
            "title": "Energie",
            "path": "energie",
            "icon": "mdi:lightning-bolt",
            "cards": [
                *(
                    [{
                        "type": "entities",
                        "title": "Energie & Verbrauch",
                        "show_header_toggle": False,
                        "entities": energy_entities[:12],
                    }] if energy_entities else [{
                        "type": "markdown",
                        "content": "Keine Energie-Entities konfiguriert.",
                    }]
                ),
            ],
        },
        # ── 6. Musik ──
        {
            "title": "Musik",
            "path": "musik",
            "icon": "mdi:speaker-group",
            "cards": [
                *(
                    [{
                        "type": "entities",
                        "title": "Medien & Musikwolke",
                        "show_header_toggle": False,
                        "entities": media_entities[:10],
                    }] if media_entities else [{
                        "type": "markdown",
                        "content": "Keine Medien-Entities konfiguriert.",
                    }]
                ),
                {
                    "type": "grid",
                    "columns": 3,
                    "square": False,
                    "cards": [
                        {
                            "type": "button",
                            "name": "Alle abspielen",
                            "icon": "mdi:play",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.musikwolke_play",
                                "service_data": {"zone_id": "all"},
                            },
                        },
                        {
                            "type": "button",
                            "name": "Alle pausieren",
                            "icon": "mdi:pause",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.musikwolke_pause",
                                "service_data": {"zone_id": "all"},
                            },
                        },
                        {
                            "type": "button",
                            "name": "Follow starten",
                            "icon": "mdi:account-music",
                            "tap_action": {
                                "action": "call-service",
                                "service": "pilotsuite.musikwolke_start_follow",
                                "service_data": {
                                    "person_id": "person.default",
                                    "source_zone": "wohnzimmer",
                                },
                            },
                        },
                    ],
                },
            ],
        },
        # ── 7. KI / Neuronen ──
        {
            "title": "KI",
            "path": "ki",
            "icon": "mdi:head-snowflake-outline",
            "cards": [
                {
                    "type": "custom:styx-brain-card",
                    "entity": brain_nodes_entity,
                    "edge_entity": brain_edges_entity,
                },
                {
                    "type": "horizontal-stack",
                    "cards": [
                        {
                            "type": "custom:styx-mood-card",
                            "entity": mood_entity,
                        },
                        {
                            "type": "custom:styx-habitus-card",
                            "entity": habitus_entity,
                            "max_rules": 5,
                        },
                    ],
                },
                *(
                    [{
                        "type": "entities",
                        "title": "Neuronen & Sensoren",
                        "show_header_toggle": False,
                        "entities": (neuron_entities + mood_entities)[:12],
                    }] if (neuron_entities or mood_entities) else []
                ),
            ],
        },
        # ── 8. Chat ──
        {
            "title": "Chat",
            "path": "chat",
            "icon": "mdi:chat-outline",
            "cards": [{"type": "custom:styx-chat-card"}],
        },
        # ── 9. Netzwerk ──
        {
            "title": "Netzwerk",
            "path": "netzwerk",
            "icon": "mdi:network",
            "cards": [
                *(
                    [{
                        "type": "entities",
                        "title": "Netzwerk-Module (ZWave / Zigbee / Thread)",
                        "show_header_toggle": False,
                        "entities": network_entities[:15],
                    }] if network_entities else [{
                        "type": "markdown",
                        "content": "Keine Netzwerk-Entities erkannt.",
                    }]
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "Wetter & Umgebung",
                        "show_header_toggle": False,
                        "entities": weather_entities[:10],
                    }] if weather_entities else []
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "UniFi Netzwerk",
                        "show_header_toggle": False,
                        "entities": unifi_entities[:8],
                    }] if unifi_entities else []
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "Kamera & Bewegung",
                        "show_header_toggle": False,
                        "entities": camera_entities[:10],
                    }] if camera_entities else []
                ),
            ],
        },
        # ── 10. System ──
        {
            "title": "System",
            "path": "system",
            "icon": "mdi:cog",
            "cards": [
                *(
                    [{
                        "type": "entities",
                        "title": "System & Version",
                        "show_header_toggle": False,
                        "entities": system_entities[:10],
                    }] if system_entities else []
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "Knowledge Graph",
                        "show_header_toggle": False,
                        "entities": kg_entities[:8],
                    }] if kg_entities else []
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "Debug & Aktionen",
                        "show_header_toggle": False,
                        "entities": debug_entities[:15],
                    }] if debug_entities else []
                ),
                *(
                    [{
                        "type": "entities",
                        "title": "Weitere Entities",
                        "show_header_toggle": False,
                        "entities": unassigned_entities[:20],
                    }] if unassigned_entities else []
                ),
            ],
        },
    ]

    # Filter views if enabled_views is specified
    if enabled_views is not None:
        views = [v for v in views if v["path"] in enabled_views]

    return {"title": _STORAGE_DASHBOARD_TITLE, "views": views}


async def async_ensure_storage_dashboard(hass: HomeAssistant) -> str:
    """Create a storage-mode Lovelace dashboard (works without HA restart).

    Returns:
        One of: "created", "exists", "error"
    """
    try:
        # HA 2026.3+: hass.data["lovelace"] is a LovelaceData dataclass, not a dict.
        # Earlier versions used a plain dict. Support both access patterns.
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            _LOGGER.debug("Lovelace not initialized, skipping storage dashboard")
            return "error"

        # Access dashboards dict (attribute on dataclass, key on dict)
        if isinstance(lovelace, dict):
            dashboards = lovelace.get("dashboards", {})
        else:
            dashboards = getattr(lovelace, "dashboards", None) or {}

        # Gather PilotSuite entity IDs for the dashboard
        ps_entities = sorted(
            eid
            for eid in hass.states.async_entity_ids()
            if "pilotsuite" in eid or "copilot" in eid
        )

        # Helper: save/update the views config in HA storage
        def _save_views() -> bool:
            """Save dashboard views to HA storage. Returns success."""
            try:
                from homeassistant.helpers.storage import Store

                dashboard_id = _STORAGE_DASHBOARD_URL_PATH.replace("-", "_")
                store = Store(hass, 1, f"lovelace.{dashboard_id}")
                config = _build_storage_dashboard_config(ps_entities)
                return store, config
            except Exception:  # noqa: BLE001
                return None, None

        # Dashboard already exists — update views
        if _STORAGE_DASHBOARD_URL_PATH in dashboards:
            _LOGGER.debug(
                "Storage dashboard '%s' exists, updating views", _STORAGE_DASHBOARD_URL_PATH
            )
            store, config = _save_views()
            if store and config:
                await store.async_save({"config": config})
                _LOGGER.info(
                    "Updated storage-mode PilotSuite dashboard views (%d entities)",
                    len(ps_entities),
                )
            return "exists"

        # Dashboard not loaded yet — check/create via DashboardsCollection.
        try:
            from homeassistant.components.lovelace.dashboard import (
                DashboardsCollection,
            )
        except ImportError:
            _LOGGER.warning(
                "Cannot import DashboardsCollection — create dashboard '%s' "
                "manually via the HA UI",
                _STORAGE_DASHBOARD_URL_PATH,
            )
            return "error"

        coll = DashboardsCollection(hass)
        await coll.async_load()

        # Double-check storage in case the dashboard exists but wasn't in the dict
        for item in coll.async_items():
            item_url = (
                item.get("url_path")
                if isinstance(item, dict)
                else getattr(item, "url_path", None)
            )
            if item_url == _STORAGE_DASHBOARD_URL_PATH:
                _LOGGER.debug(
                    "Storage dashboard '%s' found in collection, updating views",
                    _STORAGE_DASHBOARD_URL_PATH,
                )
                store, config = _save_views()
                if store and config:
                    await store.async_save({"config": config})
                return "exists"

        # Create the dashboard entry in the collection store
        await coll.async_create_item({
            "url_path": _STORAGE_DASHBOARD_URL_PATH,
            "title": _STORAGE_DASHBOARD_TITLE,
            "icon": _STORAGE_DASHBOARD_ICON,
            "show_in_sidebar": True,
            "require_admin": False,
        })

        # Save dashboard view config
        store, config = _save_views()
        if store and config:
            await store.async_save({"config": config})
            _LOGGER.info(
                "Created storage-mode PilotSuite dashboard with %d entities",
                len(ps_entities),
            )
        else:
            _LOGGER.warning(
                "Dashboard entry created but could not save views — "
                "configure views manually in the HA UI"
            )

        return "created"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to create storage-mode PilotSuite dashboard")
        return "error"


_YAML_DASHBOARD_SLUGS = ("copilot-pilotsuite", "copilot-habitus-zones")


async def async_hide_yaml_dashboards_from_sidebar(hass: HomeAssistant) -> None:
    """Hide legacy YAML dashboards from sidebar at runtime (no HA restart needed).

    The YAML snippet already sets show_in_sidebar: false, but that only takes
    effect after HA restart. This re-registers the panels immediately.
    """
    try:
        from homeassistant.components import frontend

        panels = hass.data.get(frontend.DATA_PANELS, {})
        hidden_count = 0
        for slug in _YAML_DASHBOARD_SLUGS:
            if slug in panels:
                panel = panels[slug]
                if getattr(panel, "sidebar_show", True):
                    frontend.async_register_built_in_panel(
                        hass,
                        "lovelace",
                        frontend_url_path=slug,
                        require_admin=False,
                        show_in_sidebar=False,
                        sidebar_title=getattr(panel, "sidebar_title", slug),
                        sidebar_icon=getattr(panel, "sidebar_icon", "mdi:robot-outline"),
                        config={"mode": "yaml"},
                        update=True,
                    )
                    _LOGGER.debug("Hidden YAML dashboard '%s' from sidebar", slug)
                    hidden_count += 1
        if hidden_count:
            _LOGGER.info("Hidden %d YAML dashboards from sidebar at runtime", hidden_count)
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not hide YAML dashboards from sidebar", exc_info=True)


def _validate_report_sections(sections: list[str]) -> tuple[bool, list[str]]:
    """Validate that all required report sections are present.

    Returns (ok, missing) where ok=True if all sections present.
    """
    missing = list(REQUIRED_REPORT_SECTIONS - set(sections))
    return len(missing) == 0, missing


REQUIRED_REPORT_SECTIONS = frozenset({
    "Changed", "Checked", "Not clean / open",
    "Next step", "workers", "cron"
})
