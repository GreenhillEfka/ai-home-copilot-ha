#!/usr/bin/env python3
"""PS-178: Area-to-Zone Mapping Registry Loader.

Loads explicit area→zone mapping from JSON config.
Supports 1:1, N:1 aggregations, and unmatched fallback.

Usage:
  from .area_zone_registry import load_area_zone_map
  area_zone_map = load_area_zone_map(hass)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _get_config_path() -> Path:
    """Get path to area zone map config file."""
    return Path(__file__).parent / "config" / "area_zone_map.json"


def load_area_zone_map() -> dict[str, Any]:
    """
    Load area-to-zone mapping from JSON config.
    
    Returns:
        Dict with mappings, aggregation_rules, zone_types, unmatched_fallback
    """
    config_path = _get_config_path()
    
    if not config_path.exists():
        _LOGGER.warning("[PS-178] Area zone map config not found: %s", config_path)
        return _get_default_map()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        _LOGGER.info(
            "[PS-178] Loaded area zone map: %d mappings, %d aggregation rules",
            len(config.get("mappings", [])),
            len(config.get("aggregation_rules", [])),
        )
        
        return config
    except json.JSONDecodeError as exc:
        _LOGGER.error("[PS-178] Invalid JSON in area zone map: %s", exc)
        return _get_default_map()
    except Exception as exc:
        _LOGGER.error("[PS-178] Error loading area zone map: %s", exc)
        return _get_default_map()


def _get_default_map() -> dict[str, Any]:
    """Return default fallback mapping."""
    return {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "unmatched_fallback": "ungeordnet",
        "mappings": [],
        "aggregation_rules": [],
        "zone_types": {"ungeordnet": "fallback"},
    }


def get_zone_for_area(area_id: str, config: dict[str, Any]) -> str | None:
    """
    Get zone ID for a given area ID.
    
    Args:
        area_id: Home Assistant area ID
        config: Loaded area zone map config
    
    Returns:
        Zone ID or None if not mapped
    """
    for mapping in config.get("mappings", []):
        if mapping.get("area_id") == area_id:
            return mapping.get("zone_id")
    
    return None


def get_aggregated_areas(zone_id: str, config: dict[str, Any]) -> list[str]:
    """
    Get all area IDs that aggregate to a given zone.
    
    Args:
        zone_id: Target zone ID
        config: Loaded area zone map config
    
    Returns:
        List of area IDs that map to this zone
    """
    area_ids = []
    for mapping in config.get("mappings", []):
        if mapping.get("zone_id") == zone_id:
            area_ids.append(mapping["area_id"])
    return area_ids


def get_zone_type(zone_id: str, config: dict[str, Any]) -> str:
    """
    Get zone type from config.
    
    Args:
        zone_id: Zone ID
        config: Loaded area zone map config
    
    Returns:
        Zone type (area, room, fallback)
    """
    zone_types = config.get("zone_types", {})
    return zone_types.get(zone_id, "area")


def get_unmatched_fallback(config: dict[str, Any]) -> str:
    """
    Get fallback zone for unmatched areas.
    
    Args:
        config: Loaded area zone map config
    
    Returns:
        Fallback zone ID (default: "ungeordnet")
    """
    return config.get("unmatched_fallback", "ungeordnet")


def validate_mapping(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate area zone map config.
    
    Args:
        config: Loaded area zone map config
    
    Returns:
        (valid, errors) tuple
    """
    errors = []
    
    # Check required fields
    required = ["version", "unmatched_fallback", "mappings", "zone_types"]
    for field in required:
        if field not in config:
            errors.append(f"missing required field: {field}")
    
    # Check mappings have required fields
    for i, mapping in enumerate(config.get("mappings", [])):
        if "area_id" not in mapping:
            errors.append(f"mapping[{i}] missing area_id")
        if "zone_id" not in mapping:
            errors.append(f"mapping[{i}] missing zone_id")
        if "confidence" in mapping and not (0.0 <= mapping["confidence"] <= 1.0):
            errors.append(f"mapping[{i}] confidence out of range: {mapping['confidence']}")
    
    # Check zone_types are valid
    valid_types = {"area", "room", "fallback"}
    for zone_id, zone_type in config.get("zone_types", {}).items():
        if zone_type not in valid_types:
            errors.append(f"zone_types[{zone_id}] invalid type: {zone_type}")
    
    return len(errors) == 0, errors
