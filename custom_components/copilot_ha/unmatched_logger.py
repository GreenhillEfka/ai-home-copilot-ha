#!/usr/bin/env python3
"""PS-179: Unmatched Entity Logger for Zone Auto-Setup.

Logs entities that cannot be matched to any area/zone.
Provides suggested_zone (if uncertain) and fallback to "ungeordnet".

Usage:
  from .unmatched_logger import log_unmatched_entities
  log_unmatched_entities(hass, entities, area_zone_map)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _get_log_path() -> Path:
    """Get path to unmatched entities log file."""
    return Path("/config/clawd/pilotsuite_ops/logs/unmatched_entities.log")


def _ensure_log_dir() -> None:
    """Ensure log directory exists."""
    log_path = _get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)


def log_unmatched_entities(
    entities: list[dict[str, Any]],
    area_zone_map: dict[str, str],
    zone_fallback: str = "ungeordnet",
) -> list[dict[str, Any]]:
    """
    Log entities that cannot be matched to any area/zone.
    
    Args:
        entities: List of entity dicts with entity_id, area_id (optional)
        area_zone_map: Mapping of area_id → zone_id
        zone_fallback: Fallback zone for unmatched entities
    
    Returns:
        List of unmatched entity records with logging metadata
    """
    _ensure_log_dir()
    
    unmatched = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for entity in entities:
        entity_id = entity.get("entity_id", "unknown")
        area_id = entity.get("area_id")
        
        # Check if area is mapped to a zone
        if not area_id or area_id not in area_zone_map:
            # Entity is unmatched
            record = {
                "timestamp": timestamp,
                "entity_id": entity_id,
                "area_id": area_id,
                "suggested_zone": _suggest_zone(entity),
                "fallback": zone_fallback,
                "reason": "no_area_match" if not area_id else "area_not_mapped",
            }
            unmatched.append(record)
            
            # Log as WARNING
            _LOGGER.warning(
                "[PS-179] Unmatched entity: %s (area=%s, suggested=%s, fallback=%s)",
                entity_id,
                area_id or "none",
                record["suggested_zone"] or "unknown",
                zone_fallback,
            )
    
    # Write to log file
    if unmatched:
        log_path = _get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            for record in unmatched:
                f.write(f"{record['timestamp']} | {record['entity_id']} | {record['area_id']} | {record['suggested_zone']} | {record['fallback']}\n")
    
    return unmatched


def _suggest_zone(entity: dict[str, Any]) -> str | None:
    """
    Suggest a zone based on entity type/name patterns.
    
    Returns None if no suggestion can be made.
    """
    entity_id = entity.get("entity_id", "")
    entity_type = entity.get("entity_type", "")
    
    # Pattern-based suggestions
    suggestions = {
        "climate": "climate_zone",
        "temperature": "climate_zone",
        "thermostat": "climate_zone",
        "light": "lighting_zone",
        "brightness": "lighting_zone",
        "motion": "security_zone",
        "binary_sensor": "security_zone",
        "cover": "comfort_zone",
        "blind": "comfort_zone",
        "power": "energy_zone",
        "energy": "energy_zone",
        "music": "comfort_zone",
        "media": "comfort_zone",
    }
    
    for keyword, zone in suggestions.items():
        if keyword in entity_id.lower():
            return zone
    
    return None


def get_unmatched_summary(hours: int = 24) -> dict[str, Any]:
    """
    Get summary of unmatched entities from log file.
    
    Args:
        hours: Lookback period in hours
    
    Returns:
        Summary dict with counts and recent entries
    """
    from datetime import timedelta
    
    log_path = _get_log_path()
    if not log_path.exists():
        return {"total": 0, "recent": [], "generated_at": datetime.now(timezone.utc).isoformat()}
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    total = 0
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) < 5:
                    continue
                ts_str = parts[0]
                try:
                    ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                
                total += 1
                if ts >= cutoff:
                    recent.append({
                        "timestamp": ts_str,
                        "entity_id": parts[1],
                        "area_id": parts[2],
                        "suggested_zone": parts[3],
                        "fallback": parts[4],
                    })
    except Exception:
        pass
    
    return {
        "total": total,
        "recent": recent[:20],  # Limit to 20 recent entries
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
