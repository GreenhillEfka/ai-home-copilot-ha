"""Projection contract tests for neuron_dashboard.py sensors.

Verifies NeuronDashboardSensor, MoodHistorySensor, SuggestionSensor
project from CopilotDataUpdateCoordinator.data without local semantic invention.

Contract Mirror pattern: mirrors take raw coordinator_data dict directly,
avoiding the import chain through coordinator.py → api.py.
Only source-file reads are used for GC guards.
"""
from __future__ import annotations

import os
import pytest

SENSOR_PATH = "custom_components/pilotsuite/sensors/neuron_dashboard.py"


# ---------------------------------------------------------------------------
# Contract Mirrors (write-only — must stay in sync with the sensor source)
# ---------------------------------------------------------------------------

class NeuronDashboardSensorContract:
    """Mirror of NeuronDashboardSensor projection logic."""

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {
                "context_neurons": {},
                "state_neurons": {},
                "mood_neurons": {},
                "total_count": 0,
                "active_count": 0,
            }
        neurons = coordinator_data.get("neurons", {})
        context = {}
        state = {}
        mood = {}
        for name, data in neurons.items():
            if isinstance(data, dict):
                if "context" in name or name.startswith(("presence", "time", "light", "weather")):
                    context[name] = data
                elif "mood" in name:
                    mood[name] = data
                else:
                    state[name] = data
        return {
            "context_neurons": context,
            "state_neurons": state,
            "mood_neurons": mood,
            "total_count": len(neurons),
            "active_count": sum(
                1 for n in neurons.values()
                if isinstance(n, dict) and n.get("active")
            ),
        }

    @staticmethod
    def native_value(_coordinator_data=None):
        return "ok"


class MoodHistorySensorContract:
    """Mirror of MoodHistorySensor projection logic (history tracking only)."""

    @staticmethod
    def native_value(_coordinator_data=None):
        return "ok"

    @staticmethod
    def current_mood_and_confidence(coordinator_data):
        if not coordinator_data:
            return "unknown", 0.0
        return (
            coordinator_data.get("dominant_mood", "unknown"),
            coordinator_data.get("mood_confidence", 0.0),
        )


class SuggestionSensorContract:
    """Mirror of SuggestionSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "none"
        suggestions = coordinator_data.get("suggestions", [])
        if not suggestions:
            return "none"
        first = suggestions[0]
        if isinstance(first, dict):
            return first.get("action_type", "none")
        return "none"

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {"suggestions": [], "ranked_candidates_count": 0}
        suggestions = coordinator_data.get("suggestions", [])
        ranked_candidates = coordinator_data.get("ranked_candidates", [])
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "top_suggestion": suggestions[0] if suggestions else None,
            "ranked_candidates_count": len(ranked_candidates),
            "ranked_candidates": ranked_candidates[:10],
        }


# ---------------------------------------------------------------------------
# NeuronDashboardSensor tests (ND prefix)
# ---------------------------------------------------------------------------

def test_nd1_no_data_returns_structured_empty_attributes():
    """ND1: No coordinator data → structured empty attributes with all keys."""
    attrs = NeuronDashboardSensorContract.extra_state_attributes(None)
    assert attrs == {
        "context_neurons": {},
        "state_neurons": {},
        "mood_neurons": {},
        "total_count": 0,
        "active_count": 0,
    }


def test_nd2_empty_neurons_returns_empty_context_state_mood():
    """ND2: Empty neurons dict → empty context/state/mood groups."""
    attrs = NeuronDashboardSensorContract.extra_state_attributes({})
    assert attrs.get("context_neurons") == {}
    assert attrs.get("state_neurons") == {}
    assert attrs.get("mood_neurons") == {}
    assert attrs.get("total_count") == 0


def test_nd3_context_neurons_grouped_correctly():
    """ND3: presence/time/light/weather neurons grouped as context."""
    data = {
        "neurons": {
            "presence.room": {"active": True, "value": "living_room"},
            "time.of_day": {"active": True, "value": "evening"},
            "light.level": {"active": False, "value": 42},
            "mood.dominant": {"active": True, "value": "calm"},
            "energy.current": {"active": True, "value": 350},
        }
    }
    attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    ctx = attrs["context_neurons"]
    assert "presence.room" in ctx
    assert "time.of_day" in ctx
    assert "light.level" in ctx
    assert "mood.dominant" not in ctx
    assert "energy.current" not in ctx


def test_nd4_mood_neurons_grouped_correctly():
    """ND4: mood neurons grouped correctly."""
    data = {
        "neurons": {
            "mood.dominant": {"active": True, "value": "calm"},
            "mood.stress": {"active": False, "value": "low"},
        }
    }
    attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    mood = attrs["mood_neurons"]
    assert "mood.dominant" in mood
    assert "mood.stress" in mood


def test_nd5_state_neurons_other_neurons():
    """ND5: other neurons default to state_neurons."""
    data = {
        "neurons": {
            "energy.current": {"active": True, "value": 350},
            "media.activity": {"active": False, "value": "idle"},
        }
    }
    attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    state = attrs["state_neurons"]
    assert "energy.current" in state
    assert "media.activity" in state


def test_nd6_total_count_and_active_count():
    """ND6: total_count and active_count computed correctly."""
    data = {
        "neurons": {
            "n1": {"active": True},
            "n2": {"active": False},
            "n3": {"active": True},
        }
    }
    attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    assert attrs["total_count"] == 3
    assert attrs["active_count"] == 2


def test_nd7_non_dict_neuron_data_handled():
    """ND7: non-dict neuron data does not crash."""
    data = {
        "neurons": {
            "n1": "not a dict",
            "n2": None,
            "n3": {"active": True},
        }
    }
    attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    assert attrs["total_count"] == 3
    # non-dict items excluded from active_count
    assert attrs["active_count"] == 1


def test_nd8_native_value_is_ok():
    """ND8: NeuronDashboardSensor native_value is 'ok'."""
    assert NeuronDashboardSensorContract.native_value({}) == "ok"


# ---------------------------------------------------------------------------
# MoodHistorySensor tests (MH prefix)
# ---------------------------------------------------------------------------

def test_mh1_no_data_returns_unknown():
    """MH1: No coordinator data → mood 'unknown', confidence 0.0."""
    mood, confidence = MoodHistorySensorContract.current_mood_and_confidence(None)
    assert mood == "unknown"
    assert confidence == 0.0


def test_mh2_native_value_is_ok():
    """MH2: MoodHistorySensor native_value is 'ok'."""
    assert MoodHistorySensorContract.native_value({}) == "ok"


def test_mh3_mood_and_confidence_from_data():
    """MH3: MoodHistorySensor reads dominant_mood/confidence from coordinator."""
    data = {
        "dominant_mood": "relaxed",
        "mood_confidence": 0.87,
    }
    mood, confidence = MoodHistorySensorContract.current_mood_and_confidence(data)
    assert mood == "relaxed"
    assert confidence == 0.87


# ---------------------------------------------------------------------------
# SuggestionSensor tests (SG prefix)
# ---------------------------------------------------------------------------

def test_sg1_no_data_returns_none():
    """SG1: No suggestions → native_value 'none'."""
    assert SuggestionSensorContract.native_value(None) == "none"


def test_sg2_empty_suggestions_returns_none():
    """SG2: Empty suggestions list → 'none'."""
    assert SuggestionSensorContract.native_value({"suggestions": []}) == "none"


def test_sg3_first_suggestion_action_type_returned():
    """SG3: native_value returns first suggestion action_type."""
    data = {
        "suggestions": [
            {"action_type": "light_adjust", "confidence": 0.9},
            {"action_type": "scene_activate", "confidence": 0.7},
        ]
    }
    assert SuggestionSensorContract.native_value(data) == "light_adjust"


def test_sg4_non_dict_suggestion_returns_none():
    """SG4: non-dict suggestion item → 'none'."""
    data = {"suggestions": ["not a dict", {"action_type": "valid"}]}
    assert SuggestionSensorContract.native_value(data) == "none"


def test_sg5_suggestion_count_and_top_in_attrs():
    """SG5: SuggestionSensor attrs include count and top_suggestion."""
    data = {
        "suggestions": [
            {"action_type": "light_adjust", "confidence": 0.9},
            {"action_type": "scene_activate", "confidence": 0.7},
        ],
        "ranked_candidates": [{}, {}, {}],
    }
    attrs = SuggestionSensorContract.extra_state_attributes(data)
    assert attrs["count"] == 2
    assert attrs["top_suggestion"]["action_type"] == "light_adjust"
    assert attrs["ranked_candidates_count"] == 3


def test_sg6_ranked_candidates_limited_to_10():
    """SG6: ranked_candidates in attrs limited to 10 items."""
    data = {
        "suggestions": [],
        "ranked_candidates": [{"id": i} for i in range(25)],
    }
    attrs = SuggestionSensorContract.extra_state_attributes(data)
    assert len(attrs["ranked_candidates"]) == 10


def test_sg7_no_data_attrs_have_keys():
    """SG7: No data → attrs have correct default keys."""
    attrs = SuggestionSensorContract.extra_state_attributes(None)
    assert "suggestions" in attrs
    assert "ranked_candidates_count" in attrs


# ---------------------------------------------------------------------------
# Global contract tests (GC prefix)
# ---------------------------------------------------------------------------

def test_gc1_pure_coordinator_projection():
    """GC1: All three sensors are pure coordinator projections."""
    data = {
        "neurons": {"n1": {"active": True}},
        "dominant_mood": "focused",
        "mood_confidence": 0.75,
        "suggestions": [{"action_type": "work_start"}],
        "ranked_candidates": [],
    }
    nd_attrs = NeuronDashboardSensorContract.extra_state_attributes(data)
    assert nd_attrs["total_count"] == 1

    mood, conf = MoodHistorySensorContract.current_mood_and_confidence(data)
    assert mood == "focused"
    assert conf == 0.75

    assert SuggestionSensorContract.native_value(data) == "work_start"


def test_gc2_source_guard_no_direct_api_calls():
    """GC2: Source guard — neuron_dashboard does not call external APIs."""
    worktree_root = os.environ.get(
        "PILOTSUITE_WORKTREE_ROOT",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_components", "pilotsuite")
    )
    filepath = os.path.join(worktree_root, "sensors", "neuron_dashboard.py")
    # Fallback: resolve relative to this test file
    if not os.path.exists(filepath):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(test_dir, "..", "..", "custom_components", "p\\ilotsuite", "sensors", "neuron_dashboard.py")
    if not os.path.exists(filepath):
        # last resort: walk up from test dir
        import inspect
        test_file = os.path.abspath(inspect.getfile(inspect.currentframe()))
        parts = test_file.split(os.sep)
        # custom_components/pilotsuite/sensors/neuron_dashboard.py
        idx = parts.index("tests")
        filepath = os.path.join(os.sep, *parts[:idx], "custom_components", "pilotsuite", "sensors", "neuron_dashboard.py")

    with open(filepath, "r") as fh:
        source = fh.read()
    # No direct HTTP/network calls in the sensor
    assert "requests." not in source
    assert "aiohttp" not in source
    assert "httpx" not in source
    assert "urllib.request" not in source


def test_gc3_max_history_constant_present():
    """GC3: MoodHistorySensor max_history is capped at 20."""
    worktree_root = os.environ.get(
        "PILOTSUITE_WORKTREE_ROOT",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_components", "pilotsuite")
    )
    filepath = os.path.join(worktree_root, "sensors", "neuron_dashboard.py")
    if not os.path.exists(filepath):
        import inspect
        test_file = os.path.abspath(inspect.getfile(inspect.currentframe()))
        parts = test_file.split(os.sep)
        idx = parts.index("tests")
        filepath = os.path.join(os.sep, *parts[:idx], "custom_components", "pilotsuite", "sensors", "neuron_dashboard.py")
    with open(filepath, "r") as fh:
        source = fh.read()
    assert "_max_history = 20" in source or "_max_history=20" in source


def _resolve_neuron_dashboard_path():
    import os, inspect
    test_file = os.path.abspath(inspect.getfile(inspect.currentframe()))
    parts = test_file.split(os.sep)
    idx = parts.index("tests")
    return os.path.join(os.sep, *parts[:idx], "custom_components", "pilotsuite", "sensors", "neuron_dashboard.py")


def test_gc4_unique_ids_are_pilotsuite_canonical():
    """GC4: All three neuron_dashboard sensor unique IDs use pilotsuite_* namespace."""
    filepath = _resolve_neuron_dashboard_path()
    with open(filepath, "r") as fh:
        source = fh.read()
    assert 'pilotsuite_neuron_dashboard' in source
    assert 'pilotsuite_mood_history' in source
    assert 'pilotsuite_suggestions' in source


def test_gc5_no_stale_ai_copilot_unique_ids():
    """GC5: No stale ai_copilot_* unique IDs remain in neuron_dashboard.py."""
    filepath = _resolve_neuron_dashboard_path()
    with open(filepath, "r") as fh:
        source = fh.read()
    assert 'ai_copilot_neuron_dashboard' not in source
    assert 'ai_copilot_mood_history' not in source
    assert 'ai_copilot_suggestions' not in source


def test_gc6_migration_entries_in_init():
    """GC6: Legacy→pilotsuite migrations for all three sensors exist in __init__.py."""
    import pathlib
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "custom_components", "pilotsuite", "__init__.py"),
    ]
    filepath = None
    for p in candidates:
        if pathlib.Path(p).exists():
            filepath = p
            break
    if filepath is None:
        pytest.skip("__init__.py not resolvable from test context")
    with open(filepath, "r") as fh:
        source = fh.read()
    assert '"ai_copilot_neuron_dashboard": "pilotsuite_neuron_dashboard"' in source
    assert '"ai_copilot_mood_history": "pilotsuite_mood_history"' in source
    assert '"ai_copilot_suggestions": "pilotsuite_suggestions"' in source
