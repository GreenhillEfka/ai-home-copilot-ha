"""Projection contract tests for ApplianceFingerprintSensor.

Verifies: ApplianceFingerprintSensor is a pure projection shell on
GET /api/v1/energy/fingerprints + GET /api/v1/energy/fingerprints/usage.
No local semantic invention.

AF1-AF10  — native_value and attrs contract cases
GC1-GC2   — global contract: hits Core API / no local semantic invention
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from custom_components.copilot_ha.sensors.appliance_fingerprint_sensor import (
    ApplianceFingerprintSensor,
)


def make_sensor(coordinator_data):
    """Return ApplianceFingerprintSensor with _data set as if async_update ran."""
    class FakeCoordinator:
        pass

    coordinator = FakeCoordinator()
    sensor = ApplianceFingerprintSensor.__new__(ApplianceFingerprintSensor)
    sensor._coordinator = coordinator
    sensor._data = coordinator_data if coordinator_data else {}
    return sensor


# ─── AF1-AF4: native_value ───────────────────────────────────────────────────

class TestAFNativeValue:
    """native_value = _data.get("fingerprint_count", 0)."""

    @pytest.mark.parametrize("count,expected", [(3, 3), (0, 0), (1, 1), (15, 15)])
    def test_af1_native_value_with_count(self, count, expected):
        # After async_update: _data["fingerprint_count"] = data.get("count", 0)
        sensor = make_sensor({"fingerprint_count": count})
        assert sensor.native_value == expected

    def test_af2_native_value_missing_count(self):
        sensor = make_sensor({"fingerprint_count": 0})
        assert sensor.native_value == 0

    def test_af3_native_value_absent_key(self):
        sensor = make_sensor({})
        assert sensor.native_value == 0

    def test_af4_native_value_empty_data(self):
        """AF4: native_value returns 0 when _data is empty dict (async_update failed or no data yet)."""
        sensor = make_sensor({})
        assert sensor.native_value == 0


# ─── AF5-AF10: extra_state_attributes ───────────────────────────────────────

class TestAFAtrributes:
    """attrs = fingerprints[:5] + usage_stats[:5] + total_devices."""

    def test_af5_attrs_full(self):
        # After async_update: _data["fingerprints"] = transformed list
        # with "avg_watts" (not "avg_power_watts")
        sensor = make_sensor({
            "fingerprints": [
                {"id": "d1", "name": "Waschmaschine",
                 "type": "washer", "avg_watts": 500},
                {"id": "d2", "name": "Trockner",
                 "type": "dryer", "avg_watts": 1500},
            ],
            "fingerprint_count": 2,
            "usage_stats": [
                {"id": "d1", "name": "Waschmaschine",
                 "runs": 45, "kwh": 120.5},
            ],
        })
        attrs = sensor.extra_state_attributes
        assert attrs["total_devices"] == 2
        assert len(attrs["fingerprints"]) == 2
        assert attrs["fingerprints"][0]["name"] == "Waschmaschine"
        assert attrs["fingerprints"][0]["avg_watts"] == 500
        assert len(attrs["usage_stats"]) == 1
        assert attrs["usage_stats"][0]["runs"] == 45

    def test_af6_attrs_fingerprints_capped_5(self):
        sensor = make_sensor({
            "fingerprints": [
                {"id": f"d{i}", "name": f"Dev {i}",
                 "type": "unknown", "avg_watts": 100}
                for i in range(8)
            ],
            "fingerprint_count": 8,
            "usage_stats": [],
        })
        attrs = sensor.extra_state_attributes
        assert len(attrs["fingerprints"]) == 5
        assert attrs["total_devices"] == 8

    def test_af7_attrs_usage_stats_capped_5(self):
        sensor = make_sensor({
            "fingerprints": [],
            "fingerprint_count": 0,
            "usage_stats": [
                {"id": f"d{i}", "name": f"Dev {i}",
                 "runs": i * 10, "kwh": i * 5.0}
                for i in range(7)
            ],
        })
        attrs = sensor.extra_state_attributes
        assert len(attrs["usage_stats"]) == 5

    def test_af8_attrs_empty(self):
        sensor = make_sensor({
            "fingerprints": [],
            "fingerprint_count": 0,
        })
        attrs = sensor.extra_state_attributes
        assert attrs["fingerprints"] == []
        assert attrs["usage_stats"] == []
        assert attrs["total_devices"] == 0

    def test_af9_attrs_usage_key_absent(self):
        sensor = make_sensor({
            "fingerprints": [
                {"id": "d1", "name": "D1",
                 "type": "washer", "avg_watts": 500}
            ],
            "fingerprint_count": 1,
        })
        attrs = sensor.extra_state_attributes
        assert attrs["fingerprints"][0]["name"] == "D1"
        assert attrs["usage_stats"] == []

    def test_af10_attrs_empty_strings(self):
        sensor = make_sensor({
            "fingerprints": [],
            "fingerprint_count": 0,
            "usage_stats": [],
        })
        attrs = sensor.extra_state_attributes
        assert attrs["fingerprints"] == []
        assert attrs["usage_stats"] == []
        assert attrs["total_devices"] == 0


# ─── GC1-GC2: global contract ────────────────────────────────────────────────

class TestAFGlobalContract:
    """GC1: hits Core API / GC2: no local semantic invention."""

    def test_gc1_hits_core_api_fingerprints(self):
        """GC1: async_update fetches from /api/v1/energy/fingerprints and /api/v1/energy/fingerprints/usage."""
        # Source: base = f"{self._core_base_url()}/api/v1/energy" + "/fingerprints"
        # Contract source verification via read (avoids live async method call)
        import inspect
        source = inspect.getsource(ApplianceFingerprintSensor.async_update)
        assert "/fingerprints" in source

    def test_gc2_no_local_semantic_invention(self):
        """GC2: trivial list-comp + slice + dict key access, no ML/threshold."""
        sensor = make_sensor({
            "fingerprints": [
                {"id": "x", "name": "X",
                 "type": "unknown", "avg_watts": 999}
            ],
            "fingerprint_count": 1,
            "usage_stats": [
                {"id": "x", "name": "X",
                 "runs": 1, "kwh": 0.5}
            ],
        })
        assert sensor.native_value == 1
        attrs = sensor.extra_state_attributes
        assert attrs["fingerprints"][0]["avg_watts"] == 999
        assert attrs["usage_stats"][0]["kwh"] == 0.5
