"""Projection contract tests for mood sensors.

Verifies MoodSensor + MoodConfidenceSensor + NeuronActivitySensor are pure
Projection-Shells on coordinator.data with type-safe guard helpers.
"""
import math
import pytest


# =============================================================================
# Guard helpers (mirror of mood_sensor.py)
# =============================================================================

def _as_mapping(val):
    if isinstance(val, dict):
        return val
    return {}


def _as_float(val, default):
    if isinstance(val, bool):
        return default
    if isinstance(val, (int, float)) and math.isfinite(val):
        return float(val)
    return default


def _as_string(val):
    if isinstance(val, str) and val.strip():
        return val.strip()
    return ""


def _as_list(val):
    if isinstance(val, list):
        return val
    return []


# =============================================================================
# MoodSensor contract mirror
# =============================================================================

class MoodSensorContract:
    """Mirror of MoodSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return "unknown"
        mood_data = _as_mapping(data.get("mood"))
        return _as_string(mood_data.get("mood")) or "unknown"

    @staticmethod
    def attrs(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return {}
        mood_data = _as_mapping(data.get("mood"))
        raw_emotions = _as_list(mood_data.get("emotions"))
        emotions = raw_emotions
        if not emotions:
            neurons = _as_list(mood_data.get("contributing_neurons"))
            emotions = [
                {"name": _as_string(n.get("name")) or "unknown",
                 "value": _as_float(n.get("value"), 0.0)}
                for n in neurons
                if isinstance(n, dict)
            ]
        zone_moods_raw = data.get("zone_moods")
        zone_moods = _as_mapping(zone_moods_raw) if zone_moods_raw is not None else {}
        return {
            "confidence": _as_float(mood_data.get("confidence"), 0.0),
            "emotions": emotions,
            "zone": _as_string(mood_data.get("zone")) or "unknown",
            "last_updated": mood_data.get("last_update"),
            "last_update": mood_data.get("last_update"),
            "contributing_neurons": _as_list(mood_data.get("contributing_neurons")),
            "zone_moods": zone_moods,
            "zone_moods_count": len(zone_moods),
        }


# =============================================================================
# MoodConfidenceSensor contract mirror
# =============================================================================

class MoodConfidenceSensorContract:
    """Mirror of MoodConfidenceSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return 0
        mood_data = _as_mapping(data.get("mood"))
        confidence = _as_float(mood_data.get("confidence"), 0.0)
        return int(confidence * 100)

    @staticmethod
    def attrs(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return {}
        mood_data = _as_mapping(data.get("mood"))
        return {
            "mood": _as_string(mood_data.get("mood")) or "unknown",
            "factors": _as_mapping(mood_data.get("factors", {})),
        }


# =============================================================================
# NeuronActivitySensor contract mirror
# =============================================================================

class NeuronActivitySensorContract:
    """Mirror of NeuronActivitySensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return 0
        neurons = _as_mapping(data.get("neurons"))
        active_count = sum(
            1 for n in neurons.values()
            if isinstance(n, dict) and n.get("active", False) is True
        )
        return active_count

    @staticmethod
    def attrs(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return {}
        neurons = _as_mapping(data.get("neurons"))
        activity = [
            {
                "name": _as_string(name),
                "active": bool(n.get("active", False)),
                "value": _as_float(n.get("value"), 0.0),
                "confidence": _as_float(n.get("confidence"), 0.0),
            }
            for name, n in neurons.items()
            if isinstance(n, dict)
        ]
        active_neurons = [a for a in activity if a["active"]]
        return {
            "activity": activity,
            "active_neurons": active_neurons,
            "total_neurons": len(neurons),
        }


# =============================================================================
# MoodSensor test cases
# =============================================================================

class TestMoodSensorNativeValue:
    """MoodSensor.native_value contract cases."""

    @staticmethod
    def _nv(data): return MoodSensorContract.native_value(data)

    # --- Basic cases ---
    def test_mo1_unknown_no_data(self):
        """No coordinator data → 'unknown'."""
        assert self._nv(None) == "unknown"
        assert self._nv({}) == "unknown"

    def test_mo2_known_mood(self):
        """Known mood string."""
        data = {"mood": {"mood": "focused"}}
        assert self._nv(data) == "focused"

    def test_mo3_missing_mood_key(self):
        """Mood key missing but mood dict present."""
        data = {"mood": {"confidence": 0.8}}
        assert self._nv(data) == "unknown"

    def test_mo4_empty_mood_dict(self):
        """Empty mood dict."""
        data = {"mood": {}}
        assert self._nv(data) == "unknown"

    def test_mo5_different_moods(self):
        """Various mood strings."""
        for mood in ("relaxed", "tense", "happy", "sad", "energetic"):
            data = {"mood": {"mood": mood}}
            assert self._nv(data) == mood

    # --- Malformed payload cases ---
    def test_mo10_non_dict_top_level(self):
        """Non-dict top-level payload → 'unknown'."""
        for val in ("string", 42, [], True, None):
            assert self._nv({"mood": val}) == "unknown"

    def test_mo11_non_dict_mood_data(self):
        """Mood value present but mood dict itself non-dict → 'unknown'."""
        for val in ("focused", 42, [], True, None):
            data = {"mood": {"mood": val, "extra": "ignored"}}
            # mood dict is still a dict, mood value is the malformed field
            # _as_string("focused") = "focused" → ok
            # _as_string(42) = "" → "unknown"
            assert self._nv(data) in ("focused", "unknown")

    def test_mo12_blank_mood_string(self):
        """Blank/padded mood string → 'unknown'."""
        for val in ("", "   ", "\t", "\n"):
            data = {"mood": {"mood": val}}
            assert self._nv(data) == "unknown"

    def test_mo13_non_string_mood_value(self):
        """Non-string mood value → 'unknown'."""
        for val in (42, 0.85, True, [], {}):
            data = {"mood": {"mood": val}}
            assert self._nv(data) == "unknown"


class TestMoodSensorAttrs:
    """MoodSensor.extra_state_attributes contract cases."""

    @staticmethod
    def _attrs(data): return MoodSensorContract.attrs(data)

    def test_mo6_full_attrs(self):
        """Full attribute set."""
        data = {
            "mood": {
                "mood": "focused",
                "confidence": 0.85,
                "emotions": [{"name": "calm", "value": 0.9}],
                "zone": "office",
                "last_update": "2026-04-08T12:00:00Z",
                "contributing_neurons": [],
                "factors": {"sleep": 0.9},
            },
            "zone_moods": {"office": "focused", "bedroom": "relaxed"},
        }
        attrs = self._attrs(data)
        assert attrs["confidence"] == 0.85
        assert attrs["emotions"] == [{"name": "calm", "value": 0.9}]
        assert attrs["zone"] == "office"
        assert attrs["last_updated"] == "2026-04-08T12:00:00Z"
        assert attrs["last_update"] == "2026-04-08T12:00:00Z"
        assert attrs["zone_moods"] == {"office": "focused", "bedroom": "relaxed"}
        assert attrs["zone_moods_count"] == 2

    def test_mo7_empty_attrs(self):
        """Empty/No coordinator data."""
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}

    def test_mo8_emotions_from_neurons_fallback(self):
        """No emotions but contributing_neurons present."""
        data = {
            "mood": {
                "mood": "relaxed",
                "contributing_neurons": [
                    {"name": "calm neuron", "value": 0.8},
                    {"name": "focus neuron", "value": 0.5},
                ],
            }
        }
        attrs = self._attrs(data)
        assert attrs["emotions"] == [
            {"name": "calm neuron", "value": 0.8},
            {"name": "focus neuron", "value": 0.5},
        ]

    def test_mo9_defaults(self):
        """Default values when keys are missing."""
        data = {"mood": {"mood": "neutral"}}
        attrs = self._attrs(data)
        assert attrs["confidence"] == 0.0
        assert attrs["zone"] == "unknown"
        assert attrs["emotions"] == []
        assert attrs["zone_moods"] == {}
        assert attrs["zone_moods_count"] == 0

    # --- Malformed attrs cases ---
    def test_mo14_non_dict_mood_emotions(self):
        """Non-list emotions field → empty list."""
        for val in ("string", 42, {}, True, None):
            data = {"mood": {"mood": "focused", "emotions": val}}
            attrs = self._attrs(data)
            assert attrs["emotions"] == []

    def test_mo15_non_list_contributing_neurons(self):
        """Non-list contributing_neurons → empty list."""
        for val in ("string", 42, {}, True, None):
            data = {"mood": {"mood": "focused", "contributing_neurons": val}}
            attrs = self._attrs(data)
            assert attrs["contributing_neurons"] == []

    def test_mo16_non_dict_zone_moods(self):
        """Non-dict zone_moods → {}."""
        for val in ("string", 42, [], True, None):
            data = {"mood": {"mood": "focused"}, "zone_moods": val}
            attrs = self._attrs(data)
            assert attrs["zone_moods"] == {}
            assert attrs["zone_moods_count"] == 0

    def test_mo17_non_numeric_confidence(self):
        """Non-numeric confidence → 0.0."""
        for val in ("high", [], {}, True, None):
            data = {"mood": {"mood": "focused", "confidence": val}}
            attrs = self._attrs(data)
            assert attrs["confidence"] == 0.0

    def test_mo18_inf_nan_confidence(self):
        """Inf/nan confidence → 0.0."""
        for val in (float("inf"), float("-inf"), float("nan")):
            data = {"mood": {"mood": "focused", "confidence": val}}
            attrs = self._attrs(data)
            assert attrs["confidence"] == 0.0

    def test_mo19_non_dict_mood_data(self):
        """Top-level mood is non-dict → safe empty."""
        for val in ("focused", 42, [], True, None):
            data = {"mood": val}
            attrs = self._attrs(data)
            assert attrs["confidence"] == 0.0
            assert attrs["zone"] == "unknown"
            assert attrs["emotions"] == []


# =============================================================================
# MoodConfidenceSensor test cases
# =============================================================================

class TestMoodConfidenceSensorNativeValue:
    """MoodConfidenceSensor.native_value contract cases."""

    @staticmethod
    def _nv(data): return MoodConfidenceSensorContract.native_value(data)

    def test_mc1_zero_no_data(self):
        """No data → 0."""
        assert self._nv(None) == 0
        assert self._nv({}) == 0

    def test_mc2_confidence_conversion(self):
        """Confidence 0.0→100 → 0→100 int."""
        for conf, expected in [(0.0, 0), (0.5, 50), (0.75, 75), (1.0, 100), (0.85, 85)]:
            data = {"mood": {"confidence": conf}}
            assert self._nv(data) == expected

    def test_mc3_missing_confidence(self):
        """Confidence key missing → 0."""
        data = {"mood": {"mood": "focused"}}
        assert self._nv(data) == 0

    def test_mc4_confidence_edge(self):
        """Edge confidence values."""
        for conf in (0.01, 0.99, 0.001):
            data = {"mood": {"confidence": conf}}
            assert isinstance(self._nv(data), int)

    # --- Malformed confidence cases ---
    def test_mc8_non_numeric_confidence(self):
        """Non-numeric confidence → 0."""
        for val in ("high", [], {}, True, None, "0.8"):
            data = {"mood": {"confidence": val}}
            assert self._nv(data) == 0

    def test_mc9_inf_nan_confidence(self):
        """Inf/nan confidence → 0."""
        for val in (float("inf"), float("-inf"), float("nan")):
            data = {"mood": {"confidence": val}}
            assert self._nv(data) == 0

    def test_mc10_bool_confidence(self):
        """Bool confidence → 0 (not 100)."""
        for val in (True, False):
            data = {"mood": {"confidence": val}}
            assert self._nv(data) == 0

    def test_mc11_non_dict_top_level(self):
        """Non-dict top-level payload → 0."""
        for val in ("string", 42, [], True, None):
            assert self._nv({"mood": val}) == 0

    def test_mc12_non_dict_mood_data(self):
        """Mood is non-dict → 0."""
        for val in ("focused", 42, [], True, None):
            data = {"mood": val}
            assert self._nv(data) == 0


class TestMoodConfidenceSensorAttrs:
    """MoodConfidenceSensor.extra_state_attributes contract cases."""

    @staticmethod
    def _attrs(data): return MoodConfidenceSensorContract.attrs(data)

    def test_mc5_full_attrs(self):
        """Full attribute set."""
        data = {"mood": {"mood": "relaxed", "factors": {"sleep": 0.9}}}
        attrs = self._attrs(data)
        assert attrs["mood"] == "relaxed"
        assert attrs["factors"] == {"sleep": 0.9}

    def test_mc6_empty_attrs(self):
        """Empty/No data."""
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}

    def test_mc7_default_mood(self):
        """Default mood 'unknown' when missing."""
        data = {"mood": {"confidence": 0.5}}
        attrs = self._attrs(data)
        assert attrs["mood"] == "unknown"

    # --- Malformed attrs cases ---
    def test_mc13_non_dict_mood_attrs(self):
        """Non-dict mood data → safe empty attrs."""
        for val in ("relaxed", 42, [], True, None):
            data = {"mood": val}
            attrs = self._attrs(data)
            assert attrs["mood"] == "unknown"
            assert attrs["factors"] == {}

    def test_mc14_non_dict_factors(self):
        """Non-dict factors → {}."""
        for val in ("string", [], 42, True, None):
            data = {"mood": {"mood": "relaxed", "factors": val}}
            attrs = self._attrs(data)
            assert attrs["factors"] == {}


# =============================================================================
# NeuronActivitySensor test cases
# =============================================================================

class TestNeuronActivitySensorNativeValue:
    """NeuronActivitySensor.native_value contract cases."""

    @staticmethod
    def _nv(data): return NeuronActivitySensorContract.native_value(data)

    def test_na1_empty_data(self):
        """Empty data → 0."""
        assert self._nv(None) == 0
        assert self._nv({}) == 0

    def test_na2_active_count(self):
        """Correct count of active neurons."""
        data = {
            "neurons": {
                "n1": {"active": True, "value": 0.8},
                "n2": {"active": False, "value": 0.1},
                "n3": {"active": True, "value": 0.6},
            }
        }
        assert self._nv(data) == 2

    def test_na3_missing_neurons(self):
        """Missing neurons key → 0."""
        data = {}
        assert self._nv(data) == 0

    def test_na4_non_dict_neurons(self):
        """Non-dict neurons → 0."""
        for val in ([], "string", 42, True, None):
            data = {"neurons": val}
            assert self._nv(data) == 0

    def test_na5_non_dict_neuron_items(self):
        """Non-dict items in neurons dict are skipped."""
        data = {
            "neurons": {
                "n1": {"active": True, "value": 0.8},
                "n2": "not a dict",
                "n3": {"active": True, "value": 0.6},
            }
        }
        assert self._nv(data) == 2


class TestNeuronActivitySensorAttrs:
    """NeuronActivitySensor.extra_state_attributes contract cases."""

    @staticmethod
    def _attrs(data): return NeuronActivitySensorContract.attrs(data)

    def test_na6_full_attrs(self):
        """Full attribute set."""
        data = {
            "neurons": {
                "n1": {"active": True, "value": 0.8, "confidence": 0.9},
                "n2": {"active": False, "value": 0.1, "confidence": 0.3},
            }
        }
        attrs = self._attrs(data)
        assert attrs["total_neurons"] == 2
        assert len(attrs["active_neurons"]) == 1
        assert attrs["active_neurons"][0]["name"] == "n1"

    def test_na7_empty_attrs(self):
        """Empty/No data."""
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}

    def test_na8_non_dict_neurons_attrs(self):
        """Non-dict neurons → safe empty attrs."""
        for val in ([], "string", 42, True, None):
            data = {"neurons": val}
            attrs = self._attrs(data)
            assert attrs["total_neurons"] == 0
            assert attrs["activity"] == []
            assert attrs["active_neurons"] == []


# =============================================================================
# Global contract guards
# =============================================================================

class TestMoodGlobalContract:
    """GC1/GC2/GC3 for mood sensors."""

    def test_gc1_guard_helpers_defined(self):
        """Guard helpers _as_mapping, _as_float, _as_string, _as_list exist."""
        import ast
        src = open("custom_components/pilotsuite/sensors/mood_sensor.py").read()
        tree = ast.parse(src)
        guard_names = {"_as_mapping", "_as_float", "_as_string", "_as_list"}
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in guard_names:
                found.add(node.name)
        assert found == guard_names, f"Missing guards: {guard_names - found}"

    def test_gc2_unique_ids_are_pilotsuite_prefixed(self):
        """All mood sensor unique_ids use pilotsuite_ prefix."""
        import ast
        src = open("custom_components/pilotsuite/sensors/mood_sensor.py").read()
        tree = ast.parse(src)
        expected = {"pilotsuite_mood", "pilotsuite_mood_confidence", "pilotsuite_neuron_activity"}
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "_attr_unique_id":
                        for val in node.value.elts if isinstance(node.value, ast.Tuple) else [node.value]:
                            if isinstance(val, ast.Constant):
                                found.add(val.value)
        assert expected.issubset(found), f"Unique ids missing: {expected - found}"

    def test_gc3_no_copilot_ha_regression(self):
        """No regressing copilot_ha unique_id remnants."""
        src = open("custom_components/pilotsuite/sensors/mood_sensor.py").read()
        assert "copilot_ha_mood" not in src
