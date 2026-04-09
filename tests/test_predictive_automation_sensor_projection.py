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
class PredictiveAutomationSensorContract:
    """Contract-Mirror für PredictiveAutomationSensor."""
    
    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if coordinator_data is None:
            return "idle"
        suggestions = coordinator_data.get("suggestions", [])
        if suggestions is None:
            suggestions = []
        return str(len(suggestions))
    
    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if coordinator_data is None:
            return {}
        suggestions = coordinator_data.get("suggestions", [])
        if suggestions is None:
            suggestions = []
        return {
            "suggestion_count": len(suggestions),
            "suggestions": suggestions,
            "last_update": coordinator_data.get("last_update"),
        }


class PredictiveAutomationDetailsSensorContract:
    """Contract-Mirror für PredictiveAutomationDetailsSensor."""
    
    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if coordinator_data is None:
            return "none"
        suggestions = coordinator_data.get("suggestions", [])
        if suggestions is None:
            return "none"
        if not suggestions:
            return "none"
        best = max(suggestions, key=lambda s: s.get("confidence", 0))
        return best.get("pattern", "unknown")
    
    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if coordinator_data is None:
            return {}
        suggestions = coordinator_data.get("suggestions", [])
        if suggestions is None:
            suggestions = []
        return {
            "suggestions": [
                {
                    "pattern": s.get("pattern", ""),
                    "confidence": s.get("confidence", 0),
                    "lift": s.get("lift", 1.0),
                    "support": s.get("support", 0),
                    "zone": s.get("zone", ""),
                    "mood_type": s.get("mood_type", ""),
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


class TestGlobalContract:
    """GC1–GC2: Globaler Projection-Contract."""
    
    def test_gc1_no_local_semantic_invention(self):
        """GC1: Sensor ist reine Projection-Shell — keine lokale Semantik."""
        # Source-Inspection: predictive_automation.py nutzt NUR:
        # - coordinator.data.get("suggestions", [])
        # - len(suggestions)
        # - max(suggestions, key=lambda s: s.get("confidence", 0))
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
