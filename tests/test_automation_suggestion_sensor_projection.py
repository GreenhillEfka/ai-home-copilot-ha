"""AutomationSuggestionSensor — Projection Contract Tests.

Contract: AutomationSuggestionSensor ist reine Projection-Shell auf /api/v1/automations/suggestions.
Keine lokale Semantik — alle Werte kommen direkt vom Core-API.
"""
import pytest
from homeassistant.components.sensor import SensorEntity


# Contract Mirror
class AutomationSuggestionSensorContract:
    def __init__(self, *, ok=True, count=0, suggestions=None, status_code=200):
        self.ok = ok
        self.count = count
        self.suggestions = suggestions or []
        self.status_code = status_code

    def to_api_response(self):
        if self.status_code != 200:
            return None
        return {
            "ok": self.ok,
            "count": self.count,
            "suggestions": self.suggestions,
        }


def make_suggestion(id="s1", title="Test", category="energy", confidence=0.85, savings=None):
    """Factory für API-konforme suggestion dicts."""
    d = {"id": id, "title": title, "category": category, "confidence": confidence}
    if savings is not None:
        d["estimated_savings_eur"] = savings
    return d


# ─── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def coordinator():
    class FakeCoordinator:
        _session = None
        _config = {"host": "testhost", "port": 8909, "token": "testtoken"}
        _core_base_url_val = "http://127.0.0.1:8123"

        def _core_base_url(self):
            return self._core_base_url_val

        def _core_headers(self):
            return {"Authorization": "Bearer test"}
    return FakeCoordinator()


@pytest.fixture
def sensor(coordinator):
    from custom_components.copilot_ha.sensors.automation_suggestion_sensor import AutomationSuggestionSensor
    s = AutomationSuggestionSensor(coordinator)
    return s


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestNativeValue:
    """AS1: native_value spiegelt /api/v1/automations/suggestions count."""

    def test_as1_multiple(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=3,
            suggestions=[
                make_suggestion("s1", "Heizung"),
                make_suggestion("s2", "Licht"),
                make_suggestion("s3", "EV"),
            ]
        )
        sensor._suggestion_data = data.to_api_response()
        assert sensor.native_value == "3 Vorschläge"

    def test_as1_one(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=1,
            suggestions=[make_suggestion("s1", "Heizung")]
        )
        sensor._suggestion_data = data.to_api_response()
        assert sensor.native_value == "1 Vorschlag"

    def test_as1_zero(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=True, count=0, suggestions=[])
        sensor._suggestion_data = data.to_api_response()
        assert sensor.native_value == "Keine Vorschläge"

    def test_as1_ok_false(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=False, count=5)
        sensor._suggestion_data = data.to_api_response()
        assert sensor.native_value == "unavailable"

    def test_as1_data_none(self, sensor, coordinator):
        sensor._suggestion_data = None
        assert sensor.native_value == "unavailable"

    def test_as1_empty_dict(self, sensor, coordinator):
        sensor._suggestion_data = {}
        assert sensor.native_value == "unavailable"

    def test_as1_missing_ok_key(self, sensor, coordinator):
        sensor._suggestion_data = {"count": 5, "suggestions": []}
        assert sensor.native_value == "unavailable"


class TestIcon:
    """AS2: icon spiegelt Suggestion count → statisches mapping."""

    def test_as2_zero(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=True, count=0, suggestions=[])
        sensor._suggestion_data = data.to_api_response()
        assert sensor.icon == "mdi:check-circle"

    def test_as2_one(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=1,
            suggestions=[make_suggestion()]
        )
        sensor._suggestion_data = data.to_api_response()
        assert sensor.icon == "mdi:robot"

    def test_as2_few(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=3,
            suggestions=[make_suggestion(f"s{i}") for i in range(3)]
        )
        sensor._suggestion_data = data.to_api_response()
        assert sensor.icon == "mdi:robot"

    def test_as2_many(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=5,
            suggestions=[make_suggestion(f"s{i}") for i in range(5)]
        )
        sensor._suggestion_data = data.to_api_response()
        assert sensor.icon == "mdi:robot-expressive"

    def test_as2_ok_false(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=False, count=0)
        sensor._suggestion_data = data.to_api_response()
        assert sensor.icon == "mdi:robot-off"

    def test_as2_data_none(self, sensor, coordinator):
        sensor._suggestion_data = None
        assert sensor.icon == "mdi:robot-off"


class TestAttributes:
    """AS3: extra_state_attributes zeigt rohe Core-API-Daten ohne lokale Semantik."""

    def test_as3_full(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=2,
            suggestions=[
                make_suggestion("s1", "Heizung", "energy", 0.9, 120.50),
                make_suggestion("s2", "Licht", "lighting", 0.7, 45.0),
            ]
        )
        sensor._suggestion_data = data.to_api_response()
        attrs = sensor.extra_state_attributes

        assert attrs["status"] == "ok"
        assert attrs["total_count"] == 2
        assert attrs["source"] == "/api/v1/automations/suggestions"
        assert attrs["by_category"] == {"energy": 1, "lighting": 1}
        assert attrs["total_potential_savings_eur"] == 165.50

        top = attrs["top_suggestions"]
        assert len(top) == 2
        assert top[0]["id"] == "s1"
        assert top[0]["title"] == "Heizung"
        assert top[0]["category"] == "energy"
        assert top[0]["confidence"] == 0.9
        assert top[0]["savings_eur"] == 120.50

    def test_as3_empty(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=True, count=0, suggestions=[])
        sensor._suggestion_data = data.to_api_response()
        attrs = sensor.extra_state_attributes

        assert attrs["status"] == "ok"
        assert attrs["total_count"] == 0
        assert "by_category" not in attrs
        assert "top_suggestions" not in attrs

    def test_as3_unavailable(self, sensor, coordinator):
        sensor._suggestion_data = None
        attrs = sensor.extra_state_attributes
        assert attrs["status"] == "unavailable"
        assert "total_count" not in attrs

    def test_as3_not_list(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=True, count=3, suggestions="not a list")
        sensor._suggestion_data = data.to_api_response()
        attrs = sensor.extra_state_attributes
        assert attrs["status"] == "ok"
        assert attrs["total_count"] == 3
        assert "by_category" not in attrs

    def test_as3_non_dict_items(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=2,
            suggestions=["string item", 123, None]
        )
        sensor._suggestion_data = data.to_api_response()
        attrs = sensor.extra_state_attributes
        assert attrs["status"] == "ok"
        assert attrs["total_count"] == 2
        assert "by_category" not in attrs


class TestGlobalContract:
    """GC: Pure projection shell, keine lokale Semantik-Invention."""

    def test_gc1_source_endpoint(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(ok=True, count=1, suggestions=[make_suggestion()])
        sensor._suggestion_data = data.to_api_response()
        attrs = sensor.extra_state_attributes
        assert attrs["source"] == "/api/v1/automations/suggestions"

    def test_gc2_no_local_semantics(self, sensor, coordinator):
        data = AutomationSuggestionSensorContract(
            ok=True, count=1,
            suggestions=[make_suggestion("x", "Test", "test", 0.5, 10.0)]
        )
        sensor._suggestion_data = data.to_api_response()

        # native_value: pure Stringformatierung von count
        assert sensor.native_value == "1 Vorschlag"
        # icon: statisches Schwellenwert-Mapping, keine ML/Heuristik
        assert sensor.icon == "mdi:robot"
        # attrs: reine Core-Daten-Weitergabe
        attrs = sensor.extra_state_attributes
        assert attrs["total_count"] == 1
        assert attrs["status"] == "ok"
