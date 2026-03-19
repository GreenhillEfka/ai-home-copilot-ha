"""Tests for zone health module (PS-144).

Tests:
- ZoneHealthMetrics collection
- Health score calculation
- Air quality classification
- Service handlers
- Automation triggers
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.copilot_ha.zone_health import (
    ZoneHealthMetrics,
    collect_zone_health_metrics,
    _get_health_score,
    _get_air_quality,
    TEMP_COMFORT_MIN,
    TEMP_COMFORT_MAX,
    HUMIDITY_COMFORT_MIN,
    HUMIDITY_COMFORT_MAX,
    CO2_GOOD_MAX,
    CO2_MODERATE_MAX,
)

from custom_components.copilot_ha.zone_health_card import (
    HealthCardState,
    HealthCardConfig,
    create_health_card_state,
    _get_score_category,
    _get_temp_status,
    _get_humidity_status,
    _get_light_status,
)


class TestZoneHealthMetrics:
    """Tests for ZoneHealthMetrics dataclass."""

    def test_default_values(self):
        metrics = ZoneHealthMetrics(zone_id="zone:test", zone_name="Test")
        assert metrics.zone_id == "zone:test"
        assert metrics.zone_name == "Test"
        assert metrics.health_score == 100.0
        assert metrics.temperature is None
        assert metrics.humidity is None
        assert metrics.co2 is None
        assert metrics.air_quality == "good"


class TestHealthScoreCalculation:
    """Tests for health score calculation."""

    def test_perfect_score(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:test",
            zone_name="Test",
            temperature=22.0,
            humidity=50.0,
            co2=400.0,
        )
        score = _get_health_score(metrics)
        assert score == 100.0

    def test_cold_penalty(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:test",
            zone_name="Test",
            temperature=15.0,  # Below comfort min
        )
        score = _get_health_score(metrics)
        assert score < 100.0
        assert score >= 80.0  # 6 degrees * 2 = 12 point penalty

    def test_hot_penalty(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:test",
            zone_name="Test",
            temperature=28.0,  # Above comfort max
        )
        score = _get_health_score(metrics)
        assert score < 100.0

    def test_humid_penalty(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:test",
            zone_name="Test",
            humidity=80.0,  # Above comfort max
        )
        score = _get_health_score(metrics)
        assert score < 100.0

    def test_co2_moderate_penalty(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:test",
            zone_name="Test",
            co2=1000.0,  # Above good threshold
        )
        score = _get_health_score(metrics)
        assert score < 100.0
        assert score >= 85.0


class TestAirQualityClassification:
    """Tests for air quality classification."""

    def test_good_air(self):
        assert _get_air_quality(400.0) == "good"
        assert _get_air_quality(800.0) == "good"

    def test_moderate_air(self):
        assert _get_air_quality(900.0) == "moderate"
        assert _get_air_quality(1200.0) == "moderate"

    def test_poor_air(self):
        assert _get_air_quality(1500.0) == "poor"
        assert _get_air_quality(2000.0) == "poor"

    def test_unknown_air(self):
        assert _get_air_quality(None) == "unknown"


class TestScoreCategory:
    """Tests for score category classification."""

    def test_excellent(self):
        assert _get_score_category(95.0) == "excellent"
        assert _get_score_category(90.0) == "excellent"

    def test_good(self):
        assert _get_score_category(80.0) == "good"
        assert _get_score_category(75.0) == "good"

    def test_fair(self):
        assert _get_score_category(60.0) == "fair"
        assert _get_score_category(50.0) == "fair"

    def test_poor(self):
        assert _get_score_category(40.0) == "poor"
        assert _get_score_category(0.0) == "poor"


class TestTemperatureStatus:
    """Tests for temperature status classification."""

    def test_normal(self):
        assert _get_temp_status(22.0) == "normal"
        assert _get_temp_status(20.0) == "normal"

    def test_cold(self):
        assert _get_temp_status(15.0) == "cold"
        assert _get_temp_status(10.0) == "cold"

    def test_hot(self):
        assert _get_temp_status(28.0) == "hot"
        assert _get_temp_status(30.0) == "hot"

    def test_unknown(self):
        assert _get_temp_status(None) == "unknown"


class TestHumidityStatus:
    """Tests for humidity status classification."""

    def test_normal(self):
        assert _get_humidity_status(50.0) == "normal"
        assert _get_humidity_status(45.0) == "normal"

    def test_dry(self):
        assert _get_humidity_status(20.0) == "dry"
        assert _get_humidity_status(25.0) == "dry"

    def test_humid(self):
        assert _get_humidity_status(80.0) == "humid"
        assert _get_humidity_status(85.0) == "humid"

    def test_unknown(self):
        assert _get_humidity_status(None) == "unknown"


class TestLightStatus:
    """Tests for light status classification."""

    def test_normal(self):
        assert _get_light_status(500.0) == "normal"
        assert _get_light_status(300.0) == "normal"

    def test_dim(self):
        assert _get_light_status(50.0) == "dim"
        assert _get_light_status(90.0) == "dim"

    def test_bright(self):
        assert _get_light_status(1500.0) == "bright"
        assert _get_light_status(2000.0) == "bright"

    def test_unknown(self):
        assert _get_light_status(None) == "unknown"


class TestHealthCardState:
    """Tests for health card state creation."""

    def test_create_from_metrics(self):
        metrics = ZoneHealthMetrics(
            zone_id="zone:wohn",
            zone_name="Wohnbereich",
            temperature=22.0,
            humidity=50.0,
            co2=600.0,
            lux=400.0,
        )
        state = create_health_card_state(metrics)
        
        assert state.zone_id == "zone:wohn"
        assert state.zone_name == "Wohnbereich"
        assert state.health_score == 100.0
        assert state.score_category == "excellent"
        assert state.temperature_status == "normal"
        assert state.humidity_status == "normal"
        assert state.air_quality == "good"
        assert state.light_status == "normal"


@pytest.mark.asyncio
async def test_collect_metrics_from_mock_entities():
    """Test collecting metrics from mock HA entities."""
    hass = MagicMock()
    
    # Mock states
    temp_state = MagicMock()
    temp_state.state = "22.5"
    temp_state.attributes = {"device_class": "temperature"}
    
    humid_state = MagicMock()
    humid_state.state = "48.0"
    humid_state.attributes = {"device_class": "humidity"}
    
    co2_state = MagicMock()
    co2_state.state = "650.0"
    co2_state.attributes = {"device_class": "carbon_dioxide"}
    
    hass.states.get = MagicMock(side_effect=lambda eid: {
        "sensor.temp": temp_state,
        "sensor.humid": humid_state,
        "sensor.co2": co2_state,
    }.get(eid))
    
    entity_ids = ["sensor.temp", "sensor.humid", "sensor.co2"]
    
    metrics = collect_zone_health_metrics(
        hass, "zone:test", "Test Zone", entity_ids
    )
    
    assert metrics.temperature == 22.5
    assert metrics.humidity == 48.0
    assert metrics.co2 == 650.0
    assert metrics.air_quality == "good"
    assert metrics.health_score == 100.0
