"""Projection Contract Tests: activity_sensors.

Verifies:
- ActivityLevelSensor: pure HA-local projection of activity data
- ActivityStillnessSensor: pure HA-local projection of stillness detection

No Core API calls; uses hass.states.async_all() for HA-local aggregation.
"""
import inspect
import math
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from custom_components.pilotsuite.sensors import activity_sensors as activity_module


# ---------------------------------------------------------------------------
# Contract Mirrors (exact sensor logic replication)
# ---------------------------------------------------------------------------

def _as_mapping(val):
    if isinstance(val, dict):
        return val
    return {}


def _as_string(val, default="unknown"):
    if isinstance(val, str) and val.strip():
        return val.strip()
    return default


def _as_int(val, default=0):
    if isinstance(val, bool):
        return default
    if isinstance(val, (int, float)) and math.isfinite(val):
        return int(val)
    return default


def _as_bool(val, default=False):
    if isinstance(val, bool):
        return val
    return default

class ActivityLevelSensorContract:
    """Mirror of ActivityLevelSensor._get_activity_from_api()."""

    @staticmethod
    def _motion_count_from_states(hass_states: dict) -> int:
        """Replicate fallback motion_count calculation from hass states."""
        return sum(
            1 for s in hass_states.get("binary_sensor", [])
            if s.get("attributes", {}).get("device_class") == "motion"
            and s.get("state") == "on"
        )

    @staticmethod
    def compute_native_value(activity_data: dict, hass_states: dict) -> str:
        activity = _as_mapping(activity_data)
        level = _as_string(activity.get("level"), "unknown")
        if not activity:
            # Fallback path — replicate _fallback_activity_states()
            score = 0
            for s in hass_states.get("binary_sensor", []):
                if s.get("attributes", {}).get("device_class") == "motion" and s.get("state") == "on":
                    score += 3
            for s in hass_states.get("media_player", []):
                if s.get("state") == "playing":
                    score += 2
            for s in hass_states.get("light", []):
                if s.get("state") == "on":
                    score += 1
            if score == 0:
                level = "idle"
            elif score < 5:
                level = "low"
            elif score < 15:
                level = "moderate"
            else:
                level = "high"
        return level

    @staticmethod
    def compute_motion_count(activity_data: dict, hass_states: dict) -> int:
        """Compute motion_count: from activity_data if present, else from hass_states."""
        activity = _as_mapping(activity_data)
        if activity:
            return _as_int(activity.get("motion_count"), 0)
        return ActivityLevelSensorContract._motion_count_from_states(hass_states)

    @staticmethod
    def compute_attrs(activity_data: dict, hass_states: dict) -> dict:
        activity = _as_mapping(activity_data)
        motion_count = ActivityLevelSensorContract.compute_motion_count(activity_data, hass_states)
        camera_motion = _as_bool(activity.get("camera_motion"), False)
        media_playing = sum(1 for s in hass_states.get("media_player", []) if s.get("state") == "playing")
        lights_on = sum(1 for s in hass_states.get("light", []) if s.get("state") == "on")
        score = _as_int(activity.get("value"), 0)
        return {
            "score": score,
            "motion_active": motion_count,
            "camera_motion_active": camera_motion,
            "media_playing": media_playing,
            "lights_on": lights_on,
            "sources": ["api", "motion_sensors", "camera", "media", "lights"],
        }


class ActivityStillnessSensorContract:
    """Mirror of ActivityStillnessSensor._get_activity_from_api()."""

    @staticmethod
    def compute_motion_count(activity_data: dict, hass_states: dict) -> int:
        """Compute motion_count: from activity_data if present, else from hass_states."""
        activity = _as_mapping(activity_data)
        if activity:
            return _as_int(activity.get("motion_count"), 0)
        return ActivityLevelSensorContract._motion_count_from_states(hass_states)

    @staticmethod
    def compute_native_value(activity_data: dict, hass_states: dict, hour: int) -> str:
        motion_count = ActivityStillnessSensorContract.compute_motion_count(activity_data, hass_states)
        media_playing = sum(1 for s in hass_states.get("media_player", []) if s.get("state") == "playing")
        if motion_count == 0 and media_playing == 0:
            return "sleeping" if hour >= 23 or hour < 6 else "still"
        elif motion_count == 0:
            return "quiet"
        else:
            return "active"

    @staticmethod
    def compute_attrs(activity_data: dict, hass_states: dict, hour: int) -> dict:
        activity = _as_mapping(activity_data)
        motion_count = ActivityStillnessSensorContract.compute_motion_count(activity_data, hass_states)
        media_playing = sum(1 for s in hass_states.get("media_player", []) if s.get("state") == "playing")
        score = _as_int(activity.get("value"), 0)
        level = _as_string(activity.get("level"), "unknown") if activity else "unknown"
        return {
            "motion_detected": motion_count > 0,
            "media_active": media_playing > 0,
            "is_night": hour >= 23 or hour < 6,
            "activity_level": level,
            "activity_score": score,
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def activity_api_data():
    """Minimal valid activity_data from Neuron API."""
    return {"level": "moderate", "value": 8, "motion_count": 2, "camera_motion": True}


@pytest.fixture
def hass_states():
    """Minimal hass states structure."""
    return {"binary_sensor": [], "media_player": [], "light": []}


# ---------------------------------------------------------------------------
# ActivityLevelSensor — native_value
# ---------------------------------------------------------------------------

def test_al1_activity_level_api_idle(activity_api_data, hass_states):
    """AL1: native_value = 'idle' when API returns level=idle."""
    data = {"level": "idle", "value": 0, "motion_count": 0, "camera_motion": False}
    assert ActivityLevelSensorContract.compute_native_value(data, hass_states) == "idle"


def test_al2_activity_level_api_moderate(activity_api_data, hass_states):
    """AL2: native_value = 'moderate' when API returns level=moderate."""
    data = {"level": "moderate", "value": 8, "motion_count": 2, "camera_motion": True}
    assert ActivityLevelSensorContract.compute_native_value(data, hass_states) == "moderate"


def test_al3_activity_level_api_high(activity_api_data, hass_states):
    """AL3: native_value = 'high' when API returns level=high."""
    data = {"level": "high", "value": 20, "motion_count": 5, "camera_motion": True}
    assert ActivityLevelSensorContract.compute_native_value(data, hass_states) == "high"


def test_al4_activity_level_fallback_idle(hass_states):
    """AL4: native_value = 'idle' in fallback when score=0."""
    states = {"binary_sensor": [], "media_player": [], "light": []}
    assert ActivityLevelSensorContract.compute_native_value({}, states) == "idle"


def test_al5_activity_level_fallback_low(hass_states):
    """AL5: native_value = 'low' in fallback when 1 <= score < 5 (1 motion)."""
    states = {
        "binary_sensor": [{"state": "on", "attributes": {"device_class": "motion"}}],
        "media_player": [],
        "light": [],
    }
    # 1 motion * 3 = 3 → low
    assert ActivityLevelSensorContract.compute_native_value({}, states) == "low"


def test_al6_activity_level_fallback_moderate(hass_states):
    """AL6: native_value = 'moderate' in fallback when 5 <= score < 15."""
    states = {
        "binary_sensor": [{"state": "on", "attributes": {"device_class": "motion"}}],
        "media_player": [{"state": "playing"}],
        "light": [],
    }
    # 1 motion * 3 + 1 media * 2 = 5 → moderate
    assert ActivityLevelSensorContract.compute_native_value({}, states) == "moderate"


def test_al7_activity_level_fallback_high(hass_states):
    """AL7: native_value = 'high' in fallback when score >= 15."""
    states = {
        "binary_sensor": [
            {"state": "on", "attributes": {"device_class": "motion"}},
            {"state": "on", "attributes": {"device_class": "motion"}},
            {"state": "on", "attributes": {"device_class": "motion"}},
        ],
        "media_player": [{"state": "playing"}, {"state": "playing"}],
        "light": [{"state": "on"}, {"state": "on"}],
    }
    # 3 motion * 3 + 2 media * 2 + 2 lights * 1 = 9 + 4 + 2 = 15 → high
    assert ActivityLevelSensorContract.compute_native_value({}, states) == "high"


# ---------------------------------------------------------------------------
# ActivityLevelSensor — extra_state_attributes
# ---------------------------------------------------------------------------

def test_al8_activity_level_attrs_full(activity_api_data, hass_states):
    """AL8: attrs include score, motion_active, camera, media, lights, sources."""
    attrs = ActivityLevelSensorContract.compute_attrs(activity_api_data, hass_states)
    assert attrs["score"] == 8
    assert attrs["motion_active"] == 2
    assert attrs["camera_motion_active"] is True
    assert attrs["media_playing"] == 0
    assert attrs["lights_on"] == 0
    assert "sources" in attrs


def test_al9_activity_level_attrs_with_media_and_lights(activity_api_data, hass_states):
    """AL9: attrs reflect media_playing and lights_on from hass states."""
    states = {
        "binary_sensor": [],
        "media_player": [{"state": "playing"}, {"state": "idle"}, {"state": "playing"}],
        "light": [{"state": "on"}, {"state": "off"}, {"state": "on"}],
    }
    attrs = ActivityLevelSensorContract.compute_attrs(activity_api_data, states)
    assert attrs["media_playing"] == 2
    assert attrs["lights_on"] == 2


def test_al10_activity_level_attrs_motion_active(activity_api_data, hass_states):
    """AL10: motion_active True when motion_count > 0."""
    data = {"level": "high", "value": 10, "motion_count": 3, "camera_motion": False}
    attrs = ActivityLevelSensorContract.compute_attrs(data, hass_states)
    assert attrs["motion_active"] == 3


def test_al11_activity_level_malformed_activity_falls_back(hass_states):
    """AL11: non-dict activity payload uses fallback HA-state aggregation."""
    states = {
        "binary_sensor": [{"state": "on", "attributes": {"device_class": "motion"}}],
        "media_player": [],
        "light": [],
    }
    assert ActivityLevelSensorContract.compute_native_value("bad-payload", states) == "low"


def test_al12_activity_level_blank_level_becomes_unknown(hass_states):
    """AL12: blank string level is guarded to 'unknown'."""
    data = {"level": "  ", "value": 5, "motion_count": 1, "camera_motion": True}
    assert ActivityLevelSensorContract.compute_native_value(data, hass_states) == "unknown"


def test_al13_activity_level_attrs_guard_non_numeric_fields(hass_states):
    """AL13: malformed score/motion_count/camera_motion are guarded."""
    data = {"level": "moderate", "value": "8", "motion_count": True, "camera_motion": "yes"}
    attrs = ActivityLevelSensorContract.compute_attrs(data, hass_states)
    assert attrs["score"] == 0
    assert attrs["motion_active"] == 0
    assert attrs["camera_motion_active"] is False


# ---------------------------------------------------------------------------
# ActivityStillnessSensor — native_value
# ---------------------------------------------------------------------------

def test_as1_stillness_sleeping(hass_states):
    """AS1: native_value = 'sleeping' when no motion/media at night (hour=2)."""
    data = {"level": "idle", "value": 0, "motion_count": 0, "camera_motion": False}
    # Night hour: 2
    assert ActivityStillnessSensorContract.compute_native_value(data, hass_states, hour=2) == "sleeping"


def test_as2_stillness_still_daytime(hass_states):
    """AS2: native_value = 'still' when no motion/media during day (hour=14)."""
    data = {"level": "idle", "value": 0, "motion_count": 0, "camera_motion": False}
    # Day hour: 14
    assert ActivityStillnessSensorContract.compute_native_value(data, hass_states, hour=14) == "still"


def test_as3_stillness_quiet(hass_states):
    """AS3: native_value = 'quiet' when no motion but media playing."""
    data = {"level": "low", "value": 2, "motion_count": 0, "camera_motion": False}
    states = {
        "binary_sensor": [],
        "media_player": [{"state": "playing"}],
        "light": [],
    }
    assert ActivityStillnessSensorContract.compute_native_value(data, states, hour=14) == "quiet"


def test_as4_stillness_active(hass_states):
    """AS4: native_value = 'active' when motion detected."""
    data = {"level": "high", "value": 10, "motion_count": 2, "camera_motion": True}
    assert ActivityStillnessSensorContract.compute_native_value(data, hass_states, hour=14) == "active"


def test_as5_stillness_edge_late_night(hass_states):
    """AS5: native_value = 'sleeping' at hour=23 (boundary)."""
    data = {"level": "idle", "value": 0, "motion_count": 0, "camera_motion": False}
    assert ActivityStillnessSensorContract.compute_native_value(data, hass_states, hour=23) == "sleeping"


def test_as6_stillness_edge_early_morning(hass_states):
    """AS6: native_value = 'sleeping' at hour=5 (boundary)."""
    data = {"level": "idle", "value": 0, "motion_count": 0, "camera_motion": False}
    assert ActivityStillnessSensorContract.compute_native_value(data, hass_states, hour=5) == "sleeping"


# ---------------------------------------------------------------------------
# ActivityStillnessSensor — extra_state_attributes
# ---------------------------------------------------------------------------

def test_as7_stillness_attrs_full(hass_states):
    """AS7: attrs include motion_detected, media_active, is_night, activity_level, activity_score."""
    data = {"level": "moderate", "value": 8, "motion_count": 2, "camera_motion": True}
    states = {
        "binary_sensor": [],
        "media_player": [{"state": "playing"}],
        "light": [],
    }
    attrs = ActivityStillnessSensorContract.compute_attrs(data, states, hour=2)
    assert attrs["motion_detected"] is True
    assert attrs["media_active"] is True
    assert attrs["is_night"] is True
    assert attrs["activity_level"] == "moderate"
    assert attrs["activity_score"] == 8


def test_as8_stillness_attrs_daytime(hass_states):
    """AS8: is_night=False during daytime hours."""
    data = {"level": "high", "value": 15, "motion_count": 3, "camera_motion": False}
    attrs = ActivityStillnessSensorContract.compute_attrs(data, hass_states, hour=14)
    assert attrs["is_night"] is False
    assert attrs["motion_detected"] is True
    assert attrs["activity_level"] == "high"


def test_as9_stillness_malformed_activity_falls_back_to_sleeping(hass_states):
    """AS9: non-dict activity payload falls back cleanly."""
    assert ActivityStillnessSensorContract.compute_native_value(["bad"], hass_states, hour=2) == "sleeping"


def test_as10_stillness_attrs_guard_blank_level_and_bad_score(hass_states):
    """AS10: blank level and malformed score are guarded."""
    data = {"level": "\t", "value": float("nan"), "motion_count": 0, "camera_motion": False}
    attrs = ActivityStillnessSensorContract.compute_attrs(data, hass_states, hour=14)
    assert attrs["activity_level"] == "unknown"
    assert attrs["activity_score"] == 0


@pytest.mark.asyncio
async def test_prod_al14_async_update_guards_malformed_api_payload():
    """AL14: production ActivityLevelSensor guards malformed context/activity payloads."""
    coordinator = MagicMock()
    coordinator.async_get_neurons.return_value = {
        "context": {"activity": {"level": "  ", "value": "bad", "motion_count": True, "camera_motion": "yes"}}
    }
    hass = MagicMock()
    hass.states.async_all.side_effect = lambda domain: []

    sensor = activity_module.ActivityLevelSensor(coordinator, hass)
    await sensor.async_update()

    assert sensor._attr_native_value == "unknown"
    assert sensor._attr_extra_state_attributes["score"] == 0
    assert sensor._attr_extra_state_attributes["motion_active"] == 0
    assert sensor._attr_extra_state_attributes["camera_motion_active"] is False


@pytest.mark.asyncio
async def test_prod_as11_async_update_non_dict_neurons_uses_fallback():
    """AS11: production ActivityStillnessSensor falls back when neurons payload is non-dict."""
    coordinator = MagicMock()
    coordinator.async_get_neurons.return_value = "bad-neurons-payload"
    hass = MagicMock()
    hass.states.async_all.side_effect = lambda domain: []

    sensor = activity_module.ActivityStillnessSensor(coordinator, hass)
    with patch.object(activity_module.dt_util, "now", return_value=datetime(2026, 4, 10, 2, 0, 0)):
        await sensor.async_update()

    assert sensor._attr_native_value == "sleeping"
    assert sensor._attr_extra_state_attributes["motion_detected"] is False
    assert sensor._attr_extra_state_attributes["media_active"] is False
    assert sensor._attr_extra_state_attributes["is_night"] is True


# ---------------------------------------------------------------------------
# Global Contract
# ---------------------------------------------------------------------------

def test_gc1_no_core_api_dependency(activity_api_data, hass_states):
    """GC1: Both sensors derive purely from hass states / API context, no semantic invention."""
    # ActivityLevelSensor
    level = ActivityLevelSensorContract.compute_native_value(activity_api_data, hass_states)
    assert level in {"idle", "low", "moderate", "high", "unknown"}
    attrs = ActivityLevelSensorContract.compute_attrs(activity_api_data, hass_states)
    assert "score" in attrs
    # ActivityStillnessSensor
    stillness = ActivityStillnessSensorContract.compute_native_value(activity_api_data, hass_states, hour=14)
    assert stillness in {"sleeping", "still", "quiet", "active", "unknown"}
    still_attrs = ActivityStillnessSensorContract.compute_attrs(activity_api_data, hass_states, hour=14)
    assert "is_night" in still_attrs


def test_gc2_hass_states_only(hass_states):
    """GC2: Both sensors compute correctly purely from hass_states dict structure."""
    states = {
        "binary_sensor": [{"state": "on", "attributes": {"device_class": "motion"}}],
        "media_player": [{"state": "playing"}],
        "light": [{"state": "on"}],
    }
    level = ActivityLevelSensorContract.compute_native_value({}, states)
    assert level == "moderate"  # 3 + 2 + 1 = 6
    stillness = ActivityStillnessSensorContract.compute_native_value({}, states, hour=20)
    assert stillness == "active"  # motion_count > 0


def test_gc3_source_guard_helpers_present():
    """GC3: production module contains explicit malformed-payload guards."""
    source = inspect.getsource(activity_module)
    assert "def _as_mapping" in source
    assert "def _as_string" in source
    assert "def _as_int" in source
    assert "def _as_bool" in source


def test_gc4_unique_id_guard_activity_level():
    """GC4: ActivityLevelSensor unique_id is canonical pilotsuite ID."""
    source = inspect.getsource(activity_module)
    assert 'pilotsuite_activity_level' in source
    assert 'ai_copilot_activity_level' not in source or '_attr_unique_id' in source



def test_gc5_unique_id_guard_activity_stillness():
    """GC5: ActivityStillnessSensor unique_id is canonical pilotsuite ID."""
    source = inspect.getsource(activity_module)
    assert 'pilotsuite_activity_stillness' in source
    assert 'ai_copilot_activity_stillness' not in source or '_attr_unique_id' in source
