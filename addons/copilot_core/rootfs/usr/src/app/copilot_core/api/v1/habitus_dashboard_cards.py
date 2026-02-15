"""
habitus_dashboard_cards API endpoint (v0.2)

Provides dashboard pattern recommendations and templates for Home Assistant Lovelace.
Features:
- Zone-aware patterns from Habitus Miner
- Dynamic card generation based on discovered rules
- Real-time integration with Brain Graph
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging

_LOGGER = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


bp = Blueprint("habitus_dashboard_cards", __name__, url_prefix="/habitus/dashboard_cards")


@bp.get("")
def get_dashboard_patterns():
    """
    Return recommended dashboard patterns and card templates.
    
    Query params:
    - type: "overview" | "room" | "energy" | "sleep" | "zone" (default: all)
    - format: "yaml" | "json" (default: json)
    - zone: zone_id for zone-specific patterns (e.g., "kitchen", "zone:living_room")
    """
    pattern_type = request.args.get("type", "all").lower()
    output_format = request.args.get("format", "json").lower()
    zone_id = request.args.get("zone")

    patterns = _get_patterns(pattern_type, zone_id)

    return jsonify({
        "ok": True,
        "time": _now_iso(),
        "type": pattern_type,
        "zone": zone_id,
        "format": output_format,
        "patterns": patterns,
        "documentation": "/docs/module_specs/habitus_dashboard_cards_v0.2.md"
    })


@bp.get("/zones")
def get_zones():
    """Get list of available zones for dashboard generation."""
    # TODO: Integrate with Brain Graph zones
    return jsonify({
        "ok": True,
        "time": _now_iso(),
        "zones": [
            {"id": "zone:kitchen", "name": "Kitchen", "entities": 12},
            {"id": "zone:living_room", "name": "Living Room", "entities": 18},
            {"id": "zone:bedroom", "name": "Bedroom", "entities": 8},
            {"id": "zone:bathroom", "name": "Bathroom", "entities": 5},
        ],
        "note": "Placeholder - will be populated from Brain Graph"
    })


@bp.get("/zone/<zone_id>")
def get_zone_patterns(zone_id):
    """
    Get zone-specific patterns and dashboard templates.
    
    Path params:
    - zone_id: Zone identifier (e.g., "kitchen" or "zone:kitchen")
    """
    # Normalize zone_id
    if not zone_id.startswith("zone:"):
        zone_id = f"zone:{zone_id}"
    
    patterns = _get_patterns("zone", zone_id)
    
    return jsonify({
        "ok": True,
        "time": _now_iso(),
        "zone_id": zone_id,
        "patterns": patterns
    })


@bp.get("/rules")
def get_rule_cards():
    """
    Generate dashboard cards from discovered A→B rules.
    
    Query params:
    - min_confidence: Minimum confidence threshold (default: 0.7)
    - limit: Maximum number of rules to include (default: 10)
    - zone: Filter by zone (optional)
    """
    min_confidence = request.args.get("min_confidence", 0.7, type=float)
    limit = request.args.get("limit", 10, type=int)
    zone = request.args.get("zone")
    
    # TODO: Integrate with Habitus Miner service
    # For now, return template structure
    cards = _generate_rule_cards(min_confidence, limit, zone)
    
    return jsonify({
        "ok": True,
        "time": _now_iso(),
        "cards": cards,
        "config": {
            "min_confidence": min_confidence,
            "limit": limit,
            "zone": zone
        }
    })


def _get_patterns(pattern_type: str, zone_id: str = None) -> dict:
    """Return pattern templates based on type and zone."""
    
    base_patterns = {
        "principles": {
            "hierarchy": "Overview → Diagnosis → Detail",
            "time_windows": ["24h (operational)", "7 days (trend)", "30 days (seasonality)"],
            "max_lines_per_graph": 3,
            "title_convention": "Always include time window, e.g. '(24h)'",
            "zone_aware": True
        },
        "recommended_cards": {
            "status": ["tile", "entities", "glance"],
            "trends": ["history-graph", "statistics-graph"],
            "events": ["logbook"],
            "layout": ["grid", "vertical-stack", "horizontal-stack"],
            "habitus": ["custom:habitus-zone-card", "custom:habitus-rules-card"]
        }
    }

    templates = {}

    if pattern_type in ("all", "overview"):
        templates["overview"] = {
            "description": "Main overview page with tiles + drill-down",
            "example": {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.room_temperature",
                        "name": "Temperature",
                        "state_content": ["state", "last_changed"],
                        "tap_action": {
                            "action": "navigate",
                            "navigation_path": "/dashboard-habitus/room-detail"
                        }
                    },
                    {
                        "type": "custom:habitus-zone-card",
                        "zone": "zone:kitchen",
                        "show_rules": True
                    }
                ]
            }
        }

    if pattern_type in ("all", "room"):
        templates["room_detail"] = {
            "description": "Room detail page: status + short-term + long-term trends + events",
            "sections": [
                {
                    "purpose": "Current status",
                    "card_type": "entities",
                    "entities": ["temperature", "humidity", "co2", "window_status"]
                },
                {
                    "purpose": "Short-term trend (24h)",
                    "card_type": "history-graph",
                    "hours_to_show": 24,
                    "entities": ["temperature", "humidity"]
                },
                {
                    "purpose": "Long-term aggregated trend (7 days)",
                    "card_type": "statistics-graph",
                    "period": "day",
                    "days_to_show": 7,
                    "stat_types": ["mean", "min", "max"],
                    "entities": ["temperature"]
                },
                {
                    "purpose": "Events (24h)",
                    "card_type": "logbook",
                    "hours_to_show": 24,
                    "entities": ["binary_sensor.motion", "binary_sensor.door"]
                },
                {
                    "purpose": "Habitus patterns",
                    "card_type": "custom:habitus-rules-card",
                    "config": {
                        "zone": zone_id,
                        "min_confidence": 0.7
                    }
                }
            ]
        }

    if pattern_type in ("all", "energy"):
        templates["energy"] = {
            "description": "Energy consumption patterns",
            "example": {
                "type": "vertical-stack",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.power_consumption",
                        "name": "Current Power (W)"
                    },
                    {
                        "type": "statistics-graph",
                        "title": "Daily Energy (7 days)",
                        "period": "day",
                        "days_to_show": 7,
                        "stat_types": ["sum"],
                        "entities": ["sensor.energy_kwh"]
                    },
                    {
                        "type": "custom:habitus-rules-card",
                        "config": {
                            "domain": "energy",
                            "show_suggestions": True
                        }
                    }
                ]
            }
        }

    if pattern_type in ("all", "sleep"):
        templates["sleep"] = {
            "description": "Sleep/rest patterns",
            "example": {
                "type": "vertical-stack",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.sleep_duration_last_night",
                        "name": "Last Night Sleep"
                    },
                    {
                        "type": "statistics-graph",
                        "title": "Sleep Duration - Weekly Mean",
                        "period": "week",
                        "stat_types": ["mean"],
                        "entities": ["sensor.sleep_duration"]
                    }
                ]
            }
        }

    if pattern_type in ("all", "zone") and zone_id:
        templates["zone_specific"] = {
            "description": f"Zone-specific patterns for {zone_id}",
            "zone_id": zone_id,
            "cards": [
                {
                    "type": "custom:habitus-zone-card",
                    "zone": zone_id,
                    "show_rules": True,
                    "show_trends": True,
                    "time_window": "24h"
                },
                {
                    "type": "history-graph",
                    "title": f"{zone_id.replace('zone:', '').replace('_', ' ').title()} Activity (24h)",
                    "hours_to_show": 24,
                    "entities": []  # To be filled with zone entities
                }
            ],
            "note": "Entities populated from Brain Graph zone query"
        }

    return {
        "base": base_patterns,
        "templates": templates
    }


def _generate_rule_cards(min_confidence: float, limit: int, zone: str = None) -> list:
    """Generate dashboard cards from discovered A→B rules."""
    
    # TODO: Call Habitus Miner service to get real rules
    # For now, return a template structure
    
    cards = []
    
    # Template for rule-based cards
    rule_card_template = {
        "type": "custom:habitus-rule-card",
        "title": "Discovered Patterns",
        "config": {
            "min_confidence": min_confidence,
            "limit": limit,
            "zone": zone,
            "show_confidence": True,
            "show_lift": True,
            "show_actions": True
        }
    }
    
    cards.append(rule_card_template)
    
    # Template for suggestions card
    suggestions_card = {
        "type": "custom:habitus-suggestions-card",
        "title": "Automation Suggestions",
        "config": {
            "zone": zone,
            "min_confidence": min_confidence,
            "show_create_automation": True
        }
    }
    
    cards.append(suggestions_card)
    
    return cards


@bp.get("/health")
def health():
    """Health check for dashboard_cards module."""
    return jsonify({
        "ok": True,
        "time": _now_iso(),
        "module": "habitus_dashboard_cards",
        "version": "0.2.0",
        "features": [
            "zone_aware_patterns",
            "rule_based_cards",
            "dynamic_templates"
        ],
        "status": "active"
    })