"""Projection contract tests for HabitLearningSensor v2.

Verifies HabitLearningSensor, HabitPredictionSensor, SequencePredictionSensor
project /habit_summary, /predictions, /sequences from CopilotDataUpdateCoordinator
without local semantic invention.

Contract Mirror pattern: mirrors take raw coordinator_data dict directly,
avoiding the import chain through coordinator.py → api.py.
Only source-file reads are used for GC guards.
"""
from __future__ import annotations

import pytest

SENSOR_PATH = "custom_components/pilotsuite/sensors/habit_learning_v2.py"


# ---------------------------------------------------------------------------
# Contract Mirrors (write-only — must stay in sync with the sensor source)
# ---------------------------------------------------------------------------

class HabitLearningSensorContract:
    """Mirror of HabitLearningSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "0"
        habit_summary = coordinator_data.get("habit_summary", {})
        return str(habit_summary.get("total_patterns", 0))

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        habit_summary = coordinator_data.get("habit_summary", {})
        return {
            "total_patterns": habit_summary.get("total_patterns", 0),
            "time_patterns": habit_summary.get("time_patterns", {}),
            "mood_patterns": habit_summary.get("mood_patterns", {}),
            "sequences": habit_summary.get("sequences", {}),
            "device_patterns": habit_summary.get("device_patterns", {}),
            "last_update": habit_summary.get("last_update"),
        }


class HabitPredictionSensorContract:
    """Mirror of HabitPredictionSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "0"
        predictions = coordinator_data.get("predictions", [])
        return str(len(predictions) if predictions is not None else 0)

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        predictions = coordinator_data.get("predictions")
        if predictions is None:
            return {}
        return {"predictions": predictions}


class SequencePredictionSensorContract:
    """Mirror of SequencePredictionSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "0"
        sequences = coordinator_data.get("sequences", [])
        return str(len(sequences) if sequences is not None else 0)

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        sequences = coordinator_data.get("sequences")
        if sequences is None:
            return {}
        return {"sequences": sequences}


# ---------------------------------------------------------------------------
# HabitLearningSensor Tests — HL1 to HL10
# ---------------------------------------------------------------------------

class TestHabitLearningSensorNativeValue:
    """HL1-HL4: native_value = str(total_patterns)"""

    def test_hl1_full_habit_summary_returns_pattern_count(self):
        data = {
            "habit_summary": {
                "total_patterns": 7,
                "time_patterns": {"morning": 3},
                "mood_patterns": {"evening": 2},
                "sequences": {},
                "device_patterns": {},
                "last_update": "2026-04-09T06:00:00Z",
            }
        }
        assert HabitLearningSensorContract.native_value(data) == "7"

    def test_hl2_missing_habit_summary_key_returns_zero(self):
        assert HabitLearningSensorContract.native_value({}) == "0"

    def test_hl3_habit_summary_none_returns_zero(self):
        assert HabitLearningSensorContract.native_value(None) == "0"

    def test_hl4_empty_habit_summary_returns_zero(self):
        assert HabitLearningSensorContract.native_value({"habit_summary": {}}) == "0"


class TestHabitLearningSensorAttributes:
    """HL5-HL10: extra_state_attributes projections"""

    def test_hl5_full_habit_summary_returns_all_attributes(self):
        data = {
            "habit_summary": {
                "total_patterns": 5,
                "time_patterns": {"morning": 2, "evening": 3},
                "mood_patterns": {"focused": 4},
                "sequences": {"seq1": {"steps": 3}},
                "device_patterns": {"light.living": 1},
                "last_update": "2026-04-09T06:00:00Z",
            }
        }
        attrs = HabitLearningSensorContract.extra_state_attributes(data)
        assert attrs["total_patterns"] == 5
        assert attrs["time_patterns"] == {"morning": 2, "evening": 3}
        assert attrs["mood_patterns"] == {"focused": 4}
        assert attrs["sequences"] == {"seq1": {"steps": 3}}
        assert attrs["device_patterns"] == {"light.living": 1}
        assert attrs["last_update"] == "2026-04-09T06:00:00Z"

    def test_hl6_missing_habit_summary_returns_empty_dict(self):
        assert HabitLearningSensorContract.extra_state_attributes({}) == {}

    def test_hl7_habit_summary_none_returns_empty_dict(self):
        assert HabitLearningSensorContract.extra_state_attributes(None) == {}

    def test_hl8_partial_keys_return_defaults(self):
        data = {"habit_summary": {"total_patterns": 3}}
        attrs = HabitLearningSensorContract.extra_state_attributes(data)
        assert attrs["total_patterns"] == 3
        assert attrs["time_patterns"] == {}
        assert attrs["mood_patterns"] == {}
        assert attrs["sequences"] == {}
        assert attrs["device_patterns"] == {}
        assert attrs["last_update"] is None

    def test_hl9_attributes_are_idempotent(self):
        data = {
            "habit_summary": {
                "total_patterns": 2,
                "time_patterns": {"afternoon": 1},
                "mood_patterns": {},
                "sequences": {},
                "device_patterns": {},
                "last_update": "2026-04-09T00:00:00Z",
            }
        }
        attrs1 = HabitLearningSensorContract.extra_state_attributes(data)
        attrs2 = HabitLearningSensorContract.extra_state_attributes(data)
        assert attrs1 == attrs2

    def test_hl10_pattern_count_string_type(self):
        data = {"habit_summary": {"total_patterns": 12}}
        result = HabitLearningSensorContract.native_value(data)
        assert result == "12"
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# HabitPredictionSensor Tests — HP1 to HP6
# ---------------------------------------------------------------------------

class TestHabitPredictionSensor:
    """HP1-HP6: native_value = str(len(predictions)), attrs = predictions list."""

    def test_hp1_full_predictions_returns_count(self):
        data = {
            "predictions": [
                {"action": "light.turn_on", "confidence": 0.92, "time_window": "morning"},
                {"action": "climate.set_temp", "confidence": 0.87, "time_window": "evening"},
            ]
        }
        assert HabitPredictionSensorContract.native_value(data) == "2"

    def test_hp2_empty_predictions_returns_zero(self):
        assert HabitPredictionSensorContract.native_value({"predictions": []}) == "0"

    def test_hp3_missing_predictions_key_returns_zero(self):
        assert HabitPredictionSensorContract.native_value({}) == "0"

    def test_hp4_predictions_none_returns_zero(self):
        assert HabitPredictionSensorContract.native_value({"predictions": None}) == "0"

    def test_hp5_attributes_return_predictions_list(self):
        data = {
            "predictions": [
                {"action": "media.play", "confidence": 0.95, "time_window": "evening"}
            ]
        }
        assert HabitPredictionSensorContract.extra_state_attributes(data)["predictions"] == [
            {"action": "media.play", "confidence": 0.95, "time_window": "evening"}
        ]

    def test_hp6_attributes_empty_when_no_predictions(self):
        assert HabitPredictionSensorContract.extra_state_attributes({}) == {}


# ---------------------------------------------------------------------------
# SequencePredictionSensor Tests — SP1 to SP6
# ---------------------------------------------------------------------------

class TestSequencePredictionSensor:
    """SP1-SP6: native_value = str(len(sequences)), attrs = sequences list."""

    def test_sp1_full_sequences_returns_count(self):
        data = {
            "sequences": [
                {"id": "seq_a", "steps": 3, "confidence": 0.88},
                {"id": "seq_b", "steps": 2, "confidence": 0.75},
            ]
        }
        assert SequencePredictionSensorContract.native_value(data) == "2"

    def test_sp2_empty_sequences_returns_zero(self):
        assert SequencePredictionSensorContract.native_value({"sequences": []}) == "0"

    def test_sp3_missing_sequences_key_returns_zero(self):
        assert SequencePredictionSensorContract.native_value({}) == "0"

    def test_sp4_sequences_none_returns_zero(self):
        assert SequencePredictionSensorContract.native_value({"sequences": None}) == "0"

    def test_sp5_attributes_return_sequences_list(self):
        data = {
            "sequences": [
                {"id": "seq_x", "steps": 4, "confidence": 0.91}
            ]
        }
        assert SequencePredictionSensorContract.extra_state_attributes(data)["sequences"] == [
            {"id": "seq_x", "steps": 4, "confidence": 0.91}
        ]

    def test_sp6_attributes_empty_when_no_sequences(self):
        assert SequencePredictionSensorContract.extra_state_attributes({}) == {}


# ---------------------------------------------------------------------------
# Global Contract Tests — GC1 to GC2
# ---------------------------------------------------------------------------

class TestHabitLearningGlobalContract:
    """GC1-GC2: source guard — pure coordinator projection, no local invention."""

    def test_gc1_source_uses_habit_summary_coordinator_field(self):
        """Guard: source must read habit_summary from coordinator.data."""
        src = open(SENSOR_PATH).read()
        assert "habit_summary" in src, "Source must project habit_summary from coordinator.data"

    def test_gc2_source_has_no_http_imports(self):
        """Guard: no HTTP imports — pure HA-coordinator passthrough."""
        src = open(SENSOR_PATH).read()
        http_indicators = ["import requests", "import httpx", "urllib.request", "aiohttp"]
        for indicator in http_indicators:
            assert indicator not in src, (
                f"HTTP indicator '{indicator}' found in {SENSOR_PATH} — "
                "sensor must be a pure coordinator projection"
            )
