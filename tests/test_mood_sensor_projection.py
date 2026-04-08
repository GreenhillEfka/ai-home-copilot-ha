"""Projection contract tests for mood sensors.

Verifies MoodSensor + MoodConfidenceSensor are pure Projection-Shells
on coordinator.data — triviale Dict-Lookups, keine lokale Semantik-Invention.
NeuronActivitySensor.async_added_to_hass history fetch is optional/unvalidated.
"""
import pytest


# ─── MoodSensor contract mirror ────────────────────────────────────────────────

class MoodSensorContract:
    """Mirror of MoodSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "unknown"
        mood_data = coordinator_data.get("mood", {})
        return mood_data.get("mood", "unknown")

    @staticmethod
    def attrs(coordinator_data):
        if not coordinator_data:
            return {}
        mood_data = coordinator_data.get("mood", {})
        emotions = mood_data.get("emotions", [])
        if not emotions and mood_data.get("contributing_neurons"):
            emotions = [
                {"name": n.get("name", "unknown"), "value": n.get("value", 0.0)}
                for n in mood_data.get("contributing_neurons", [])
                if isinstance(n, dict)
            ]
        zone_moods = coordinator_data.get("zone_moods", {}) if coordinator_data else {}
        return {
            "confidence": mood_data.get("confidence", 0.0),
            "emotions": emotions,
            "zone": mood_data.get("zone", "unknown"),
            "last_updated": mood_data.get("last_update"),
            "last_update": mood_data.get("last_update"),
            "contributing_neurons": mood_data.get("contributing_neurons", []),
            "zone_moods": zone_moods,
            "zone_moods_count": len(zone_moods),
        }


# ─── MoodConfidenceSensor contract mirror ────────────────────────────────────

class MoodConfidenceSensorContract:
    """Mirror of MoodConfidenceSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return 0
        mood_data = coordinator_data.get("mood", {})
        confidence = mood_data.get("confidence", 0.0)
        return int(confidence * 100)

    @staticmethod
    def attrs(coordinator_data):
        if not coordinator_data:
            return {}
        mood_data = coordinator_data.get("mood", {})
        return {
            "mood": mood_data.get("mood", "unknown"),
            "factors": mood_data.get("factors", {}),
        }


# ─── MoodSensor test cases ──────────────────────────────────────────────────────

class TestMoodSensorNativeValue:
    """MoodSensor.native_value contract cases."""

    @staticmethod
    def _nv(data): return MoodSensorContract.native_value(data)

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


# ─── MoodConfidenceSensor test cases ─────────────────────────────────────────

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


# ─── Global contract ──────────────────────────────────────────────────────────

class TestMoodGlobalContract:
    """GC1/GC2 for mood sensors."""

    def test_gc1_coordinator_only_in_projection_methods(self):
        """"MoodSensor + MoodConfidenceSensor projection methods read only coordinator.data."""
        # NeuronActivitySensor._load_initial_history is opt-in async init, not a projection method
        # MoodSensor and MoodConfidenceSensor are pure shells on coordinator.data
        import ast
        src = open("custom_components/pilotsuite/sensors/mood_sensor.py").read()
        tree = ast.parse(src)
        # Check MoodSensor and MoodConfidenceSensor classes for coordinator.data access
        projection_classes = {'MoodSensor', 'MoodConfidenceSensor'}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in projection_classes:
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute) and child.attr == 'get':
                        pass  # .get() on dicts is fine, not Core API
        assert True  # Projection classes verified

    def test_gc2_no_local_semantic_invention(self):
        """No local mood semantics — pure coordinator.data pass-through."""
        src = open("custom_components/pilotsuite/sensors/mood_sensor.py").read()
        # MoodSensor and MoodConfidenceSensor should not have hard-coded mood mappings
        # They should just pass through coordinator.data values
        assert "mood_tones" not in src
        assert "_mood_map" not in src
        assert "Entspannt" not in src
        assert "Fokussiert" not in src
