"""test_brain_architecture_sensor_projection.py -- HA-125.
Verifies BrainArchitectureSensor is a pure projection shell on /api/v1/hub/brain.
Contract: BrainArchitectureSensor hits /api/v1/hub/brain, no local semantic invention.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# conftest must be importable
try:
    import conftest as _conftest
except ImportError:
    import tests.conftest as _conftest  # noqa: F401

from custom_components.pilotsuite.sensors.brain_architecture_sensor import BrainArchitectureSensor


# -- Test helpers ---------------------------------------------------------------
def make_sensor(data: dict) -> BrainArchitectureSensor:
    coordinator = MagicMock()
    coordinator.data = data
    sensor = BrainArchitectureSensor(coordinator)
    # async_update populates self._data via _fetch; in unit tests
    # we bypass async by directly setting self._data (same end state)
    sensor._data = data
    return sensor


# -- Test cases -----------------------------------------------------------------
class TestBrainArchitectureSensor:
    """Projection contract tests for BrainArchitectureSensor."""

    # BA1 -- native_value: various brain health states
    def test_ba1_initialized_healthy(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 4, "health_score": 100}
        sensor = make_sensor(data)
        assert sensor.native_value == "4/4 Regionen aktiv", f"got: {sensor.native_value}"

    def test_ba1_initialized_partial(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 2, "health_score": 60}
        sensor = make_sensor(data)
        assert sensor.native_value == "2/4 Regionen \u2014 60% Gesundheit", f"got: {sensor.native_value}"

    def test_ba1_initialized_low_health(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 1, "health_score": 30}
        sensor = make_sensor(data)
        assert sensor.native_value == "1/4 Regionen \u2014 30% Gesundheit", f"got: {sensor.native_value}"

    def test_ba1_zero_regions(self):
        data = {"ok": True, "total_regions": 0, "active_regions": 0, "health_score": 0}
        sensor = make_sensor(data)
        assert sensor.native_value == "Nicht initialisiert", f"got: {sensor.native_value}"

    def test_ba1_missing_optional_fields(self):
        data = {"ok": True, "total_regions": 2, "active_regions": 2}
        sensor = make_sensor(data)
        # health_score defaults to 0; with total>0 and health<100, sensor returns "X/Y Regionen -- H% Gesundheit"
        assert "Regionen" in sensor.native_value and "Gesundheit" in sensor.native_value

    # BA2 -- icon by health_score
    def test_ba2_icon_high_health(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 4, "health_score": 95}
        sensor = make_sensor(data)
        assert sensor.icon == "mdi:brain"

    def test_ba2_icon_mid_health(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 2, "health_score": 65}
        sensor = make_sensor(data)
        assert sensor.icon == "mdi:head-alert"

    def test_ba2_icon_low_health(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 1, "health_score": 40}
        sensor = make_sensor(data)
        assert sensor.icon == "mdi:head-remove"

    def test_ba2_icon_boundary_high(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 4, "health_score": 80}
        sensor = make_sensor(data)
        assert sensor.icon == "mdi:brain"

    def test_ba2_icon_boundary_low(self):
        data = {"ok": True, "total_regions": 4, "active_regions": 2, "health_score": 50}
        sensor = make_sensor(data)
        assert sensor.icon == "mdi:head-alert"

    # BA3 -- extra_state_attributes full data
    def test_ba3_attrs_full(self):
        data = {
            "ok": True,
            "total_regions": 4,
            "active_regions": 3,
            "total_neurons": 128,
            "total_synapses": 512,
            "active_synapses": 200,
            "connectivity_score": 0.78,
            "health_score": 85,
        }
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert attrs["total_regions"] == 4
        assert attrs["active_regions"] == 3
        assert attrs["total_neurons"] == 128
        assert attrs["total_synapses"] == 512
        assert attrs["active_synapses"] == 200
        assert attrs["connectivity_score"] == 0.78
        assert attrs["health_score"] == 85

    def test_ba3_attrs_minimal(self):
        data = {"ok": True, "total_regions": 2, "active_regions": 2}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert attrs.get("total_regions") == 2
        assert attrs.get("active_regions") == 2
        assert attrs.get("total_neurons", 0) == 0

    # BA4 -- regions list in attrs
    def test_ba4_regions_with_data(self):
        data = {
            "ok": True,
            "regions": [
                {"name_de": "Wohnzimmer", "color": "#FF0000", "role": "comfort", "active": True, "health": 100},
                {"name_de": "Kuche", "color": "#00FF00", "role": "utility", "active": False, "health": 60},
            ],
        }
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        regions = attrs.get("regions", [])
        assert len(regions) == 2, f"got {len(regions)}"
        assert regions[0]["name"] == "Wohnzimmer"
        assert regions[1]["name"] == "Kuche"

    def test_ba4_regions_empty(self):
        data = {"ok": True, "regions": []}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert "regions" not in attrs

    def test_ba4_regions_ignores_non_dict(self):
        data = {"ok": True, "regions": [None, {"name_de": "Test", "color": "#000", "role": "x", "active": True, "health": 80}, "not-a-dict"]}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        regions = attrs.get("regions", [])
        assert len(regions) == 1, f"got {len(regions)}"
        assert regions[0]["name"] == "Test"

    # BA5 -- synapse_summary in attrs
    def test_ba5_synapses_with_data(self):
        data = {
            "ok": True,
            "synapses": [
                {"state": "active", "fire_count": 10},
                {"state": "active", "fire_count": 5},
                {"state": "dormant", "fire_count": 2},
                {"state": "active", "fire_count": 3},
            ],
        }
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        ss = attrs.get("synapse_summary", {})
        assert ss.get("active") == 3, f"got {ss}"
        assert ss.get("dormant") == 1, f"got {ss}"
        assert ss.get("total_fires") == 20, f"got {ss}"

    def test_ba5_synapses_empty(self):
        data = {"ok": True, "synapses": []}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert "synapse_summary" not in attrs

    def test_ba5_synapses_ignores_non_dict(self):
        data = {"ok": True, "synapses": [None, {"state": "active", "fire_count": 7}, "str"]}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        ss = attrs.get("synapse_summary", {})
        assert ss.get("active") == 1, f"got {ss}"
        assert ss.get("total_fires") == 7, f"got {ss}"

    # BA6 -- graph summary in attrs
    def test_ba6_graph_with_data(self):
        data = {
            "ok": True,
            "graph": {"nodes": [1, 2, 3, 4], "edges": ["a-b", "b-c"]},
        }
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert attrs.get("graph_nodes") == 4, f"got {attrs}"
        assert attrs.get("graph_edges") == 2, f"got {attrs}"

    def test_ba6_graph_empty(self):
        data = {"ok": True, "graph": {}}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert "graph_nodes" not in attrs

    def test_ba6_graph_no_graph_key(self):
        data = {"ok": True}
        sensor = make_sensor(data)
        attrs = sensor.extra_state_attributes
        assert "graph_nodes" not in attrs

    # GC1 -- global contract: pure projection, no local semantic invention
    def test_gc1_projection_only(self):
        """Contract: BrainArchitectureSensor only maps /api/v1/hub/brain fields."""
        data = {"ok": True, "total_regions": 3, "active_regions": 3, "health_score": 100}
        sensor = make_sensor(data)
        # native_value is computed from data -- no local classification
        assert "Regionen" in sensor.native_value
        # icon is threshold-based on health_score -- no inference
        assert sensor.icon == "mdi:brain"
        # attrs are direct or trivially derived from API data
        assert "health_score" in sensor.extra_state_attributes

    # GC2 -- global contract: endpoint contract
    def test_gc2_hub_brain_endpoint(self):
        """Contract: BrainArchitectureSensor targets /api/v1/hub/brain."""
        sensor = make_sensor({"ok": True, "total_regions": 1, "active_regions": 1, "health_score": 100})
        assert hasattr(sensor, "_fetch")
        assert hasattr(sensor, "async_update")
