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
    """Tab 5: Musik — Sonos / Musikwolke control."""
    core_url = f"http://{host}:{port}"
    return {
        "title": "Musik",
        "path": "musik",
        "icon": "mdi:speaker-group",
        "badges": [],
        "cards": [
            # Sonos overview iframe
            {
                "type": "iframe",
                "url": f"{core_url}/api/v1/sonos/summary",
                "title": "Sonos-Uebersicht",
                "aspect_ratio": "16:9",
            },
            # Media Follow sensor
            {
                "type": "entities",
                "title": "Musikwolke",
                "entities": [
                    {"entity": "sensor.pilotsuite_media_follow", "name": "Follow-Status"},
                ],
            },
            # Quick controls (markdown with instructions)
            {
                "type": "markdown",
                "title": "Musikwolke-Steuerung",
                "content": (
                    "### Musikwolke\n"
                    "Die Musikwolke folgt Ihnen automatisch durch die Raeume.\n\n"
                    "**Aktive Gruppen:** Siehe Sonos-Uebersicht oben.\n\n"
                    "Steuerung ueber:\n"
                    "- Styx Chat: *\"Spiele Musik im Wohnzimmer\"*\n"
                    "- HA Automation: `copilot_ha.send_event`\n"
                    f"- API: `POST {core_url}/api/v1/sonos/musikwolke/create`"
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


def dashboard_to_yaml(
    host: str,
    port: int,
    zones: list[dict[str, Any]] | None = None,
) -> str:
    """Generate full dashboard as YAML string for Lovelace import."""
    dashboard = generate_styx_dashboard(host, port, zones=zones)
    return _yaml_dump(dashboard)
