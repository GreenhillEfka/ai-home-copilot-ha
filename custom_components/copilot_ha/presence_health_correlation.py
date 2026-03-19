"""Presence-Health Correlation — Correlate presence with health metrics (PS-149).

Correlates:
- Presence duration vs health score trends
- Absence periods vs climate degradation
- Multi-source presence confidence vs air quality
- Occupancy patterns vs health automation triggers

Provides insights for predictive health adjustments.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from homeassistant.core import HomeAssistant

from .zone_health import ZoneHealthMetrics
from .presence_module import ZonePresenceState

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


@dataclass
class PresenceHealthCorrelation:
    """Correlation between presence and health for a zone."""
    zone_id: str
    zone_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    
    # Presence metrics
    presence_confidence: float = 0.0
    presence_duration_minutes: float = 0.0
    source_count: int = 0
    
    # Health metrics
    health_score: float = 100.0
    temperature: float | None = None
    humidity: float | None = None
    co2: float | None = None
    air_quality: str = "unknown"
    
    # Correlation insights
    occupancy_health_impact: str = "neutral"  # positive, neutral, negative
    absence_degradation_risk: str = "low"  # low, medium, high
    recommended_action: str = "none"  # ventilate, climate_adjust, notify, none


def _calculate_occupancy_health_impact(
    presence_confidence: float,
    health_score: float,
    co2: float | None,
) -> str:
    """Determine if occupancy is positively/neutral/negatively impacting health."""
    if presence_confidence > 0.5:
        # Occupied zone
        if health_score >= 75:
            return "positive"  # Good health despite occupancy
        if co2 is not None and co2 > 1000:
            return "negative"  # High CO2 from occupancy
        return "neutral"
    else:
        # Unoccupied zone
        if health_score >= 90:
            return "positive"  # Excellent health when empty
        return "neutral"


def _calculate_absence_degradation_risk(
    absence_duration_minutes: float,
    health_score: float,
    temperature: float | None,
    humidity: float | None,
) -> str:
    """Determine risk of health degradation during absence."""
    if absence_duration_minutes < 30:
        return "low"
    
    if absence_duration_minutes < 120:
        if health_score < 60:
            return "medium"
        return "low"
    
    # Long absence (>2 hours)
    if health_score < 50:
        return "high"
    if temperature is not None and (temperature < 15 or temperature > 30):
        return "high"
    if humidity is not None and (humidity < 20 or humidity > 80):
        return "medium"
    return "low"


def _determine_recommended_action(
    presence_confidence: float,
    health_score: float,
    co2: float | None,
    temperature: float | None,
    humidity: float | None,
    air_quality: str,
) -> str:
    """Determine recommended action based on presence-health correlation."""
    # High priority: occupied + poor health
    if presence_confidence > 0.5 and health_score < 50:
        if co2 is not None and co2 > 1200:
            return "ventilate"
        return "notify"
    
    # Medium priority: occupied + moderate health issues
    if presence_confidence > 0.5 and health_score < 75:
        if co2 is not None and co2 > 1000:
            return "ventilate"
        if temperature is not None and (temperature < 18 or temperature > 26):
            return "climate_adjust"
        if humidity is not None and (humidity < 30 or humidity > 70):
            return "climate_adjust"
    
    # Low priority: unoccupied + poor health (preventive)
    if presence_confidence < 0.3 and health_score < 60:
        return "notify"
    
    return "none"


async def async_correlate_presence_health(
    hass: HomeAssistant,
    zone_id: str,
    presence: ZonePresenceState,
    health: ZoneHealthMetrics,
) -> PresenceHealthCorrelation:
    """Correlate presence and health metrics for a zone."""
    correlation = PresenceHealthCorrelation(
        zone_id=zone_id,
        zone_name=health.zone_name,
        presence_confidence=presence.confidence,
        presence_duration_minutes=0.0,  # Would need historical data
        source_count=presence.source_count,
        health_score=health.health_score,
        temperature=health.temperature,
        humidity=health.humidity,
        co2=health.co2,
        air_quality=health.air_quality,
    )
    
    # Calculate correlations
    correlation.occupancy_health_impact = _calculate_occupancy_health_impact(
        presence.confidence,
        health.health_score,
        health.co2,
    )
    
    correlation.absence_degradation_risk = _calculate_absence_degradation_risk(
        presence.absence_duration_minutes,
        health.health_score,
        health.temperature,
        health.humidity,
    )
    
    correlation.recommended_action = _determine_recommended_action(
        presence.confidence,
        health.health_score,
        health.co2,
        health.temperature,
        health.humidity,
        health.air_quality,
    )
    
    _LOGGER.debug(
        "Zone %s correlation: presence=%.2f, health=%.1f, impact=%s, risk=%s, action=%s",
        zone_id,
        presence.confidence,
        health.health_score,
        correlation.occupancy_health_impact,
        correlation.absence_degradation_risk,
        correlation.recommended_action,
    )
    
    return correlation


async def async_correlate_all_zones(
    hass: HomeAssistant,
    entry_id: str,
    presence_map: dict[str, ZonePresenceState],
    health_map: dict[str, ZoneHealthMetrics],
) -> dict[str, PresenceHealthCorrelation]:
    """Correlate presence and health for all zones."""
    correlations: dict[str, PresenceHealthCorrelation] = {}
    
    for zone_id in presence_map.keys():
        if zone_id not in health_map:
            continue
        
        presence = presence_map[zone_id]
        health = health_map[zone_id]
        
        correlation = await async_correlate_presence_health(
            hass, zone_id, presence, health
        )
        correlations[zone_id] = correlation
    
    return correlations


async def async_get_presence_health_insights(
    hass: HomeAssistant,
    entry_id: str,
    correlations: dict[str, PresenceHealthCorrelation],
) -> dict[str, Any]:
    """Generate insights from presence-health correlations."""
    insights = {
        "entry_id": entry_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "total_zones": len(correlations),
        "occupied_zones": 0,
        "zones_with_poor_health": 0,
        "zones_needing_action": 0,
        "recommendations": [],
    }
    
    for zone_id, corr in correlations.items():
        if corr.presence_confidence > 0.3:
            insights["occupied_zones"] += 1
        
        if corr.health_score < 50:
            insights["zones_with_poor_health"] += 1
        
        if corr.recommended_action != "none":
            insights["zones_needing_action"] += 1
            insights["recommendations"].append({
                "zone_id": zone_id,
                "zone_name": corr.zone_name,
                "action": corr.recommended_action,
                "reason": f"Health {corr.health_score:.0f}, Presence {corr.presence_confidence:.2f}",
            })
    
    return insights
