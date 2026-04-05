"""Projection Contract Tests: inspector_sensor.py

Verifies: InspectorSensor is a pure diagnostic projection shell on
coordinator.data — no local semantic invention.

Sensors:
- InspectorSensor(zones): mirrors zones count + zones dict
- InspectorSensor(tags): mirrors tags count + tags dict
- InspectorSensor(character): mirrors character.preset
- InspectorSensor(mood): mirrors mood.current

Contract verified:
- state = raw count or single string value from coordinator.data
- attrs = raw dict passthrough from coordinator.data
- No local classification or heuristic
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# === Fixtures ===

@pytest.fixture
def coordinator():
    return MagicMock()


@pytest.fixture
def zones_sensor(coordinator):
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    return InspectorSensor(coordinator, "zones", "Habitus Zones", "mdi:floor-plan")


@pytest.fixture
def tags_sensor(coordinator):
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    return InspectorSensor(coordinator, "tags", "Active Tags", "mdi:tag-multiple")


@pytest.fixture
def character_sensor(coordinator):
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    return InspectorSensor(coordinator, "character", "Character Profile", "mdi:account-cog")


@pytest.fixture
def mood_sensor(coordinator):
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    return InspectorSensor(coordinator, "mood", "Current Mood", "mdi:emoticon")


# === IS1: zones ===

def test_inspector_zones_is1_no_data(coordinator, zones_sensor):
    """IS1: No coordinator data → 'unknown'"""
    coordinator.data = None
    assert zones_sensor.state == "unknown"


def test_inspector_zones_is1_empty_zones(coordinator, zones_sensor):
    """IS1: Empty zones dict → 0"""
    coordinator.data = {"zones": {"zones": []}}
    assert zones_sensor.state == 0


def test_inspector_zones_is1_with_zones(coordinator, zones_sensor):
    """IS1: Zones list → len count"""
    coordinator.data = {"zones": {"zones": [{"id": "z1"}, {"id": "z2"}, {"id": "z3"}]}}
    assert zones_sensor.state == 3


# === IS2: tags ===

def test_inspector_tags_is2_no_data(coordinator, tags_sensor):
    """IS2: No coordinator data → 'unknown'"""
    coordinator.data = None
    assert tags_sensor.state == "unknown"


def test_inspector_tags_is2_empty_tags(coordinator, tags_sensor):
    """IS2: Empty tags dict → 0"""
    coordinator.data = {"tags": {"tags": []}}
    assert tags_sensor.state == 0


def test_inspector_tags_is2_with_tags(coordinator, tags_sensor):
    """IS2: Tags list → len count"""
    coordinator.data = {"tags": {"tags": [{"id": "t1"}, {"id": "t2"}]}}
    assert tags_sensor.state == 2


# === IS3: character ===

def test_inspector_character_is3_no_data(coordinator, character_sensor):
    """IS3: No coordinator data → 'unknown'"""
    coordinator.data = None
    assert character_sensor.state == "unknown"


def test_inspector_character_is3_preset(coordinator, character_sensor):
    """IS3: character.preset string passthrough"""
    coordinator.data = {"character": {"preset": "friendly", "tone": "casual"}}
    assert character_sensor.state == "friendly"


def test_inspector_character_is3_no_preset_key(coordinator, character_sensor):
    """IS3: No preset key → 'not set'"""
    coordinator.data = {"character": {"tone": "casual"}}
    assert character_sensor.state == "not set"


# === IS4: mood ===

def test_inspector_mood_is4_no_data(coordinator, mood_sensor):
    """IS4: No coordinator data → 'unknown'"""
    coordinator.data = None
    assert mood_sensor.state == "unknown"


def test_inspector_mood_is4_current(coordinator, mood_sensor):
    """IS4: mood.current string passthrough"""
    coordinator.data = {"mood": {"current": "content", "intensity": 0.7}}
    assert mood_sensor.state == "content"


def test_inspector_mood_is4_no_current_key(coordinator, mood_sensor):
    """IS4: No current key → 'unknown'"""
    coordinator.data = {"mood": {"intensity": 0.7}}
    assert mood_sensor.state == "unknown"


# === IS5: attrs ===

def test_inspector_is5_zones_attrs(coordinator, zones_sensor):
    """IS5: zones attrs carry raw zones dict"""
    coordinator.data = {"zones": {"zones": [{"id": "z1"}], "version": 2}}
    attrs = zones_sensor.extra_state_attributes
    assert attrs["zones"] == {"zones": [{"id": "z1"}], "version": 2}


def test_inspector_is5_tags_attrs(coordinator, tags_sensor):
    """IS5: tags attrs carry raw tags dict"""
    coordinator.data = {"tags": {"tags": [{"id": "t1"}], "count": 1}}
    attrs = tags_sensor.extra_state_attributes
    assert attrs["tags"] == {"tags": [{"id": "t1"}], "count": 1}


def test_inspector_is5_character_attrs(coordinator, character_sensor):
    """IS5: character attrs carry raw character dict"""
    coordinator.data = {"character": {"preset": "friendly", "tone": "casual"}}
    attrs = character_sensor.extra_state_attributes
    assert attrs["character"] == {"preset": "friendly", "tone": "casual"}


def test_inspector_is5_mood_attrs(coordinator, mood_sensor):
    """IS5: mood attrs carry raw mood dict"""
    coordinator.data = {"mood": {"current": "content", "intensity": 0.7}}
    attrs = mood_sensor.extra_state_attributes
    assert attrs["mood"] == {"current": "content", "intensity": 0.7}


# === GC: Global Contract ===

def test_inspector_gc1_pure_projection_zones(coordinator, zones_sensor):
    """GC1: InspectorSensor(zones) is pure projection shell on coordinator.data['zones']"""
    coordinator.data = {"zones": {"zones": [{"id": "z1"}]}}
    assert zones_sensor.state == 1
    assert zones_sensor.extra_state_attributes["zones"] == {"zones": [{"id": "z1"}]}


def test_inspector_gc1_pure_projection_mood(coordinator, mood_sensor):
    """GC1: InspectorSensor(mood) is pure projection shell on coordinator.data['mood']"""
    coordinator.data = {"mood": {"current": "content", "intensity": 0.7}}
    assert mood_sensor.state == "content"
    assert mood_sensor.extra_state_attributes["mood"] == {"current": "content", "intensity": 0.7}


def test_inspector_gc2_no_local_semantic_invention(coordinator, zones_sensor):
    """GC2: No local semantic invention — all state comes verbatim from coordinator.data"""
    coordinator.data = {
        "zones": {"zones": [{"id": "z1", "label": "Wohnzimmer"}]},
        "mood": {"current": "content", "intensity": 0.7},
        "character": {"preset": "friendly", "custom": True},
        "tags": {"tags": [{"id": "t1"}]},
    }

    # Sensor does NOT classify zones by type
    # Sensor does NOT compute mood intensity locally
    # Sensor does NOT transform character presets
    # Sensor just mirrors raw coordinator.data values
    assert zones_sensor.state == 1
    assert zones_sensor.extra_state_attributes["zones"] == {"zones": [{"id": "z1", "label": "Wohnzimmer"}]}
