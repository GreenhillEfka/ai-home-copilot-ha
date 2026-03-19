"""Presence Module — Multi-source presence aggregation (PS-147).

Aggregates presence from multiple sources:
- Motion sensors (PIR)
- Occupancy sensors (mmWave)
- Presence sensors (ToF)
- Device tracker (BLE/WiFi)
- Light/Power consumption
- Sound/Noise levels

Provides unified presence state per zone.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


@dataclass
class PresenceSource:
    """A single presence sensor source."""
    entity_id: str
    source_type: str  # motion, occupancy, presence, device_tracker, power, sound
    confidence: float  # 0.0-1.0
    last_triggered: datetime | None = None
    state: str = "off"


@dataclass
class ZonePresenceState:
    """Aggregated presence state for a zone."""
    zone_id: str
    zone_name: str
    is_present: bool = False
    confidence: float = 0.0
    source_count: int = 0
    active_sources: list[str] = field(default_factory=list)
    last_detected: datetime | None = None
    absence_duration_minutes: float = 0.0


# Source type confidence weights
SOURCE_WEIGHTS = {
    "presence": 1.0,  # ToF, mmWave presence
    "occupancy": 0.9,  # mmWave occupancy
    "motion": 0.7,  # PIR motion
    "device_tracker": 0.6,  # BLE/WiFi
    "power": 0.5,  # Power consumption
    "sound": 0.4,  # Sound detection
}

# Absence timeout per source type (minutes)
ABSENCE_TIMEOUTS = {
    "presence": 5,
    "occupancy": 10,
    "motion": 3,
    "device_tracker": 15,
    "power": 30,
    "sound": 1,
}


def _get_entity_source_type(entity_id: str, device_class: str | None) -> str:
    """Determine source type from entity."""
    entity_lower = entity_id.lower()
    
    if device_class == "presence":
        return "presence"
    if device_class == "occupancy":
        return "occupancy"
    if device_class == "motion":
        return "motion"
    
    if "mmwave" in entity_lower or "mm_wave" in entity_lower or "radar" in entity_lower:
        return "occupancy"
    if "presence" in entity_lower or "tof" in entity_lower:
        return "presence"
    if "motion" in entity_lower or "pir" in entity_lower:
        return "motion"
    if "device_tracker" in entity_lower or "ble" in entity_lower or "wifi" in entity_lower:
        return "device_tracker"
    if "power" in entity_lower or "energy" in entity_lower:
        return "power"
    if "sound" in entity_lower or "noise" in entity_lower or "audio" in entity_lower:
        return "sound"
    
    return "motion"  # Default fallback


async def async_collect_zone_presence(
    hass: HomeAssistant,
    zone_id: str,
    entity_ids: list[str],
) -> ZonePresenceState:
    """Collect and aggregate presence from zone entities."""
    sources: list[PresenceSource] = []
    now = datetime.now(tz=timezone.utc)
    
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if not state:
            continue
        
        device_class = state.attributes.get("device_class")
        source_type = _get_entity_source_type(entity_id, device_class)
        
        # Determine state
        try:
            state_value = state.state
            if source_type in ("motion", "occupancy", "presence"):
                is_on = state_value in ("on", "true", "1")
            elif source_type == "device_tracker":
                is_on = state_value in ("home", "connected")
            elif source_type == "power":
                is_on = float(state_value) > 10.0  # > 10W
            elif source_type == "sound":
                is_on = float(state_value) > 30.0  # > 30dB
            else:
                is_on = False
        except (ValueError, TypeError):
            is_on = False
        
        if is_on:
            last_triggered = now
            confidence = SOURCE_WEIGHTS.get(source_type, 0.5)
        else:
            # Check if within timeout window
            last_triggered = None
            confidence = 0.0
        
        sources.append(PresenceSource(
            entity_id=entity_id,
            source_type=source_type,
            confidence=confidence,
            last_triggered=last_triggered,
            state="on" if is_on else "off",
        ))
    
    # Aggregate presence
    active_sources = [s for s in sources if s.last_triggered is not None]
    total_confidence = sum(s.confidence for s in active_sources)
    
    # Normalize confidence (max 1.0)
    normalized_confidence = min(1.0, total_confidence)
    
    # Determine presence
    is_present = normalized_confidence > 0.3  # Threshold for presence
    
    # Last detected time
    last_detected = None
    if active_sources:
        last_detected = max(s.last_triggered for s in active_sources if s.last_triggered)
    
    # Absence duration
    absence_duration = 0.0
    if not is_present and last_detected:
        absence_duration = (now - last_detected).total_seconds() / 60.0
    
    # Find zone name from entity metadata or fallback
    zone_name = zone_id.replace("zone:", "").replace("_", " ").title()
    
    return ZonePresenceState(
        zone_id=zone_id,
        zone_name=zone_name,
        is_present=is_present,
        confidence=normalized_confidence,
        source_count=len(sources),
        active_sources=[s.entity_id for s in active_sources],
        last_detected=last_detected,
        absence_duration_minutes=absence_duration,
    )


async def async_aggregate_all_zone_presence(
    hass: HomeAssistant,
    entry_id: str,
    zones: list[Any],
) -> dict[str, ZonePresenceState]:
    """Aggregate presence for all zones."""
    presence_map: dict[str, ZonePresenceState] = {}
    
    for zone in zones:
        zone_id = zone.zone_id
        entity_ids = list(zone.entity_ids) if hasattr(zone, "entity_ids") else []
        
        presence = await async_collect_zone_presence(hass, zone_id, entity_ids)
        presence_map[zone_id] = presence
        
        _LOGGER.debug(
            "Zone %s presence: %s (confidence=%.2f, sources=%d)",
            zone.name,
            "present" if presence.is_present else "absent",
            presence.confidence,
            presence.source_count,
        )
    
    return presence_map


async def async_setup_presence_tracking(hass: HomeAssistant, entry_id: str) -> None:
    """Set up presence tracking for a config entry."""
    from .habitus_zones_store_v2 import async_get_zones_v2
    
    zones = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.debug("No zones found, skipping presence tracking")
        return
    
    # Store presence state in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][f"presence_tracking_{entry_id}"] = {
        "enabled": True,
        "zones": [z.zone_id for z in zones],
        "last_update": datetime.now(tz=timezone.utc),
    }
    
    _LOGGER.info("Presence tracking set up for %d zones", len(zones))
