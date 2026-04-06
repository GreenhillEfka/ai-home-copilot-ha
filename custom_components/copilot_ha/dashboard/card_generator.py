"""Dashboard Card Generator — Auto-generate Lovelace YAML cards (v6.0.0).

Generates a complete PilotSuite Styx dashboard with tabs:
1. Styx      — Neural Brain, Mood, Chat, Suggestions, Automations
2. Haushalt  — Presence, Zones, Weather, Household overview
3. Energie   — Consumption, Production, Schedule, Sankey, Anomalies
4. Praesenz  — Per-zone presence status, automation modes
5. Musik     — Sonos / Musikwolke control
6+ Per-Zone  — Dynamic tabs for each Habitus zone
"""

from __future__ import annotations

import logging
from typing import Any

import yaml

_LOGGER = logging.getLogger(__name__)


def _yaml_dump(data: Any) -> str:
    """Dump data to YAML string with clean formatting."""
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ── Tab 1: Styx (Brain / AI) ──────────────────────────────────────────

def generate_styx_view(host: str, port: int) -> dict[str, Any]:
    """Tab 1: Styx — Neural Brain, Chat, Suggestions."""
    core_url = f"http://{host}:{port}"
    return {
        "title": "Styx",
        "path": "styx",
        "icon": "mdi:brain",
        "badges": [],
        "cards": [
            # Brain Graph iframe
            {
                "type": "iframe",
                "url": f"{core_url}/api/v1/styx/dashboard",
                "title": "Neuronales Netzwerk",
                "aspect_ratio": "16:9",
            },
            # Mood + Brain side by side
            {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "entities",
                        "title": "Stimmung",
                        "entities": [
                            {"entity": "sensor.copilot_ha_mood", "name": "Aktuelle Stimmung"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Brain Graph",
                        "entities": [
                            {"entity": "sensor.copilot_ha_brain_graph_nodes", "name": "Knoten"},
                        ],
                    },
                ],
            },
            # Suggestions
            {
                "type": "markdown",
                "title": "KI-Vorschlaege",
                "content": (
                    "{% set suggestions = state_attr('sensor.copilot_ha_suggestions', 'suggestions') %}\n"
                    "{% if suggestions %}\n"
                    "{% for s in suggestions[:5] %}\n"
                    "- **{{ s.title }}** ({{ s.confidence }}%): {{ s.description }}\n"
                    "{% endfor %}\n"
                    "{% else %}\n"
                    "Keine aktiven Vorschlaege.\n"
                    "{% endif %}"
                ),
            },
            # Automations
            {
                "type": "entities",
                "title": "Automatisierungen",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.copilot_ha_predictive_automation", "name": "Vorhergesagte Automatisierung"},
                ],
            },
        ],
    }


# ── Tab 2: Haushalt (Household) ───────────────────────────────────────

def generate_haushalt_view(host: str, port: int) -> dict[str, Any]:
    """Tab 2: Haushalt — Household overview, presence, zones."""
    return {
        "title": "Haushalt",
        "path": "haushalt",
        "icon": "mdi:home-city",
        "badges": [],
        "cards": [
            # Presence Overview
            {
                "type": "entities",
                "title": "Praesenz",
                "entities": [
                    {"entity": "binary_sensor.pilotsuite_zone_presence_overview", "name": "Gesamt-Praesenz"},
                    {"entity": "sensor.pilotsuite_presence_intelligence", "name": "Praesenz Intelligence"},
                ],
            },
            # Habitus Zones
            {
                "type": "entities",
                "title": "Habitus-Zonen",
                "entities": [
                    {"entity": "sensor.pilotsuite_habitus_zones", "name": "Zonen-Uebersicht"},
                ],
            },
            # Zone Modes
            {
                "type": "markdown",
                "title": "Aktive Modi",
                "content": (
                    "{% set modes = state_attr('sensor.pilotsuite_zone_modes', 'active_modes') %}\n"
                    "{% if modes and modes | length > 0 %}\n"
                    "{% for m in modes %}\n"
                    "- **{{ m.zone_id }}**: {{ m.mode_name_de }} ({{ m.remaining_min }} min)\n"
                    "{% endfor %}\n"
                    "{% else %}\n"
                    "Keine aktiven Sondermodi.\n"
                    "{% endif %}"
                ),
            },
            # Light Intelligence
            {
                "type": "entities",
                "title": "Licht-Intelligenz",
                "entities": [
                    {"entity": "sensor.pilotsuite_light_intelligence", "name": "Lichtsteuerung"},
                ],
            },
        ],
    }


# ── Tab 3: Energie ────────────────────────────────────────────────────

def generate_energy_overview_card(host: str, port: int) -> dict[str, Any]:
    """Generate energy overview gauge card."""
    return {
        "type": "vertical-stack",
        "title": "Energie-Uebersicht",
        "cards": [
            {
                "type": "horizontal-stack",
                "cards": [
                    {
                        "type": "gauge",
                        "entity": "sensor.pilotsuite_energy_consumption",
                        "name": "Verbrauch heute",
                        "unit": "kWh",
                        "min": 0,
                        "max": 50,
                        "severity": {"green": 0, "yellow": 20, "red": 35},
                    },
                    {
                        "type": "gauge",
                        "entity": "sensor.pilotsuite_energy_production",
                        "name": "Erzeugung heute",
                        "unit": "kWh",
                        "min": 0,
                        "max": 30,
                        "severity": {"red": 0, "yellow": 5, "green": 15},
                    },
                ],
            },
            {
                "type": "gauge",
                "entity": "sensor.pilotsuite_current_power",
                "name": "Aktuelle Leistung",
                "unit": "W",
                "min": 0,
                "max": 11000,
                "severity": {"green": 0, "yellow": 5000, "red": 8000},
            },
        ],
    }


def generate_schedule_card(host: str, port: int) -> dict[str, Any]:
    """Generate energy schedule card showing upcoming device runs."""
    return {
        "type": "vertical-stack",
        "title": "Geraete-Zeitplan",
        "cards": [
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_energy_schedule",
                "name": "Naechstes Geraet",
                "icon": "mdi:calendar-clock",
            },
            {
                "type": "markdown",
                "content": (
                    "### Tagesplan\n"
                    "{% set sched = state_attr('sensor.pilotsuite_energy_schedule', 'schedule') %}\n"
                    "{% if sched %}\n"
                    "| Geraet | Zeit | Kosten | PV |\n"
                    "|--------|------|--------|----|{% for s in sched %}\n"
                    "| {{ s.device }} | {{ s.hours }} | {{ s.cost_eur }} EUR | {{ s.pv_pct }}% |{% endfor %}\n"
                    "\n**Gesamtkosten:** {{ state_attr('sensor.pilotsuite_energy_schedule', 'total_estimated_cost_eur') }} EUR\n"
                    "**PV-Abdeckung:** {{ state_attr('sensor.pilotsuite_energy_schedule', 'total_pv_coverage_percent') }}%\n"
                    "{% else %}\n"
                    "Kein Zeitplan verfuegbar.\n"
                    "{% endif %}"
                ),
            },
        ],
    }


def generate_sankey_card(host: str, port: int) -> dict[str, Any]:
    """Generate Sankey energy flow diagram card (iframe)."""
    return {
        "type": "iframe",
        "url": f"http://{host}:{port}/api/v1/energy/sankey.svg?theme=dark&width=700&height=400",
        "title": "Energiefluss",
        "aspect_ratio": "16:9",
    }


def generate_anomaly_card() -> dict[str, Any]:
    """Generate conditional anomaly alert card."""
    return {
        "type": "conditional",
        "conditions": [
            {"entity": "sensor.pilotsuite_energy_consumption", "state_not": "unavailable"},
        ],
        "card": {
            "type": "markdown",
            "title": "Energie-Warnungen",
            "content": (
                "{% set anomalies = state_attr('sensor.pilotsuite_energy_consumption', 'anomalies_detected') %}\n"
                "{% if anomalies and anomalies > 0 %}\n"
                "Warnung: **{{ anomalies }} Anomalie(n) erkannt**\n"
                "\nPruefen Sie den Energieverbrauch auf ungewoehnliche Muster.\n"
                "{% else %}\n"
                "Keine Anomalien erkannt\n"
                "{% endif %}"
            ),
        },
    }


def generate_energy_view(host: str, port: int, zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab 3: Energie — Full energy dashboard."""
    cards: list[dict[str, Any]] = [
        generate_energy_overview_card(host, port),
        generate_schedule_card(host, port),
        generate_sankey_card(host, port),
    ]

    if zones:
        zone_cards = []
        for zone in zones:
            zone_cards.append({
                "type": "entities",
                "title": zone.get("zone_name", zone.get("zone_id", "Zone")),
                "entities": [
                    {
                        "type": "attribute",
                        "entity": "sensor.pilotsuite_energy_sankey_flow",
                        "attribute": "total_consumption_kwh",
                        "name": "Verbrauch",
                        "suffix": "kWh",
                    },
                ],
                "footer": {
                    "type": "graph",
                    "entity": "sensor.pilotsuite_energy_sankey_flow",
                    "hours_to_show": 24,
                },
            })
        cards.append({
            "type": "vertical-stack",
            "title": "Zonen-Energie",
            "cards": zone_cards,
        })

    cards.append(generate_anomaly_card())

    return {
        "title": "Energie",
        "path": "energie",
        "icon": "mdi:lightning-bolt",
        "badges": [],
        "cards": cards,
    }


# ── Tab 4: Praesenz ───────────────────────────────────────────────────

def generate_presence_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab 4: Praesenz — Zone presence and automation modes."""
    cards: list[dict[str, Any]] = [
        # Global presence overview
        {
            "type": "entities",
            "title": "Praesenz-Uebersicht",
            "entities": [
                {"entity": "binary_sensor.pilotsuite_zone_presence_overview", "name": "Gesamt"},
                {"entity": "sensor.pilotsuite_presence_intelligence", "name": "Intelligence"},
            ],
        },
    ]

    # Per-zone presence cards
    if zones:
        zone_presence_cards = []
        for zone in zones:
            zone_id = zone.get("zone_id", "")
            zone_name = zone.get("zone_name", zone.get("name", zone_id))
            entity_id = f"binary_sensor.pilotsuite_zone_presence_{zone_id}"
            zone_presence_cards.append({
                "type": "entities",
                "title": zone_name,
                "entities": [
                    {"entity": entity_id, "name": "Praesenz"},
                ],
            })

        if zone_presence_cards:
            cards.append({
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": zone_presence_cards,
            })

    # Mode overview (markdown template)
    cards.append({
        "type": "markdown",
        "title": "Automatisierungs-Modi",
        "content": (
            "{% set overview = state_attr('binary_sensor.pilotsuite_zone_presence_overview', 'total_zones') %}\n"
            "{% set occupied = state_attr('binary_sensor.pilotsuite_zone_presence_overview', 'occupied_zones') %}\n"
            "{% set lights = state_attr('binary_sensor.pilotsuite_zone_presence_overview', 'active_lights') %}\n"
            "{% set music = state_attr('binary_sensor.pilotsuite_zone_presence_overview', 'active_music') %}\n"
            "| Metrik | Wert |\n"
            "|--------|------|\n"
            "| Zonen gesamt | {{ overview }} |\n"
            "| Belegt | {{ occupied }} |\n"
            "| Aktive Beleuchtung | {{ lights }} |\n"
            "| Aktive Musik | {{ music }} |"
        ),
    })

    return {
        "title": "Praesenz",
        "path": "praesenz",
        "icon": "mdi:motion-sensor",
        "badges": [],
        "cards": cards,
    }


# ── Tab 5: Musik / Musikwolke ─────────────────────────────────────────

def generate_music_view(host: str, port: int) -> dict[str, Any]:
    """Tab 5: Musik — Sonos / Musikwolke control with interactive buttons."""
    core_url = f"http://{host}:{port}"
    return {
        "title": "Musik",
        "path": "musik",
        "icon": "mdi:speaker-group",
        "badges": [],
        "cards": [
            # Musikwolke status + follow sensor
            {
                "type": "entities",
                "title": "Musikwolke-Status",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.pilotsuite_media_follow", "name": "Follow-Modus"},
                ],
            },
            # Sonos overview iframe
            {
                "type": "iframe",
                "url": f"{core_url}/api/v1/sonos/summary",
                "title": "Sonos-Uebersicht",
                "aspect_ratio": "16:9",
            },
            # Interactive Musikwolke controls
            {
                "type": "vertical-stack",
                "title": "Musikwolke-Steuerung",
                "cards": [
                    # Play / Pause / Volume grid
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
                                    "service": "copilot_ha.musikwolke_play",
                                    "service_data": {"zone_id": "all"},
                                },
                            },
                            {
                                "type": "button",
                                "name": "Alle pausieren",
                                "icon": "mdi:pause",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "copilot_ha.musikwolke_pause",
                                    "service_data": {"zone_id": "all"},
                                },
                            },
                            {
                                "type": "button",
                                "name": "Gruppe aufloesen",
                                "icon": "mdi:speaker-off",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "copilot_ha.musikwolke_dissolve",
                                    "service_data": {"zone_ids": []},
                                    "confirmation": {
                                        "text": "Alle Musikwolke-Gruppen aufloesen?",
                                    },
                                },
                            },
                        ],
                    },
                    # Follow mode controls
                    {
                        "type": "grid",
                        "columns": 2,
                        "square": False,
                        "cards": [
                            {
                                "type": "button",
                                "name": "Follow starten",
                                "icon": "mdi:account-music",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "copilot_ha.musikwolke_start_follow",
                                    "service_data": {
                                        "person_id": "person.default",
                                        "source_zone": "wohnzimmer",
                                    },
                                },
                            },
                            {
                                "type": "button",
                                "name": "Follow stoppen",
                                "icon": "mdi:account-music-outline",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "copilot_ha.musikwolke_stop_follow",
                                    "service_data": {"session_id": "latest"},
                                },
                            },
                        ],
                    },
                ],
            },
            # Zone automation mode
            {
                "type": "markdown",
                "title": "Zonen-Automatisierung",
                "content": (
                    "{% set modes = state_attr('sensor.pilotsuite_zone_modes', 'active_modes') %}\n"
                    "{% if modes and modes | length > 0 %}\n"
                    "| Zone | Modus |\n"
                    "|------|-------|\n"
                    "{% for m in modes %}\n"
                    "| {{ m.zone_id }} | {{ m.mode_name_de }} |\n"
                    "{% endfor %}\n"
                    "{% else %}\n"
                    "Alle Zonen im Standard-Modus (off).\n"
                    "{% endif %}"
                ),
            },
            # Info card
            {
                "type": "markdown",
                "title": "Info",
                "content": (
                    "Die **Musikwolke** synchronisiert Sonos-Speaker ueber Zonen.\n\n"
                    "- **Follow-Modus**: Musik folgt Ihnen automatisch\n"
                    "- **Gruppen**: Mehrere Zonen spielen synchron\n"
                    "- **Steuerung**: Buttons oben, Styx Chat oder HA Automations\n\n"
                    "Services: `copilot_ha.musikwolke_*`, `copilot_ha.zone_automation_set_mode`"
                ),
            },
        ],
    }


# ── Per-Zone Tab ──────────────────────────────────────────────────────

def generate_zone_view(
    zone: dict[str, Any],
    host: str,
    port: int,
) -> dict[str, Any]:
    """Generate a per-zone tab with presence, light, climate, media cards."""
    zone_id = zone.get("zone_id", "")
    zone_name = zone.get("zone_name", zone.get("name", zone_id))
    entities = zone.get("entities", {})

    cards: list[dict[str, Any]] = []

    # Zone presence + automation state
    presence_entity = f"binary_sensor.pilotsuite_zone_presence_{zone_id}"
    cards.append({
        "type": "entities",
        "title": f"{zone_name} — Status",
        "entities": [
            {"entity": presence_entity, "name": "Praesenz"},
        ],
    })

    # Lights
    light_entities = entities.get("lights", [])
    if light_entities:
        cards.append({
            "type": "entities",
            "title": "Beleuchtung",
            "show_header_toggle": True,
            "entities": [{"entity": eid} for eid in light_entities[:8]],
        })

    # Climate
    climate_entities = (
        entities.get("temperature", [])
        + entities.get("humidity", [])
        + entities.get("heating", [])
    )
    if climate_entities:
        cards.append({
            "type": "entities",
            "title": "Klima",
            "entities": [{"entity": eid} for eid in climate_entities[:6]],
        })

    # Media
    media_entities = entities.get("media", [])
    if media_entities:
        cards.append({
            "type": "entities",
            "title": "Medien",
            "entities": [{"entity": eid} for eid in media_entities[:4]],
        })

    # Covers
    cover_entities = entities.get("cover", [])
    if cover_entities:
        cards.append({
            "type": "entities",
            "title": "Rollladen / Abdeckungen",
            "show_header_toggle": True,
            "entities": [{"entity": eid} for eid in cover_entities[:6]],
        })

    # If no entity groups, show a simple fallback
    if not any([light_entities, climate_entities, media_entities, cover_entities]):
        entity_ids = zone.get("entity_ids", [])
        if entity_ids:
            cards.append({
                "type": "entities",
                "title": "Geraete",
                "entities": [{"entity": eid} for eid in entity_ids[:10]],
            })

    return {
        "title": zone_name,
        "path": f"zone-{zone_id}",
        "icon": "mdi:floor-plan",
        "badges": [],
        "cards": cards,
    }


# ── Full Dashboard Assembly ───────────────────────────────────────────

def generate_full_dashboard(
    host: str,
    port: int,
    zones: list[dict[str, Any]] | None = None,
    include_sankey: bool = True,
    include_schedule: bool = True,
    include_anomalies: bool = True,
) -> dict[str, Any]:
    """Generate complete energy dashboard view (backward compatible)."""
    cards: list[dict[str, Any]] = [generate_energy_overview_card(host, port)]
    if include_schedule:
        cards.append(generate_schedule_card(host, port))
    if include_sankey:
        cards.append(generate_sankey_card(host, port))
    if zones:
        zone_cards = []
        for zone in zones:
            zone_cards.append({
                "type": "entities",
                "title": zone.get("zone_name", zone.get("zone_id", "Zone")),
                "entities": [{
                    "type": "attribute",
                    "entity": "sensor.pilotsuite_energy_sankey_flow",
                    "attribute": "total_consumption_kwh",
                    "name": "Verbrauch",
                    "suffix": "kWh",
                }],
                "footer": {
                    "type": "graph",
                    "entity": "sensor.pilotsuite_energy_sankey_flow",
                    "hours_to_show": 24,
                },
            })
        cards.append({"type": "vertical-stack", "title": "Zonen-Energie", "cards": zone_cards})
    if include_anomalies:
        cards.append(generate_anomaly_card())

    return {
        "title": "PilotSuite Energie",
        "path": "pilotsuite-energy",
        "icon": "mdi:lightning-bolt",
        "badges": [],
        "cards": cards,
    }


def generate_styx_dashboard(
    host: str,
    port: int,
    zones: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate complete multi-tab Styx dashboard.

    Returns a dict with {"views": [...]} ready for Lovelace YAML import.
    """
    views: list[dict[str, Any]] = [
        generate_styx_view(host, port),
        generate_haushalt_view(host, port),
        generate_energy_view(host, port, zones=zones),
        generate_presence_view(zones=zones),
        generate_music_view(host, port),
    ]

    # Add per-zone tabs
    for zone in (zones or []):
        views.append(generate_zone_view(zone, host, port))

    return {"views": views}


# ── Tab 7: Lichtmodul ────────────────────────────────────────────────

def generate_licht_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab: Licht — Per-zone light control."""
    cards: list[dict[str, Any]] = [
        {
            "type": "entities",
            "title": "Licht-Uebersicht",
            "show_header_toggle": False,
            "entities": [
                {"entity": "sensor.pilotsuite_licht_status", "name": "Lichter an / gesamt"},
                {"entity": "sensor.pilotsuite_licht_overrides", "name": "Manuelle Overrides"},
            ],
        },
    ]

    for zone in (zones or []):
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("zone_name", zone.get("name", zone_id))
        light_entities = zone.get("entities", {}).get("lights", [])
        if light_entities:
            cards.append({
                "type": "entities",
                "title": zone_name,
                "show_header_toggle": True,
                "entities": [{"entity": eid} for eid in light_entities[:8]],
            })

    return {
        "title": "Licht",
        "path": "licht",
        "icon": "mdi:lightbulb-group",
        "badges": [],
        "cards": cards,
    }


# ── Tab 8: Helligkeitsmodul ──────────────────────────────────────────

def generate_helligkeit_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab: Helligkeit — Brightness sensors per zone."""
    cards: list[dict[str, Any]] = [
        {
            "type": "horizontal-stack",
            "cards": [
                {
                    "type": "gauge",
                    "entity": "sensor.outdoor_brightness",
                    "name": "Outdoor Lux",
                    "unit": "lx",
                    "min": 0,
                    "max": 100000,
                    "severity": {"red": 0, "yellow": 5000, "green": 20000},
                },
                {
                    "type": "gauge",
                    "entity": "sensor.pilotsuite_helligkeit_zones_needing_light",
                    "name": "Zonen brauchen Licht",
                    "min": 0,
                    "max": 10,
                    "severity": {"green": 0, "yellow": 2, "red": 5},
                },
            ],
        },
    ]

    for zone in (zones or []):
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("zone_name", zone.get("name", zone_id))
        brightness_entities = (
            zone.get("entities", {}).get("brightness", [])
            + zone.get("entities", {}).get("illuminance", [])
        )
        if brightness_entities:
            cards.append({
                "type": "sensor",
                "entity": brightness_entities[0],
                "name": f"{zone_name} — Indoor Lux",
                "graph": "line",
                "hours_to_show": 24,
            })

    return {
        "title": "Helligkeit",
        "path": "helligkeit",
        "icon": "mdi:brightness-6",
        "badges": [],
        "cards": cards,
    }


# ── Tab 9: Heizmodul ────────────────────────────────────────────────

def generate_heiz_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab: Heizung — Climate control per zone."""
    cards: list[dict[str, Any]] = [
        {
            "type": "horizontal-stack",
            "cards": [
                {
                    "type": "gauge",
                    "entity": "sensor.pilotsuite_avg_indoor_temp",
                    "name": "Ø Temperatur",
                    "unit": "°C",
                    "min": 10,
                    "max": 30,
                    "severity": {"green": 19, "yellow": 24, "red": 27},
                },
                {
                    "type": "gauge",
                    "entity": "sensor.pilotsuite_avg_humidity",
                    "name": "Ø Feuchte",
                    "unit": "%",
                    "min": 0,
                    "max": 100,
                    "severity": {"red": 0, "yellow": 30, "green": 40},
                },
            ],
        },
    ]

    for zone in (zones or []):
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("zone_name", zone.get("name", zone_id))
        climate_entities = zone.get("entities", {}).get("heating", [])
        temp_entities = zone.get("entities", {}).get("temperature", [])
        humidity_entities = zone.get("entities", {}).get("humidity", [])

        if climate_entities:
            zone_cards: list[dict[str, Any]] = [
                {"type": "thermostat", "entity": climate_entities[0]},
            ]
            side = []
            if temp_entities:
                side.append({"type": "entity", "entity": temp_entities[0], "name": "Temperatur"})
            if humidity_entities:
                side.append({"type": "entity", "entity": humidity_entities[0], "name": "Feuchte"})
            if side:
                zone_cards.append({"type": "horizontal-stack", "cards": side})
            cards.append({"type": "vertical-stack", "title": zone_name, "cards": zone_cards})

    return {
        "title": "Heizung",
        "path": "heizung",
        "icon": "mdi:thermostat",
        "badges": [],
        "cards": cards,
    }


# ── Tab 10: Bewegungsmodul ───────────────────────────────────────────

def generate_bewegung_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab: Bewegung — Motion sensors per zone."""
    cards: list[dict[str, Any]] = [
        {
            "type": "entities",
            "title": "Bewegungs-Uebersicht",
            "show_header_toggle": False,
            "entities": [
                {"entity": "sensor.pilotsuite_bewegung_active", "name": "Aktive Sensoren"},
                {"entity": "sensor.pilotsuite_bewegung_last_motion", "name": "Letzte Bewegung"},
            ],
        },
    ]

    for zone in (zones or []):
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("zone_name", zone.get("name", zone_id))
        motion_entities = zone.get("entities", {}).get("motion", [])
        if motion_entities:
            cards.append({
                "type": "vertical-stack",
                "title": zone_name,
                "cards": [
                    {"type": "entity", "entity": motion_entities[0], "name": "Bewegungsmelder", "icon": "mdi:motion-sensor"},
                    {"type": "sensor", "entity": motion_entities[0], "name": "Verlauf", "graph": "line", "hours_to_show": 24},
                ],
            })

    return {
        "title": "Bewegung",
        "path": "bewegung",
        "icon": "mdi:motion-sensor",
        "badges": [],
        "cards": cards,
    }


# ── Tab 11: Praesenzmodul ───────────────────────────────────────────

def generate_praesenz_view(zones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Tab: Praesenz — Person presence per zone."""
    cards: list[dict[str, Any]] = [
        {
            "type": "entities",
            "title": "Personen zu Hause",
            "show_header_toggle": False,
            "entities": [
                {"entity": "sensor.pilotsuite_persons_home", "name": "Personen"},
                {"entity": "sensor.pilotsuite_zones_occupied", "name": "Zonen belegt"},
            ],
        },
    ]

    if zones:
        zone_cards = []
        for zone in zones:
            zone_id = zone.get("zone_id", "")
            zone_name = zone.get("zone_name", zone.get("name", zone_id))
            zone_cards.append({
                "type": "entities",
                "title": zone_name,
                "entities": [
                    {"entity": f"binary_sensor.pilotsuite_zone_presence_{zone_id}", "name": "Belegt"},
                    {"entity": f"sensor.pilotsuite_{zone_id}_person_count", "name": "Personen"},
                ],
            })
        if zone_cards:
            cards.append({"type": "grid", "columns": 2, "square": False, "cards": zone_cards})

    cards.append({
        "type": "markdown",
        "title": "Praesenz-Uebersicht",
        "content": (
            "{% set dashboard = state_attr('sensor.pilotsuite_praesenz_dashboard', 'zones') %}\n"
            "{% if dashboard %}\n"
            "| Zone | Status | Personen |\n"
            "|------|--------|----------|\n"
            "{% for z in dashboard %}\n"
            "| {{ z.zone_name }} | {{ 'belegt' if z.is_occupied else 'leer' }} | {{ z.persons | join(', ') if z.persons else '—' }} |\n"
            "{% endfor %}\n"
            "{% else %}\n"
            "Keine Praesenz-Daten verfuegbar.\n"
            "{% endif %}"
        ),
    })

    return {
        "title": "Praesenz",
        "path": "praesenz-modul",
        "icon": "mdi:account-group",
        "badges": [],
        "cards": cards,
    }


# ── Full Dashboard Assembly (updated) ────────────────────────────────


def generate_network_view() -> dict[str, Any]:
    """Tab: Netzwerk — ZWave, Zigbee, Thread, UniFi status."""
    return {
        "title": "Netzwerk",
        "path": "netzwerk",
        "icon": "mdi:network",
        "badges": [],
        "cards": [
            {
                "type": "entities",
                "title": "ZWave Netzwerk",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.pilotsuite_zwave_network_health", "name": "Netzwerk-Health"},
                    {"entity": "sensor.pilotsuite_zwave_devices_online", "name": "Geraete online"},
                    {"entity": "binary_sensor.pilotsuite_zwave_mesh_status", "name": "Mesh-Status"},
                ],
            },
            {
                "type": "entities",
                "title": "Zigbee Netzwerk",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.pilotsuite_zigbee_network_health", "name": "Netzwerk-Health"},
                    {"entity": "sensor.pilotsuite_zigbee_devices_online", "name": "Geraete online"},
                    {"entity": "binary_sensor.pilotsuite_zigbee_mesh_status", "name": "Mesh-Status"},
                ],
            },
            {
                "type": "entities",
                "title": "Mesh-Uebersicht",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.pilotsuite_mesh_network_overview", "name": "Gesamt-Uebersicht"},
                ],
            },
            {
                "type": "entities",
                "title": "UniFi Netzwerk",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.copilot_ha_unifi_clients_online", "name": "Clients online"},
                    {"entity": "sensor.copilot_ha_unifi_wan_latency", "name": "WAN Latenz"},
                    {"entity": "sensor.copilot_ha_unifi_packet_loss", "name": "Paketverlust"},
                    {"entity": "sensor.copilot_ha_unifi_uptime", "name": "Uptime"},
                ],
            },
            {
                "type": "entities",
                "title": "Wetter & Umgebung",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.copilot_ha_weather_condition", "name": "Wetterlage"},
                    {"entity": "sensor.copilot_ha_weather_temperature", "name": "Temperatur"},
                    {"entity": "sensor.copilot_ha_weather_cloud_coverage", "name": "Bewoelkung"},
                    {"entity": "sensor.copilot_ha_weather_uv_index", "name": "UV-Index"},
                ],
            },
        ],
    }


def generate_system_view() -> dict[str, Any]:
    """Tab: System — Debug, Version, Knowledge Graph, Kamera."""
    return {
        "title": "System",
        "path": "system",
        "icon": "mdi:cog",
        "badges": [],
        "cards": [
            {
                "type": "entities",
                "title": "System & Version",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "binary_sensor.copilot_ha_online", "name": "Online"},
                    {"entity": "sensor.copilot_ha_version", "name": "Version"},
                    {"entity": "sensor.copilot_ha_core_api_v1", "name": "Core API"},
                ],
            },
            {
                "type": "entities",
                "title": "Kamera & Bewegung",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "sensor.copilot_ha_camera_motion_history", "name": "Bewegungsverlauf"},
                    {"entity": "sensor.copilot_ha_camera_presence_history", "name": "Praesenzverlauf"},
                    {"entity": "sensor.copilot_ha_camera_activity_history", "name": "Aktivitaetsverlauf"},
                    {"entity": "sensor.copilot_ha_camera_zone_activity", "name": "Zonen-Aktivitaet"},
                ],
            },
            {
                "type": "entities",
                "title": "Debug & Wartung",
                "show_header_toggle": False,
                "entities": [
                    {"entity": "button.copilot_ha_reload_config_entry", "name": "Config neu laden"},
                    {"entity": "button.copilot_ha_enable_debug_30m", "name": "Debug 30min"},
                    {"entity": "button.copilot_ha_disable_debug", "name": "Debug aus"},
                    {"entity": "button.copilot_ha_clear_all_logs", "name": "Logs leeren"},
                    {"entity": "button.copilot_ha_ping_core", "name": "Core anpingen"},
                ],
            },
        ],
    }


def generate_styx_dashboard_extended(
    host: str,
    port: int,
    zones: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate complete multi-tab Styx dashboard including module tabs.

    Returns a dict with {"views": [...]} ready for Lovelace YAML import.
    """
    views: list[dict[str, Any]] = [
        generate_styx_view(host, port),
        generate_haushalt_view(host, port),
        generate_energy_view(host, port, zones=zones),
        generate_presence_view(zones=zones),
        generate_music_view(host, port),
        # Module tabs
        generate_licht_view(zones=zones),
        generate_helligkeit_view(zones=zones),
        generate_heiz_view(zones=zones),
        generate_bewegung_view(zones=zones),
        generate_praesenz_view(zones=zones),
        # Netzwerk + System tabs
        generate_network_view(),
        generate_system_view(),
    ]

    # Add per-zone tabs
    for zone in (zones or []):
        views.append(generate_zone_view(zone, host, port))

    return {"views": views}


def dashboard_to_yaml(
    host: str,
    port: int,
    zones: list[dict[str, Any]] | None = None,
) -> str:
    """Generate full dashboard as YAML string for Lovelace import."""
    dashboard = generate_styx_dashboard(host, port, zones=zones)
    return _yaml_dump(dashboard)


# ── Habitus Zone Live Overview (2026-04-06) ─────────────────────────────────
def generate_habitus_zone_live_view(
    zones: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate a live Habitus Zone overview tab with real-time entity states.
    
    Shows all configured Habitus zones with live state cards pulled from HA entities.
    Each zone card shows: presence, temperature, lights, climate, energy.
    Uses Glance card for compact multi-entity overview.
    """
    all_zones = zones or []
    
    cards: list[dict[str, Any]] = []
    
    # ── Zone grid cards ────────────────────────────────────────────────────
    for zone in all_zones:
        zone_id = zone.get("zone_id", zone.get("zone_type", "unknown"))
        zone_name = zone.get("zone_name", zone.get("name_de", zone_id))
        entities = zone.get("entities", {})
        zone_type = zone.get("zone_type", "room")
        
        # Determine icon by zone type
        icon_map = {
            "living": "mdi:sofa",
            "kitchen": "mdi:silverware-fork-knife",
            "bath": "mdi:shower",
            "bedroom": "mdi:bed",
            "office": "mdi:desk",
            "hallway": "mdi:door",
            "room_mira": "mdi:account",
            "room_paul": "mdi:account",
            "terrace": "mdi:tree",
            "outside": "mdi:leaf",
        }
        zone_icon = icon_map.get(zone_type, "mdi:floor-plan")
        
        zone_cards: list[dict[str, Any]] = []
        
        # Presence binary sensor
        presence_entity = f"binary_sensor.pilotsuite_zone_presence_{zone_id}"
        zone_cards.append({
            "type": "entity",
            "entity": presence_entity,
            "name": "Präsenz",
            "icon": zone_icon,
        })
        
        # Temperature
        temp_entities = entities.get("temperature", [])[:2]
        for te in temp_entities:
            zone_cards.append({
                "type": "entity",
                "entity": te,
                "name": "Temperatur",
            })
        
        # Humidity
        hum_entities = entities.get("humidity", [])[:1]
        for he in hum_entities:
            zone_cards.append({
                "type": "entity",
                "entity": he,
                "name": "Feuchte",
            })
        
        # Active lights
        light_entities = entities.get("lights", [])[:4]
        if light_entities:
            zone_cards.extend([{"type": "entity", "entity": e, "name": "Licht"} for e in light_entities])
        
        # Climate / heating
        climate_entities = entities.get("heating", [])[:2]
        for ce in climate_entities:
            zone_cards.append({
                "type": "entity",
                "entity": ce,
                "name": "Heizung",
            })
        
        # Media player
        media_entities = entities.get("media", [])[:1]
        for me in media_entities:
            zone_cards.append({
                "type": "entity",
                "entity": me,
                "name": "Medien",
            })
        
        # Fallback: use any available entity_ids
        if not zone_cards:
            fallback_ids = zone.get("entity_ids", [])[:6]
            zone_cards = [{"type": "entity", "entity": eid, "name": ""} for eid in fallback_ids]
        
        # Wrap in glance card for compact view
        glance_entities = [e["entity"] for e in zone_cards if "entity" in e]
        if glance_entities:
            cards.append({
                "type": "horizontal-stack",
                "cards": [
                    {
                        "type": "entities",
                        "title": f"{zone_icon} {zone_name}",
                        "entities": [{"entity": e} for e in glance_entities[:8]],
                    }
                ],
            })
    
    # ── Summary footer ─────────────────────────────────────────────────────
    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {
                "type": "stat",
                "entity": "sensor.copilot_ha_pilotsuite_zones_active",
                "name": "Aktive Zonen",
                "icon": zone_icon,
            },
            {
                "type": "sensor",
                "entity": "sensor.copilot_ha_pilotsuite_zones_total",
                "name": "Zonen Gesamt",
            },
        ],
    })
    
    return {
        "title": "Zonen Overview",
        "path": "habitus-zones-live",
        "icon": "mdi:floor-plan",
        "badges": [],
        "cards": cards,
    }


def generate_zone_quick_control_card(
    zone_id: str,
    zone_name: str,
    zone_type: str = "room",
) -> dict[str, Any]:
    """Generate a compact quick-control card for a Habitus zone.
    
    Use in a grid layout for fast zone switching.
    """
    icon_map = {
        "living": "mdi:sofa", "kitchen": "mdi:silverware-fork-knife",
        "bath": "mdi:shower", "bedroom": "mdi:bed", "office": "mdi:desk",
        "hallway": "mdi:door", "room_mira": "mdi:account-girl",
        "room_paul": "mdi:account", "terrace": "mdi:tree", "outside": "mdi:leaf",
    }
    presence_entity = f"binary_sensor.pilotsuite_zone_presence_{zone_id}"
    light_group = f"light.group_{zone_id}_lights"
    climate_entity = f"climate.zone_{zone_id}_climate"
    
    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "entity",
                "entity": presence_entity,
                "name": zone_name,
                "icon": icon_map.get(zone_type, "mdi:floor-plan"),
                "hold_action": {"action": "more-info"},
                "tap_action": {"action": "navigate", "navigation_path": f"/ui-more-info/{presence_entity}"},
            },
            {
                "type": "light",
                "entity": light_group,
                "name": "Licht",
            } if light_group else {"type": "noop"},
            {
                "type": "climate",
                "entity": climate_entity,
                "name": "Klima",
            } if climate_entity else {"type": "noop"},
        ],
    }
