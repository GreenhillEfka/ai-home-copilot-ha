"""Tests for presence-health correlation (PS-150).

Tests:
- Correlation calculation
- Occupancy health impact
- Absence degradation risk
- Recommended actions
- Multi-zone insights
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from datetime import datetime, timezone, timedelta

from custom_components.copilot_ha.zone_health import ZoneHealthMetrics
from custom_components.copilot_ha.presence_module import ZonePresenceState
from custom_components.copilot_ha.presence_health_correlation import (
    PresenceHealthCorrelation,
    _calculate_occupancy_health_impact,
    _calculate_absence_degradation_risk,
    _determine_recommended_action,
    async_correlate_presence_health,
    async_get_presence_health_insights,
)


class TestOccupancyHealthImpact:
    """Tests for occupancy health impact calculation."""

    def test_positive_occupied_good_health(self):
        impact = _calculate_occupancy_health_impact(
            presence_confidence=0.8,
            health_score=85.0,
            co2=600.0,
        )
        assert impact == "positive"

    def test_negative_occupied_high_co2(self):
        impact = _calculate_occupancy_health_impact(
            presence_confidence=0.7,
            health_score=65.0,
            co2=1500.0,
        )
        assert impact == "negative"

    def test_neutral_occupied_moderate(self):
        impact = _calculate_occupancy_health_impact(
            presence_confidence=0.6,
            health_score=70.0,
            co2=900.0,
        )
        assert impact == "neutral"

    def test_positive_unoccupied_excellent(self):
        impact = _calculate_occupancy_health_impact(
            presence_confidence=0.1,
            health_score=95.0,
            co2=400.0,
        )
        assert impact == "positive"

    def test_neutral_unoccupied_good(self):
        impact = _calculate_occupancy_health_impact(
            presence_confidence=0.2,
            health_score=80.0,
            co2=500.0,
        )
        assert impact == "neutral"


class TestAbsenceDegradationRisk:
    """Tests for absence degradation risk calculation."""

    def test_short_absence_low_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=15.0,
            health_score=75.0,
            temperature=22.0,
            humidity=50.0,
        )
        assert risk == "low"

    def test_medium_absence_good_health_low_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=90.0,
            health_score=80.0,
            temperature=21.0,
            humidity=45.0,
        )
        assert risk == "low"

    def test_medium_absence_poor_health_medium_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=90.0,
            health_score=45.0,
            temperature=20.0,
            humidity=50.0,
        )
        assert risk == "medium"

    def test_long_absence_poor_health_high_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=180.0,
            health_score=40.0,
            temperature=22.0,
            humidity=50.0,
        )
        assert risk == "high"

    def test_long_absence_extreme_temp_high_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=150.0,
            health_score=70.0,
            temperature=12.0,  # Very cold
            humidity=50.0,
        )
        assert risk == "high"

    def test_long_absence_extreme_humid_medium_risk(self):
        risk = _calculate_absence_degradation_risk(
            absence_duration_minutes=150.0,
            health_score=70.0,
            temperature=22.0,
            humidity=85.0,  # Very humid
        )
        assert risk == "medium"


class TestRecommendedAction:
    """Tests for recommended action determination."""

    def test_occupied_poor_health_high_co2_ventilate(self):
        action = _determine_recommended_action(
            presence_confidence=0.8,
            health_score=45.0,
            co2=1500.0,
            temperature=22.0,
            humidity=50.0,
            air_quality="poor",
        )
        assert action == "ventilate"

    def test_occupied_poor_health_notify(self):
        action = _determine_recommended_action(
            presence_confidence=0.7,
            health_score=40.0,
            co2=800.0,
            temperature=22.0,
            humidity=50.0,
            air_quality="good",
        )
        assert action == "notify"

    def test_occupied_moderate_health_high_co2_ventilate(self):
        action = _determine_recommended_action(
            presence_confidence=0.6,
            health_score=65.0,
            co2=1100.0,
            temperature=22.0,
            humidity=50.0,
            air_quality="moderate",
        )
        assert action == "ventilate"

    def test_occupied_moderate_health_cold_climate_adjust(self):
        action = _determine_recommended_action(
            presence_confidence=0.6,
            health_score=70.0,
            co2=600.0,
            temperature=16.0,  # Cold
            humidity=50.0,
            air_quality="good",
        )
        assert action == "climate_adjust"

    def test_occupied_moderate_health_humid_climate_adjust(self):
        action = _determine_recommended_action(
            presence_confidence=0.6,
            health_score=70.0,
            co2=600.0,
            temperature=22.0,
            humidity=75.0,  # Humid
            air_quality="good",
        )
        assert action == "climate_adjust"

    def test_unoccupied_poor_health_notify(self):
        action = _determine_recommended_action(
            presence_confidence=0.1,
            health_score=45.0,
            co2=600.0,
            temperature=22.0,
            humidity=50.0,
            air_quality="good",
        )
        assert action == "notify"

    def test_good_conditions_no_action(self):
        action = _determine_recommended_action(
            presence_confidence=0.5,
            health_score=90.0,
            co2=500.0,
            temperature=22.0,
            humidity=50.0,
            air_quality="good",
        )
        assert action == "none"


class TestPresenceHealthCorrelation:
    """Tests for PresenceHealthCorrelation dataclass."""

    def test_default_values(self):
        corr = PresenceHealthCorrelation(
            zone_id="zone:test",
            zone_name="Test",
        )
        assert corr.zone_id == "zone:test"
        assert corr.zone_name == "Test"
        assert corr.health_score == 100.0
        assert corr.presence_confidence == 0.0
        assert corr.occupancy_health_impact == "neutral"
        assert corr.absence_degradation_risk == "low"
        assert corr.recommended_action == "none"


@pytest.mark.asyncio
async def test_correlate_present_zone_good_health():
    """Test correlation for present zone with good health."""
    hass = MagicMock()
    
    presence = ZonePresenceState(
        zone_id="zone:wohn",
        zone_name="Wohnbereich",
        is_present=True,
        confidence=0.8,
        source_count=3,
        active_sources=["binary_sensor.motion1", "binary_sensor.motion2", "binary_sensor.presence"],
    )
    
    health = ZoneHealthMetrics(
        zone_id="zone:wohn",
        zone_name="Wohnbereich",
        health_score=85.0,
        temperature=22.0,
        humidity=50.0,
        co2=600.0,
        air_quality="good",
    )
    
    corr = await async_correlate_presence_health(hass, "zone:wohn", presence, health)
    
    assert corr.zone_id == "zone:wohn"
    assert corr.presence_confidence == 0.8
    assert corr.health_score == 85.0
    assert corr.occupancy_health_impact == "positive"
    assert corr.absence_degradation_risk == "low"
    assert corr.recommended_action == "none"


@pytest.mark.asyncio
async def test_correlate_present_zone_poor_health():
    """Test correlation for present zone with poor health."""
    hass = MagicMock()
    
    presence = ZonePresenceState(
        zone_id="zone:wohn",
        zone_name="Wohnbereich",
        is_present=True,
        confidence=0.7,
        source_count=2,
    )
    
    health = ZoneHealthMetrics(
        zone_id="zone:wohn",
        zone_name="Wohnbereich",
        health_score=45.0,
        temperature=22.0,
        humidity=50.0,
        co2=1400.0,
        air_quality="poor",
    )
    
    corr = await async_correlate_presence_health(hass, "zone:wohn", presence, health)
    
    assert corr.presence_confidence == 0.7
    assert corr.health_score == 45.0
    assert corr.occupancy_health_impact == "negative"
    assert corr.recommended_action == "ventilate"


@pytest.mark.asyncio
async def test_get_presence_health_insights():
    """Test insights generation from correlations."""
    hass = MagicMock()
    
    correlations = {
        "zone:wohn": PresenceHealthCorrelation(
            zone_id="zone:wohn",
            zone_name="Wohnbereich",
            presence_confidence=0.8,
            health_score=85.0,
            recommended_action="none",
        ),
        "zone:bad": PresenceHealthCorrelation(
            zone_id="zone:bad",
            zone_name="Badbereich",
            presence_confidence=0.6,
            health_score=45.0,
            recommended_action="ventilate",
        ),
        "zone:koch": PresenceHealthCorrelation(
            zone_id="zone:koch",
            zone_name="Kochbereich",
            presence_confidence=0.2,
            health_score=40.0,
            recommended_action="notify",
        ),
    }
    
    insights = await async_get_presence_health_insights(hass, "test_entry", correlations)
    
    assert insights["total_zones"] == 3
    assert insights["occupied_zones"] == 2  # wohn + bad
    assert insights["zones_with_poor_health"] == 2  # bad + koch
    assert insights["zones_needing_action"] == 2  # bad + koch
    assert len(insights["recommendations"]) == 2
