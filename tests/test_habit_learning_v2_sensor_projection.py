"""Projection contract tests for HabitLearningSensor v2.

Verifies HabitLearningSensor, HabitPredictionSensor, SequencePredictionSensor
project /habit_summary, /predictions, /sequences from CopilotDataUpdateCoordinator
without local semantic invention.

Contract Mirror pattern: mirrors take raw coordinator_data dict directly,
avoiding the import chain through coordinator.py → api.py.
Only source-file reads are used for GC guards.

HA-309 — 2026-04-10
"""
from __future__ import annotations

import pytest

SENSOR_PATH = "custom_components/pilotsuite/sensors/habit_learning_v2.py"


# ---------------------------------------------------------------------------
# Contract Mirrors (write-only — must stay in sync with the sensor source)
# ---------------------------------------------------------------------------

def _as_mapping(value):
    """Return dict-like payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _is_list(value):
    """Return True only for list payloads."""
    return isinstance(value, list)


class HabitLearningSensorContract:
    """Mirror of HabitLearningSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "0"
        habit_summary = _as_mapping(coordinator_data.get("habit_summary"))
        return str(habit_summary.get("total_patterns", 0))

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        habit_summary = _as_mapping(coordinator_data.get("habit_summary"))
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
            return "none"
        predictions = coordinator_data.get("predictions")
        if not _is_list(predictions):
            return "none"
        if not predictions:
            return "none"
        best = max(predictions, key=lambda p: _as_mapping(p).get("confidence", 0))
        return _as_mapping(best).get("pattern", "unknown")

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        predictions = coordinator_data.get("predictions")
        if not _is_list(predictions):
            return {}
        return {
            "predictions": [
                {
                    "pattern": _as_mapping(p).get("pattern", ""),
                    "confidence": _as_mapping(p).get("confidence", 0),
                    "predicted": _as_mapping(p).get("predicted", False),
                    "details": _as_mapping(p).get("details", {}),
                }
                for p in predictions
            ],
            "count": len(predictions),
        }


class SequencePredictionSensorContract:
    """Mirror of SequencePredictionSensor projection logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "none"
        sequences = coordinator_data.get("sequences")
        if not _is_list(sequences):
            return "none"
        if not sequences:
            return "none"
        best = max(sequences, key=lambda s: _as_mapping(s).get("confidence", 0))
        return " -> ".join(_as_mapping(best).get("sequence", []))

    @staticmethod
    def extra_state_attributes(coordinator_data):
        if not coordinator_data:
            return {}
        sequences = coordinator_data.get("sequences")
        if not _is_list(sequences):
            return {}
        return {
            "sequences": [
                {
                    "sequence": " -> ".join(_as_mapping(s).get("sequence", [])),
                    "confidence": _as_mapping(s).get("confidence", 0),
                    "occurrences": _as_mapping(s).get("occurrences", 0),
                    "predicted": _as_mapping(s).get("predicted", False),
                }
                for s in sequences
            ],
            "count": len(sequences),
        }


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
# HabitLearningSensor Malformed Payload Tests — HLm1 to HLm3
# ---------------------------------------------------------------------------

class TestHabitLearningSensorMalformed:
    """HLm1-HLm3: malformed habit_summary payloads must not crash."""

    def test_hlm1_habit_summary_string_returns_zero(self):
        # String is not dict-like — guard must return safe empty mapping
        assert HabitLearningSensorContract.native_value({"habit_summary": "invalid"}) == "0"

    def test_hlm2_habit_summary_list_returns_zero(self):
        # List is not dict-like — guard must return safe empty mapping
        assert HabitLearningSensorContract.native_value({"habit_summary": [1, 2, 3]}) == "0"

    def test_hlm3_habit_summary_none_returns_zero(self):
        # Explicit None must not crash
        assert HabitLearningSensorContract.native_value({"habit_summary": None}) == "0"


# ---------------------------------------------------------------------------
# HabitPredictionSensor Tests — HP1 to HP6
# ---------------------------------------------------------------------------

class TestHabitPredictionSensor:
    """HP1-HP6: native_value = pattern, attrs = predictions list."""

    def test_hp1_full_predictions_returns_pattern(self):
        data = {
            "predictions": [
                {"pattern": "morning_routine", "confidence": 0.92, "time_window": "morning"},
                {"pattern": "evening_wind_down", "confidence": 0.87, "time_window": "evening"},
            ]
        }
        # highest confidence is 0.92 → pattern "morning_routine"
        assert HabitPredictionSensorContract.native_value(data) == "morning_routine"

    def test_hp2_empty_predictions_returns_none(self):
        assert HabitPredictionSensorContract.native_value({"predictions": []}) == "none"

    def test_hp3_missing_predictions_key_returns_none(self):
        assert HabitPredictionSensorContract.native_value({}) == "none"

    def test_hp4_predictions_none_returns_none(self):
        assert HabitPredictionSensorContract.native_value({"predictions": None}) == "none"

    def test_hp5_attributes_return_predictions_list(self):
        data = {
            "predictions": [
                {"pattern": "media.play", "confidence": 0.95, "time_window": "evening"}
            ]
        }
        assert HabitPredictionSensorContract.extra_state_attributes(data)["predictions"] == [
            {"pattern": "media.play", "confidence": 0.95, "predicted": False, "details": {}}
        ]

    def test_hp6_attributes_empty_when_no_predictions(self):
        assert HabitPredictionSensorContract.extra_state_attributes({}) == {}


# ---------------------------------------------------------------------------
# HabitPredictionSensor Malformed Payload Tests — HPm1 to HPm4
# ---------------------------------------------------------------------------

class TestHabitPredictionSensorMalformed:
    """HPm1-HPm4: malformed predictions payloads must not crash."""

    def test_hpm1_predictions_string_returns_none(self):
        # string is not a list — must return "none" not crash
        assert HabitPredictionSensorContract.native_value({"predictions": "invalid"}) == "none"

    def test_hpm2_predictions_dict_returns_none(self):
        # dict is not a list — must return "none" not crash
        assert HabitPredictionSensorContract.native_value({"predictions": {"key": "value"}}) == "none"

    def test_hpm3_predictions_int_returns_none(self):
        # int is not a list — must return "none" not crash
        assert HabitPredictionSensorContract.native_value({"predictions": 42}) == "none"

    def test_hpm4_prediction_item_not_dict_falls_back(self):
        # predictions list contains a non-dict item — must not crash via .get()
        data = {"predictions": ["not_a_dict", {"pattern": "ok", "confidence": 0.8}]}
        # first item becomes {} via _as_mapping, second is valid
        # max key: first -> 0, second -> 0.8 → best is second
        assert HabitPredictionSensorContract.native_value(data) == "ok"


# ---------------------------------------------------------------------------
# SequencePredictionSensor Tests — SP1 to SP6
# ---------------------------------------------------------------------------

class TestSequencePredictionSensor:
    """SP1-SP6: native_value = joined sequence, attrs = sequences list."""

    def test_sp1_full_sequences_returns_joined(self):
        data = {
            "sequences": [
                {"sequence": ["light.on", "coffee.brew"], "confidence": 0.88, "occurrences": 5},
                {"sequence": ["tv.watch"], "confidence": 0.75, "occurrences": 3},
            ]
        }
        # highest confidence is 0.88 → sequence ["light.on", "coffee.brew"]
        assert SequencePredictionSensorContract.native_value(data) == "light.on -> coffee.brew"

    def test_sp2_empty_sequences_returns_none(self):
        assert SequencePredictionSensorContract.native_value({"sequences": []}) == "none"

    def test_sp3_missing_sequences_key_returns_none(self):
        assert SequencePredictionSensorContract.native_value({}) == "none"

    def test_sp4_sequences_none_returns_none(self):
        assert SequencePredictionSensorContract.native_value({"sequences": None}) == "none"

    def test_sp5_attributes_return_sequences_list(self):
        data = {
            "sequences": [
                {"sequence": ["light.off"], "confidence": 0.91, "occurrences": 2, "predicted": True}
            ]
        }
        assert SequencePredictionSensorContract.extra_state_attributes(data)["sequences"] == [
            {"sequence": "light.off", "confidence": 0.91, "occurrences": 2, "predicted": True}
        ]

    def test_sp6_attributes_empty_when_no_sequences(self):
        assert SequencePredictionSensorContract.extra_state_attributes({}) == {}


# ---------------------------------------------------------------------------
# SequencePredictionSensor Malformed Payload Tests — SPm1 to SPm4
# ---------------------------------------------------------------------------

class TestSequencePredictionSensorMalformed:
    """SPm1-SPm4: malformed sequences payloads must not crash."""

    def test_spm1_sequences_string_returns_none(self):
        # string is not a list — must return "none" not crash
        assert SequencePredictionSensorContract.native_value({"sequences": "invalid"}) == "none"

    def test_spm2_sequences_dict_returns_none(self):
        # dict is not a list — must return "none" not crash
        assert SequencePredictionSensorContract.native_value({"sequences": {"key": "value"}}) == "none"

    def test_spm3_sequences_int_returns_none(self):
        # int is not a list — must return "none" not crash
        assert SequencePredictionSensorContract.native_value({"sequences": 99}) == "none"

    def test_spm4_sequence_item_not_dict_falls_back(self):
        # sequences list contains a non-dict item — must not crash via .get()
        data = {"sequences": ["not_a_dict", {"sequence": ["ok"], "confidence": 0.7}]}
        # first item becomes {} via _as_mapping, second is valid
        # max key: first -> 0, second -> 0.7 → best is second
        assert SequencePredictionSensorContract.native_value(data) == "ok"


# ---------------------------------------------------------------------------
# Global Contract Tests — GC1 to GC4
# ---------------------------------------------------------------------------

class TestHabitLearningGlobalContract:
    """GC1-GC4: source guard — pure coordinator projection, no local invention."""

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

    def test_gc3_source_has_list_guard(self):
        """Guard: source must use _is_list guard to prevent non-list crash."""
        src = open(SENSOR_PATH).read()
        assert "_is_list" in src, "Source must use _is_list guard for predictions/sequences payloads"

    def test_gc4_source_has_mapping_guard(self):
        """Guard: source must use _as_mapping guard for habit_summary and sub-payloads."""
        src = open(SENSOR_PATH).read()
        assert "_as_mapping" in src, "Source must use _as_mapping guard for dict-like payloads"
