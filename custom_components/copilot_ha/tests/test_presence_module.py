"""Tests for presence module (PS-148).

Tests:
- Presence source classification
- Multi-source aggregation
- Confidence calculation
- Absence timeout
- Zone presence state
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from datetime import datetime, timezone, timedelta

from custom_components.copilot_ha.presence_module import (
    PresenceSource,
    ZonePresenceState,
    _get_entity_source_type,
    async_collect_zone_presence,
    SOURCE_WEIGHTS,
    ABSENCE_TIMEOUTS,
)


class TestSourceClassification:
    """Tests for entity source type classification."""

    def test_presence_device_class(self):
        assert _get_entity_source_type("binary_sensor.presence", "presence") == "presence"

    def test_occupancy_device_class(self):
        assert _get_entity_source_type("binary_sensor.occupancy", "occupancy") == "occupancy"

    def test_motion_device_class(self):
        assert _get_entity_source_type("binary_sensor.motion", "motion") == "motion"

    def test_mmwave_keyword(self):
        assert _get_entity_source_type("binary_sensor.mmwave", None) == "occupancy"
        assert _get_entity_source_type("binary_sensor.mm_wave", None) == "occupancy"
        assert _get_entity_source_type("binary_sensor.radar", None) == "occupancy"

    def test_tof_keyword(self):
        assert _get_entity_source_type("binary_sensor.tof", None) == "presence"

    def test_pir_keyword(self):
        assert _get_entity_source_type("binary_sensor.pir", None) == "motion"

    def test_device_tracker(self):
        assert _get_entity_source_type("device_tracker.phone", None) == "device_tracker"
        assert _get_entity_source_type("sensor.ble_tracker", None) == "device_tracker"

    def test_power(self):
        assert _get_entity_source_type("sensor.power", None) == "power"
        assert _get_entity_source_type("sensor.energy", None) == "power"

    def test_sound(self):
        assert _get_entity_source_type("sensor.sound", None) == "sound"
        assert _get_entity_source_type("sensor.noise", None) == "sound"

    def test_default_fallback(self):
        assert _get_entity_source_type("binary_sensor.unknown", None) == "motion"


class TestSourceWeights:
    """Tests for source confidence weights."""

    def test_presence_weight(self):
        assert SOURCE_WEIGHTS["presence"] == 1.0

    def test_occupancy_weight(self):
        assert SOURCE_WEIGHTS["occupancy"] == 0.9

    def test_motion_weight(self):
        assert SOURCE_WEIGHTS["motion"] == 0.7

    def test_device_tracker_weight(self):
        assert SOURCE_WEIGHTS["device_tracker"] == 0.6

    def test_power_weight(self):
        assert SOURCE_WEIGHTS["power"] == 0.5

    def test_sound_weight(self):
        assert SOURCE_WEIGHTS["sound"] == 0.4


class TestPresenceSource:
    """Tests for PresenceSource dataclass."""

    def test_default_values(self):
        source = PresenceSource(
            entity_id="binary_sensor.motion",
            source_type="motion",
            confidence=0.7,
        )
        assert source.entity_id == "binary_sensor.motion"
        assert source.source_type == "motion"
        assert source.confidence == 0.7
        assert source.last_triggered is None
        assert source.state == "off"

    def test_active_source(self):
        now = datetime.now(tz=timezone.utc)
        source = PresenceSource(
            entity_id="binary_sensor.motion",
            source_type="motion",
            confidence=0.7,
            last_triggered=now,
            state="on",
        )
        assert source.state == "on"
        assert source.last_triggered == now


class TestZonePresenceState:
    """Tests for ZonePresenceState dataclass."""

    def test_absent_state(self):
        state = ZonePresenceState(
            zone_id="zone:test",
            zone_name="Test",
        )
        assert state.is_present is False
        assert state.confidence == 0.0
        assert state.source_count == 0
        assert len(state.active_sources) == 0
        assert state.last_detected is None
        assert state.absence_duration_minutes == 0.0

    def test_present_state(self):
        now = datetime.now(tz=timezone.utc)
        state = ZonePresenceState(
            zone_id="zone:test",
            zone_name="Test",
            is_present=True,
            confidence=0.8,
            source_count=3,
            active_sources=["binary_sensor.motion1", "binary_sensor.motion2", "binary_sensor.presence"],
            last_detected=now,
            absence_duration_minutes=0.0,
        )
        assert state.is_present is True
        assert state.confidence == 0.8
        assert state.source_count == 3
        assert len(state.active_sources) == 3


@pytest.mark.asyncio
async def test_collect_presence_all_off():
    """Test presence collection when all sensors are off."""
    hass = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    
    entity_ids = ["binary_sensor.motion", "binary_sensor.presence"]
    
    presence = await async_collect_zone_presence(hass, "zone:test", entity_ids)
    
    assert presence.is_present is False
    assert presence.confidence == 0.0
    assert presence.source_count == 0


@pytest.mark.asyncio
async def test_collect_presence_motion_only():
    """Test presence collection with motion sensor active."""
    hass = MagicMock()
    
    motion_state = MagicMock()
    motion_state.state = "on"
    motion_state.attributes = {"device_class": "motion"}
    
    hass.states.get = MagicMock(side_effect=lambda eid: {
        "binary_sensor.motion": motion_state,
    }.get(eid))
    
    presence = await async_collect_zone_presence(
        hass, "zone:wohn", ["binary_sensor.motion"]
    )
    
    assert presence.is_present is True
    assert presence.confidence == 0.7  # Motion weight
    assert presence.source_count == 1
    assert "binary_sensor.motion" in presence.active_sources


@pytest.mark.asyncio
async def test_collect_presence_multiple_sources():
    """Test presence collection with multiple active sources."""
    hass = MagicMock()
    
    motion_state = MagicMock()
    motion_state.state = "on"
    motion_state.attributes = {"device_class": "motion"}
    
    presence_state = MagicMock()
    presence_state.state = "on"
    presence_state.attributes = {"device_class": "presence"}
    
    hass.states.get = MagicMock(side_effect=lambda eid: {
        "binary_sensor.motion": motion_state,
        "binary_sensor.presence": presence_state,
    }.get(eid))
    
    presence = await async_collect_zone_presence(
        hass, "zone:wohn", ["binary_sensor.motion", "binary_sensor.presence"]
    )
    
    assert presence.is_present is True
    assert presence.confidence == 1.0  # Capped at 1.0 (0.7 + 1.0 = 1.7 → 1.0)
    assert presence.source_count == 2
    assert len(presence.active_sources) == 2


@pytest.mark.asyncio
async def test_collect_presence_absence_duration():
    """Test absence duration calculation."""
    hass = MagicMock()
    
    # All sensors off
    hass.states.get = MagicMock(return_value=None)
    
    presence = await async_collect_zone_presence(
        hass, "zone:test", ["binary_sensor.motion"]
    )
    
    assert presence.is_present is False
    assert presence.absence_duration_minutes == 0.0  # No last_detected


@pytest.mark.asyncio
async def test_collect_presence_power_sensor():
    """Test presence detection from power sensor."""
    hass = MagicMock()
    
    power_state = MagicMock()
    power_state.state = "50.0"  # 50W
    power_state.attributes = {}
    
    hass.states.get = MagicMock(side_effect=lambda eid: {
        "sensor.power": power_state,
    }.get(eid))
    
    presence = await async_collect_zone_presence(
        hass, "zone:office", ["sensor.power"]
    )
    
    assert presence.is_present is True
    assert presence.confidence == 0.5  # Power weight
    assert "sensor.power" in presence.active_sources


@pytest.mark.asyncio
async def test_collect_presence_device_tracker():
    """Test presence detection from device tracker."""
    hass = MagicMock()
    
    tracker_state = MagicMock()
    tracker_state.state = "home"
    tracker_state.attributes = {}
    
    hass.states.get = MagicMock(side_effect=lambda eid: {
        "device_tracker.phone": tracker_state,
    }.get(eid))
    
    presence = await async_collect_zone_presence(
        hass, "zone:wohn", ["device_tracker.phone"]
    )
    
    assert presence.is_present is True
    assert presence.confidence == 0.6  # Device tracker weight
