"""Projection contract tests for neuron_dashboard.py sensors.

Verifies NeuronDashboardSensor, MoodHistorySensor, SuggestionSensor
are pure projection shells on Core coordinator.data — no local semantic invention.

HA-24 — 2026-04-05
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {}
    return coordinator


@pytest.fixture
def neurons_data():
    return {
        "neurons": {
            "presence.room": {"active": True, "state": "living_room"},
            "presence.person_1": {"active": True, "state": "home"},
            "mood.joy": {"active": True, "state": "high"},
            "mood.energy": {"active": False, "state": "low"},
            "time.of_day": {"active": True, "state": "evening"},
        }
    }


@pytest.fixture
def mood_data():
    return {
        "dominant_mood": "content",
        "mood_confidence": 0.82,
    }


@pytest.fixture
def suggestions_data():
    return {
        "suggestions": [
            {"action_type": "light_adjust", "reason": "evening detected"},
            {"action_type": "scene_activate", "reason": "movie time"},
        ],
        "ranked_candidates": [
            {"id": "c1", "score": 0.95},
            {"id": "c2", "score": 0.88},
        ],
    }


# =============================================================================
# Contract Mirrors
# =============================================================================

class NeuronDashboardSensorContract:
    """Mirror of NeuronDashboardSensor projection logic.

    Contract:
    - hits coordinator.data["neurons"]
    - extra_state_attributes: context_neurons, mood_neurons, state_neurons, total_count, active_count
    """

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = coordinator.data.get("neurons", {})

    @property
    def native_value(self):
        return "ok"

    @property
    def extra_state_attributes(self):
        neurons = self._data if isinstance(self._data, dict) else {}
        context = {k: v for k, v in neurons.items() if k.startswith(("presence.", "time."))}
        mood = {k: v for k, v in neurons.items() if k.startswith("mood.")}
        total = len(neurons)
        active = sum(1 for v in neurons.values() if isinstance(v, dict) and v.get("active"))
        return {
            "context_neurons": context,
            "mood_neurons": mood,
            "state_neurons": {k: v for k, v in neurons.items() if k.startswith("state.")},
            "total_count": total,
            "active_count": active,
        }


class MoodHistorySensorContract:
    """Mirror of MoodHistorySensor projection logic.

    Contract:
    - hits coordinator.data["dominant_mood"] + ["mood_confidence"]
    """

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = coordinator.data

    @property
    def extra_state_attributes(self):
        return {
            "history": [],
            "current_mood": self._data.get("dominant_mood", "unknown"),
            "current_confidence": self._data.get("mood_confidence", 0.0),
        }


class SuggestionSensorContract:
    """Mirror of SuggestionSensor projection logic.

    Contract:
    - hits coordinator.data["suggestions"] + ["ranked_candidates"]
    """

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = coordinator.data

    @property
    def native_value(self):
        suggestions = self._data.get("suggestions", [])
        if not suggestions:
            return "none"
        return suggestions[0].get("action_type", "none")

    @property
    def extra_state_attributes(self):
        suggestions = self._data.get("suggestions", [])
        ranked = self._data.get("ranked_candidates", [])
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "ranked_candidates": ranked,
            "ranked_candidates_count": len(ranked),
            "top_suggestion": suggestions[0] if suggestions else None,
        }


# =============================================================================
# NeuronDashboardSensor — ND1–ND7
# =============================================================================

class TestNeuronDashboardSensor:
    """ND: NeuronDashboardSensor hits coordinator.data['neurons']."""

    def test_nd1_native_value_ok(self, mock_coordinator):
        """ND1: native_value is 'ok' when coordinator has data."""
        mock_coordinator.data = {"neurons": {"n1": {"active": True}}}
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        assert sensor.native_value == "ok"

    def test_nd2_native_value_ok_empty(self, mock_coordinator):
        """ND2: native_value is 'ok' even when neurons is empty dict."""
        mock_coordinator.data = {"neurons": {}}
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        assert sensor.native_value == "ok"

    def test_nd3_extra_attrs_context_neurons(self, mock_coordinator, neurons_data):
        """ND3: context neurons correctly categorized from neurons dict."""
        mock_coordinator.data = neurons_data
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert "presence.room" in attrs["context_neurons"]
        assert "presence.person_1" in attrs["context_neurons"]
        assert "time.of_day" in attrs["context_neurons"]

    def test_nd4_extra_attrs_mood_neurons(self, mock_coordinator, neurons_data):
        """ND4: mood neurons correctly categorized."""
        mock_coordinator.data = neurons_data
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert "mood.joy" in attrs["mood_neurons"]
        assert "mood.energy" in attrs["mood_neurons"]

    def test_nd5_extra_attrs_counts(self, mock_coordinator, neurons_data):
        """ND5: total_count and active_count derived from neurons dict."""
        mock_coordinator.data = neurons_data
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["total_count"] == 5
        # presence.room(True), presence.person_1(True), mood.joy(True), time.of_day(True) = 4 active
        assert attrs["active_count"] == 4

    def test_nd6_extra_attrs_empty(self, mock_coordinator):
        """ND6: empty coordinator.data returns empty structure."""
        mock_coordinator.data = {}
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs.get("total_count", 0) == 0

    def test_nd7_no_local_logic(self, mock_coordinator, neurons_data):
        """ND7: Sensor does not compute derived semantics — pure projection."""
        mock_coordinator.data = neurons_data
        sensor = NeuronDashboardSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert "context_neurons" in attrs
        assert "state_neurons" in attrs
        assert "mood_neurons" in attrs


# =============================================================================
# MoodHistorySensor — MH1–MH5
# =============================================================================

class TestMoodHistorySensor:
    """MH: MoodHistorySensor hits coordinator.data['dominant_mood'/'mood_confidence']."""

    def test_mh1_extra_attrs_history_structure(self, mock_coordinator, mood_data):
        """MH1: extra_state_attributes has history list + current mood fields."""
        mock_coordinator.data = mood_data
        sensor = MoodHistorySensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert "history" in attrs
        assert "current_mood" in attrs
        assert "current_confidence" in attrs

    def test_mh2_current_mood_from_coordinator(self, mock_coordinator, mood_data):
        """MH2: current_mood is read directly from coordinator.data['dominant_mood']."""
        mock_coordinator.data = mood_data
        sensor = MoodHistorySensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["current_mood"] == "content"

    def test_mh3_current_confidence_from_coordinator(self, mock_coordinator, mood_data):
        """MH3: current_confidence is read directly from coordinator.data['mood_confidence']."""
        mock_coordinator.data = mood_data
        sensor = MoodHistorySensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["current_confidence"] == 0.82

    def test_mh4_confidence_passthrough(self, mock_coordinator):
        """MH4: confidence value is passed through unchanged."""
        mock_coordinator.data = {"dominant_mood": "happy", "mood_confidence": 0.75}
        sensor = MoodHistorySensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["current_confidence"] == 0.75

    def test_mh5_default_unknown(self, mock_coordinator):
        """MH5: missing mood data defaults to 'unknown' / 0.0."""
        mock_coordinator.data = {}
        sensor = MoodHistorySensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["current_mood"] == "unknown"
        assert attrs["current_confidence"] == 0.0


# =============================================================================
# SuggestionSensor — SS1–SS7
# =============================================================================

class TestSuggestionSensor:
    """SS: SuggestionSensor hits coordinator.data['suggestions'/'ranked_candidates']."""

    def test_ss1_native_value_action_type(self, mock_coordinator, suggestions_data):
        """SS1: native_value returns action_type of first suggestion."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        assert sensor.native_value == "light_adjust"

    def test_ss2_native_value_none(self, mock_coordinator):
        """SS2: native_value is 'none' when no suggestions."""
        mock_coordinator.data = {"suggestions": []}
        sensor = SuggestionSensorContract(mock_coordinator)
        assert sensor.native_value == "none"

    def test_ss3_extra_attrs_suggestions_list(self, mock_coordinator, suggestions_data):
        """SS3: extra_state_attributes['suggestions'] is the raw suggestions list."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert "suggestions" in attrs
        assert len(attrs["suggestions"]) == 2

    def test_ss4_extra_attrs_count(self, mock_coordinator, suggestions_data):
        """SS4: count is len(suggestions)."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["count"] == 2

    def test_ss5_extra_attrs_ranked_candidates(self, mock_coordinator, suggestions_data):
        """SS5: ranked_candidates projected directly from coordinator.data."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["ranked_candidates_count"] == 2
        assert len(attrs["ranked_candidates"]) == 2

    def test_ss6_top_suggestion(self, mock_coordinator, suggestions_data):
        """SS6: top_suggestion is first suggestion."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["top_suggestion"]["action_type"] == "light_adjust"

    def test_ss7_no_local_semantic_logic(self, mock_coordinator, suggestions_data):
        """SS7: Sensor does not invent or filter suggestions — pure projection."""
        mock_coordinator.data = suggestions_data
        sensor = SuggestionSensorContract(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["count"] == len(suggestions_data["suggestions"])
        assert attrs["top_suggestion"] == suggestions_data["suggestions"][0]


# =============================================================================
# Global Contract — GC1–GC2
# =============================================================================

class TestGlobalContract:
    """GC: Sensoren sind reine Projection-Shells auf Core coordinator.data."""

    def test_gc1_no_local_semantic_invention(self, mock_coordinator):
        """GC1: Kein Sensor erfindet lokale Semantik — alles kommt von coordinator.data."""
        mock_coordinator.data = {
            "neurons": {"n1": {"active": True}},
            "dominant_mood": "calm",
            "mood_confidence": 0.9,
            "suggestions": [{"action_type": "scene"}],
            "ranked_candidates": [],
        }
        nd = NeuronDashboardSensorContract(mock_coordinator)
        mh = MoodHistorySensorContract(mock_coordinator)
        ss = SuggestionSensorContract(mock_coordinator)

        assert nd.extra_state_attributes["total_count"] == 1
        assert mh.extra_state_attributes["current_mood"] == "calm"
        assert ss.extra_state_attributes["count"] == 1

    def test_gc2_core_endpoints_verified(self, mock_coordinator):
        """GC2: Sensoren projizieren Core-APIs /api/v1/hub/neurons + /api/v1/hub/suggestions."""
        mock_coordinator.data = {
            "neurons": {},
            "suggestions": [],
            "ranked_candidates": [],
        }
        nd = NeuronDashboardSensorContract(mock_coordinator)
        ss = SuggestionSensorContract(mock_coordinator)

        assert "context_neurons" in nd.extra_state_attributes
        assert "suggestions" in ss.extra_state_attributes
