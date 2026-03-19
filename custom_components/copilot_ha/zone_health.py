"""Zone Health Sensor — per-zone health metrics (PS-138).

Provides per-zone health status:
- Temperature: current, min, max, comfort range
- Humidity: current, min, max, comfort range
- CO2: current, air quality level
- Light: brightness, lux level
- Overall health score (0-100)

Called during zone auto-setup to initialize health tracking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class ZoneHealthMetrics:
    """Health metrics for a single zone."""
    zone_id: str
    zone_name: str
    
    # Temperature
    temperature: float | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    temperature_comfort: bool = True
    
    # Humidity
    humidity: float | None = None
    humidity_min: float | None = None
    humidity_max: float | None = None
    humidity_comfort: bool = True
    
    # CO2 / Air Quality
    co2: float | None = None
    air_quality: str = "good"  # good, moderate, poor
    
    # Light
    brightness: float | None = None
    lux: float | None = None
    
    # Overall health
    health_score: float = 100.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# Comfort ranges
TEMP_COMFORT_MIN = 18.0
TEMP_COMFORT_MAX = 26.0
HUMIDITY_COMFORT_MIN = 30.0
HUMIDITY_COMFORT_MAX = 70.0
CO2_GOOD_MAX = 800.0
CO2_MODERATE_MAX = 1200.0


def _get_health_score(metrics: ZoneHealthMetrics) -> float:
    """Calculate overall health score (0-100)."""
    score = 100.0
    
    # Temperature penalty
    if metrics.temperature is not None:
        if metrics.temperature < TEMP_COMFORT_MIN:
            score -= min(20, (TEMP_COMFORT_MIN - metrics.temperature) * 2)
        elif metrics.temperature > TEMP_COMFORT_MAX:
            score -= min(20, (metrics.temperature - TEMP_COMFORT_MAX) * 2)
    
    # Humidity penalty
    if metrics.humidity is not None:
        if metrics.humidity < HUMIDITY_COMFORT_MIN:
            score -= min(15, (HUMIDITY_COMFORT_MIN - metrics.humidity) * 0.5)
        elif metrics.humidity > HUMIDITY_COMFORT_MAX:
            score -= min(15, (metrics.humidity - HUMIDITY_COMFORT_MAX) * 0.5)
    
    # CO2 penalty
    if metrics.co2 is not None:
        if metrics.co2 > CO2_MODERATE_MAX:
            score -= 25
        elif metrics.co2 > CO2_GOOD_MAX:
            score -= min(15, (metrics.co2 - CO2_GOOD_MAX) * 0.05)
    
    return max(0.0, min(100.0, score))


def _get_air_quality(co2: float | None) -> str:
    """Determine air quality from CO2 level."""
    if co2 is None:
        return "unknown"
    if co2 <= CO2_GOOD_MAX:
        return "good"
    if co2 <= CO2_MODERATE_MAX:
        return "moderate"
    return "poor"


def collect_zone_health_metrics(
    hass: HomeAssistant,
    zone_id: str,
    zone_name: str,
    entity_ids: list[str],
) -> ZoneHealthMetrics:
    """Collect health metrics from zone entities."""
    metrics = ZoneHealthMetrics(zone_id=zone_id, zone_name=zone_name)
    
    temp_entities = []
    humidity_entities = []
    co2_entities = []
    light_entities = []
    
    # Categorize entities
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if not state:
            continue
        
        device_class = state.attributes.get("device_class")
        entity_id_lower = entity_id.lower()
        
        # Temperature sensors
        if device_class == "temperature" or "temperature" in entity_id_lower or "temp" in entity_id_lower:
            try:
                temp_entities.append(float(state.state))
            except (ValueError, TypeError):
                pass
        
        # Humidity sensors
        if device_class == "humidity" or "humidity" in entity_id_lower or "humid" in entity_id_lower:
            try:
                humidity_entities.append(float(state.state))
            except (ValueError, TypeError):
                pass
        
        # CO2 sensors
        if device_class == "carbon_dioxide" or "co2" in entity_id_lower or "carbon" in entity_id_lower:
            try:
                co2_entities.append(float(state.state))
            except (ValueError, TypeError):
                pass
        
        # Light sensors
        if device_class == "illuminance" or "illuminance" in entity_id_lower or "illumin" in entity_id_lower:
            try:
                light_entities.append(float(state.state))
            except (ValueError, TypeError):
                pass
    
    # Aggregate metrics
    if temp_entities:
        metrics.temperature = sum(temp_entities) / len(temp_entities)
        metrics.temperature_min = min(temp_entities)
        metrics.temperature_max = max(temp_entities)
        metrics.temperature_comfort = TEMP_COMFORT_MIN <= metrics.temperature <= TEMP_COMFORT_MAX
    
    if humidity_entities:
        metrics.humidity = sum(humidity_entities) / len(humidity_entities)
        metrics.humidity_min = min(humidity_entities)
        metrics.humidity_max = max(humidity_entities)
        metrics.humidity_comfort = HUMIDITY_COMFORT_MIN <= metrics.humidity <= HUMIDITY_COMFORT_MAX
    
    if co2_entities:
        metrics.co2 = max(co2_entities)  # Use worst reading
        metrics.air_quality = _get_air_quality(metrics.co2)
    
    if light_entities:
        metrics.lux = max(light_entities)  # Use brightest reading
    
    # Calculate health score
    metrics.health_score = _get_health_score(metrics)
    metrics.last_updated = datetime.now(tz=timezone.utc)
    
    return metrics


async def async_update_all_zone_health(
    hass: HomeAssistant,
    zones: list[Any],
) -> dict[str, ZoneHealthMetrics]:
    """Update health metrics for all zones."""
    health_map: dict[str, ZoneHealthMetrics] = {}
    
    for zone in zones:
        zone_id = zone.zone_id
        zone_name = zone.name
        entity_ids = list(zone.entity_ids) if hasattr(zone, "entity_ids") else []
        
        metrics = collect_zone_health_metrics(hass, zone_id, zone_name, entity_ids)
        health_map[zone_id] = metrics
        
        _LOGGER.debug(
            "Zone %s health: score=%.1f, temp=%.1f, humid=%.1f, co2=%.0f, air=%s",
            zone_name,
            metrics.health_score,
            metrics.temperature or 0,
            metrics.humidity or 0,
            metrics.co2 or 0,
            metrics.air_quality,
        )
    
    return health_map
