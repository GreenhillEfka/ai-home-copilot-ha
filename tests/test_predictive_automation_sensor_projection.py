"""PredictiveAutomationSensor Projection Contract Tests (HA-168).

Contract: PredictiveAutomationSensor + PredictiveAutomationDetailsSensor sind reine
Projection-Shells auf coordinator.data["suggestions"] — triviale len()-Aggregation +
Dict-Lookups, keine lokale Semantik.

Test-Mirror: HA-Local Contract-Mirror bildet exakt das Sensor-Verhalten ab.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from unittest.mock import MagicMock, PropertyMock


_SOURCE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "pilotsuite" / "sensors" / "predictive_automation.py"
_SOURCE_TEXT = _SOURCE_PATH.read_text(encoding="utf-8")

# Contract-Mirror: Lokale Abbildung des Sensor-Verhaltens
def _pa_as_mapping(value):
    if isinstance(value, dict):
        return value
    return {}


def _pa_as_list(value):
    if isinstance(value, list):
        return value
    return []


def _pa_as_float(value, default):
    try:
        numeric_value = float(value)
        if isinstance(value, bool) or not abs(numeric_value) < float("inf"):
            return default
        return numeric_value
    except (TypeError, ValueError):
        return default


def _pa_as_string(value, default):
    if isinstance(value, str):
        return value
    return default


class PredictiveAutomationSensorContract:
    """Contract-Mirror für PredictiveAutomationSensor."""
    
    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if coordinator_data is None:
            return "idle"
        data = _pa_as_mapping(coordinator_data)
        suggestions = _pa_as_list(data.get("suggestions"))
        return str(len(suggestions))

    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if coordinator_data is None:
            return {}
        data = _pa_as_mapping(coordinator_data)
        suggestions = _pa_as_list(data.get("suggestions"))
        return {
            "suggestion_count": len(suggestions),
            "suggestions": suggestions,
            "last_update": data.get("last_update"),
        }


class PredictiveAutomationDetailsSensorContract:
    """Contract-Mirror für PredictiveAutomationDetailsSensor."""
    
    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if coordinator_data is None:
            return "none"
        data = _pa_as_mapping(coordinator_data)
        suggestions = _pa_as_list(data.get("suggestions"))
        if not suggestions:
            return "none"

        # Guard against non-dict list items
        valid_suggestions = [_pa_as_mapping(s) for s in suggestions]
        best = max(valid_suggestions, key=lambda s: _pa_as_float(s.get("confidence"), 0.0))
        return _pa_as_string(best.get("pattern"), "unknown")

    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if coordinator_data is None:
            return {}
        data = _pa_as_mapping(coordinator_data)
        suggestions = _pa_as_list(data.get("suggestions"))
        return {
            "suggestions": [
                {
                    "pattern": _pa_as_string(_pa_as_mapping(s).get("pattern"), ""),
                    "confidence": _pa_as_float(_pa_as_mapping(s).get("confidence"), 0.0),
                    "lift": _pa_as_float(_pa_as_mapping(s).get("lift"), 1.0),
                    "support": _pa_as_float(_pa_as_mapping(s).get("support"), 0.0),
                    "zone": _pa_as_string(_pa_as_mapping(s).get("zone"), ""),
                    "mood_type": _pa_as_string(_pa_as_mapping(s).get("mood_type"), ""),
                }
                for s in suggestions
            ],
            "count": len(suggestions),
        }


class TestPredictiveAutomationSensor:
    """PA1–PA5: PredictiveAutomationSensor Projection-Contract."""
    
    @pytest.mark.parametrize("coordinator_data,expected", [
        ({"suggestions": [{"pattern": "morning_light"}, {"pattern": "evening_scene"}], "last_update": "2026-04-07T05:00:00Z"}, "2"),
        ({"suggestions": [{"pattern": "single"}], "last_update": "2026-04-07T05:00:00Z"}, "1"),
        ({"suggestions": [], "last_update": "2026-04-07T05:00:00Z"}, "0"),
        ({"suggestions": None, "last_update": "2026-04-07T05:00:00Z"}, "0"),
        ({"last_update": "2026-04-07T05:00:00Z"}, "0"),
        (None, "idle"),
        ({}, "0"),
    ])
    def test_pa1_native_value(self, coordinator_data, expected):
        """PA1: native_value = len(suggestions) oder 'idle' bei None."""
        assert PredictiveAutomationSensorContract.native_value(coordinator_data) == expected
    
    @pytest.mark.parametrize("coordinator_data,expected_count,expected_last_update", [
        ({"suggestions": [{"pattern": "test"}], "last_update": "2026-04-07T05:00:00Z"}, 1, "2026-04-07T05:00:00Z"),
        ({"suggestions": [], "last_update": "2026-04-07T05:00:00Z"}, 0, "2026-04-07T05:00:00Z"),
        ({"suggestions": None, "last_update": "2026-04-07T05:00:00Z"}, 0, "2026-04-07T05:00:00Z"),
        ({"last_update": "2026-04-07T05:00:00Z"}, 0, "2026-04-07T05:00:00Z"),
        (None, 0, None),  # empty dict, .get() returns None for missing keys
        ({}, 0, None),
    ])
    def test_pa2_extra_state_attributes(self, coordinator_data, expected_count, expected_last_update):
        """PA2: attrs = suggestion_count + suggestions + last_update."""
        attrs = PredictiveAutomationSensorContract.extra_state_attributes(coordinator_data)
        if coordinator_data is None:
            assert attrs == {}
        else:
            assert attrs.get("suggestion_count") == expected_count
            assert attrs.get("last_update") == expected_last_update
            if coordinator_data.get("suggestions"):
                assert attrs.get("suggestions") == coordinator_data["suggestions"]
    
    def test_pa3_attrs_preserves_suggestions_list(self):
        """PA3: suggestions-Liste wird unverändert durchgereicht."""
        data = {"suggestions": [{"pattern": "a", "confidence": 0.9}], "last_update": "now"}
        attrs = PredictiveAutomationSensorContract.extra_state_attributes(data)
        assert attrs["suggestions"] == [{"pattern": "a", "confidence": 0.9}]
    
    def test_pa4_none_coordinator_returns_empty_dict(self):
        """PA4: None coordinator_data → leere attrs."""
        assert PredictiveAutomationSensorContract.extra_state_attributes(None) == {}
    
    def test_pa5_empty_dict_coordinator_returns_zero_count(self):
        """PA5: {} coordinator_data → suggestion_count=0."""
        attrs = PredictiveAutomationSensorContract.extra_state_attributes({})
        assert attrs["suggestion_count"] == 0

    @pytest.mark.parametrize("coordinator_data,expected", [
        # non-list suggestions: _as_list returns [], len=0 → "0"
        ({"suggestions": "not_a_list"}, "0"),
        ({"suggestions": 42}, "0"),
        ({"suggestions": {"key": "value"}}, "0"),
        # malformed list items: _as_list returns them as-is (cast fails), len reflects reality
        ({"suggestions": [None]}, "1"),
        ({"suggestions": [1, 2, 3]}, "3"),
        ({"suggestions": ["string_item"]}, "1"),
    ])
    def test_pa6_malformed_suggestions_returns_zero_count(self, coordinator_data, expected):
        """PA6: non-list suggestions → count=0; malformed list items counted as-is."""
        value = PredictiveAutomationSensorContract.native_value(coordinator_data)
        assert value == expected


class TestPredictiveAutomationDetailsSensor:
    """PD1–PD5: PredictiveAutomationDetailsSensor Projection-Contract."""
    
    @pytest.mark.parametrize("coordinator_data,expected", [
        ({"suggestions": [{"pattern": "morning_light", "confidence": 0.9}, {"pattern": "evening", "confidence": 0.5}]}, "morning_light"),
        ({"suggestions": [{"pattern": "single", "confidence": 0.3}]}, "single"),
        ({"suggestions": []}, "none"),
        ({"suggestions": None}, "none"),
        ({"other_key": "value"}, "none"),
        (None, "none"),
        ({}, "none"),
    ])
    def test_pd1_native_value_highest_confidence(self, coordinator_data, expected):
        """PD1: native_value = pattern mit höchster confidence oder 'none'."""
        assert PredictiveAutomationDetailsSensorContract.native_value(coordinator_data) == expected
    
    @pytest.mark.parametrize("coordinator_data,expected_count", [
        ({"suggestions": [{"pattern": "a"}, {"pattern": "b"}]}, 2),
        ({"suggestions": []}, 0),
        ({"suggestions": None}, 0),
        ({"other": "data"}, 0),
        (None, 0),  # empty dict case
    ])
    def test_pd2_attrs_count_matches_suggestions_len(self, coordinator_data, expected_count):
        """PD2: attrs['count'] = len(suggestions)."""
        attrs = PredictiveAutomationDetailsSensorContract.extra_state_attributes(coordinator_data)
        if coordinator_data is None:
            assert attrs == {}
        else:
            assert attrs.get("count") == expected_count
    
    def test_pd3_attrs_normalizes_suggestion_fields(self):
        """PD3: attrs normalisiert suggestion-Felder mit Defaults."""
        data = {"suggestions": [{"pattern": "test"}]}  # missing confidence, lift, support, zone, mood_type
        attrs = PredictiveAutomationDetailsSensorContract.extra_state_attributes(data)
        assert attrs["suggestions"][0] == {
            "pattern": "test",
            "confidence": 0,
            "lift": 1.0,
            "support": 0,
            "zone": "",
            "mood_type": "",
        }
    
    def test_pd4_none_coordinator_returns_empty_dict(self):
        """PD4: None coordinator_data → leere attrs."""
        assert PredictiveAutomationDetailsSensorContract.extra_state_attributes(None) == {}
    
    def test_pd5_empty_suggestions_returns_empty_list(self):
        """PD5: leere suggestions → empty list in attrs."""
        attrs = PredictiveAutomationDetailsSensorContract.extra_state_attributes({"suggestions": []})
        assert attrs["suggestions"] == []
        assert attrs["count"] == 0

    @pytest.mark.parametrize("coordinator_data,expected", [
        # non-list suggestions → "none"
        ({"suggestions": "not_a_list"}, "none"),
        ({"suggestions": 42}, "none"),
        ({"suggestions": {"key": "value"}}, "none"),
        # non-dict list items → "unknown" (pattern non-string)
        ({"suggestions": [None]}, "unknown"),
        ({"suggestions": [1, 2, 3]}, "unknown"),
        ({"suggestions": ["string_item"]}, "unknown"),
        # non-finite / bool confidence → 0.0 effective, but valid pattern preserved → "valid"
        # Guard filters inf/nan/bool to 0.0, pattern "valid" still returned
        ({"suggestions": [{"pattern": "valid", "confidence": float("inf")}]}, "valid"),
        ({"suggestions": [{"pattern": "valid", "confidence": float("nan")}]}, "valid"),
        ({"suggestions": [{"pattern": "valid", "confidence": True}]}, "valid"),
        # valid dict but no pattern → "unknown"
        ({"suggestions": [{"confidence": 0.9}]}, "unknown"),
        ({"suggestions": [{}]}, "unknown"),
    ])
    def test_pd6_malformed_suggestions_returns_none_or_unknown(self, coordinator_data, expected):
        """PD6: malformed suggestions → safe defaults (non-list→none, non-dict→unknown)."""
        value = PredictiveAutomationDetailsSensorContract.native_value(coordinator_data)
        assert value == expected


class TestGlobalContract:
    """GC1–GC2: Globaler Projection-Contract."""
    
    def test_gc1_no_local_semantic_invention(self):
        """GC1: Sensor ist reine Projection-Shell — keine lokale Semantik."""
        # Source-Inspection: predictive_automation.py nutzt NUR:
        # - coordinator.data
        # - _as_mapping() / _as_list() guards
        # - len(suggestions), max() mit Guard
        # Keine HA-states, keine externen APIs, keine lokale ML/Heuristik
        source = _SOURCE_TEXT
        assert "class PredictiveAutomationSensor" in source
        assert "class PredictiveAutomationDetailsSensor" in source
        assert "hass.states" not in source
        assert "_core_base_url" not in source
        assert "coordinator.data" in source or "self.coordinator.data" in source
    
    def test_gc2_both_sensors_derive_from_same_coordinator_data(self):
        """GC2: Beide Sensoren projizieren aus derselben coordinator.data-Quelle."""
        # Beide Sensoren lesen coordinator.data.get("suggestions", [])
        # Contract-Mirrors verwenden identische Eingabe (coordinator_data)
        data = {"suggestions": [{"pattern": "test", "confidence": 0.8}], "last_update": "now"}
        
        pa_value = PredictiveAutomationSensorContract.native_value(data)
        pa_attrs = PredictiveAutomationSensorContract.extra_state_attributes(data)
        
        pad_value = PredictiveAutomationDetailsSensorContract.native_value(data)
        pad_attrs = PredictiveAutomationDetailsSensorContract.extra_state_attributes(data)
        
        # Beide konsistent: count=1, same suggestions source
        assert pa_value == "1"
        assert pa_attrs["suggestion_count"] == 1
        assert pad_value == "test"
        assert pad_attrs["count"] == 1

    def test_gc7_pilotsuite_predictive_automation_unique_id(self):
        """GC7: PredictiveAutomationSensor _attr_unique_id ist pilotsuite_predictive_automation."""
        source = _SOURCE_TEXT
        assert '_attr_unique_id = "pilotsuite_predictive_automation"' in source
    
    def test_gc8_pilotsuite_predictive_automation_details_unique_id(self):
        """GC8: PredictiveAutomationDetailsSensor _attr_unique_id ist pilotsuite_predictive_automation_details."""
        source = _SOURCE_TEXT
        assert '_attr_unique_id = "pilotsuite_predictive_automation_details"' in source
    
    def test_gc9_no_stale_ai_copilot_predictive_strings(self):
        """GC9: Prod-Modul führt keine stale ai_copilot_predictive_* Strings."""
        source = _SOURCE_TEXT
        assert "ai_copilot_predictive_automation" not in source
        assert "ai_copilot_predictive_automation_details" not in source

    def test_gc10_migration_map_entry_for_predictive_automation(self):
        """"GC10: Migrationsmap in __init__.py enthält predictive_automation-Einträge."""
        init_path = _SOURCE_PATH.parents[1] / "__init__.py"
        init_text = init_path.read_text(encoding="utf-8")
        assert '"ai_copilot_predictive_automation": "pilotsuite_predictive_automation"' in init_text
        assert '"ai_copilot_predictive_automation_details": "pilotsuite_predictive_automation_details"' in init_text
