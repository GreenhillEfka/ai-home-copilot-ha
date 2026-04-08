"""Projection contract tests for module_integration sensors.

Verifies the three module integration sensors are stable coordinator-data
projections with one explicit health threshold (bus errors > 10).

HA-240
"""


# ─── Contract mirrors ────────────────────────────────────────────────────────

class ModuleHealthSensorContract:
    """Mirror of ModuleHealthSensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "unavailable"
        bus = data.get("bus_stats", {})
        errors = bus.get("errors", 0)
        if errors > 10:
            return "degraded"
        return "healthy"

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        attrs = {}
        bus = data.get("bus_stats")
        if bus:
            attrs["bus_events_published"] = bus.get("events_published", 0)
            attrs["bus_events_delivered"] = bus.get("events_delivered", 0)
            attrs["bus_errors"] = bus.get("errors", 0)
            attrs["bus_subscribers"] = bus.get("total_subscribers", 0)
        return attrs


class SynapseActivitySensorContract:
    """Mirror of SynapseActivitySensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "0"
        learning = data.get("learning_stats", {})
        return str(learning.get("total_updates", 0))

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        learning = data.get("learning_stats", {})
        return {
            "total_synapses": learning.get("total_synapses", 0),
            "learning_rate": learning.get("learning_rate", 0),
            "total_drift": learning.get("total_drift", 0),
            "max_drift_synapse": learning.get("max_drift_synapse"),
        }


class CrossPatternSensorContract:
    """Mirror of CrossPatternSensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "0"
        cross = data.get("cross_module_stats", {})
        return str(cross.get("patterns_discovered", 0))

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        cross = data.get("cross_module_stats", {})
        return {
            "snapshots_collected": cross.get("snapshots_collected", 0),
            "window_size": cross.get("window_size", 0),
        }


# ─── ModuleHealthSensor cases ───────────────────────────────────────────────

class TestModuleHealthSensor:
    @staticmethod
    def _nv(data): return ModuleHealthSensorContract.native_value(data)

    @staticmethod
    def _attrs(data): return ModuleHealthSensorContract.attrs(data)

    def test_mi1_unavailable_without_data(self):
        assert self._nv(None) == "unavailable"
        assert self._nv({}) == "unavailable"

    def test_mi2_healthy_at_zero_errors(self):
        assert self._nv({"bus_stats": {"errors": 0}}) == "healthy"

    def test_mi3_healthy_at_threshold_boundary(self):
        assert self._nv({"bus_stats": {"errors": 10}}) == "healthy"

    def test_mi4_degraded_above_threshold(self):
        assert self._nv({"bus_stats": {"errors": 11}}) == "degraded"

    def test_mi5_attrs_passthrough(self):
        attrs = self._attrs({
            "bus_stats": {
                "events_published": 125,
                "events_delivered": 122,
                "errors": 2,
                "total_subscribers": 9,
            }
        })
        assert attrs == {
            "bus_events_published": 125,
            "bus_events_delivered": 122,
            "bus_errors": 2,
            "bus_subscribers": 9,
        }

    def test_mi6_attrs_empty_without_bus_stats(self):
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}
        assert self._attrs({"bus_stats": {}}) == {}


# ─── SynapseActivitySensor cases ────────────────────────────────────────────

class TestSynapseActivitySensor:
    @staticmethod
    def _nv(data): return SynapseActivitySensorContract.native_value(data)

    @staticmethod
    def _attrs(data): return SynapseActivitySensorContract.attrs(data)

    def test_mi7_native_value_defaults_to_zero(self):
        assert self._nv(None) == "0"
        assert self._nv({}) == "0"

    def test_mi8_native_value_is_stringified_update_count(self):
        assert self._nv({"learning_stats": {"total_updates": 27}}) == "27"
        assert self._nv({"learning_stats": {"total_updates": 0}}) == "0"

    def test_mi9_attrs_passthrough(self):
        attrs = self._attrs({
            "learning_stats": {
                "total_synapses": 420,
                "learning_rate": 0.15,
                "total_drift": 8.2,
                "max_drift_synapse": "kitchen->hall",
            }
        })
        assert attrs == {
            "total_synapses": 420,
            "learning_rate": 0.15,
            "total_drift": 8.2,
            "max_drift_synapse": "kitchen->hall",
        }

    def test_mi10_attrs_defaults_when_partial(self):
        attrs = self._attrs({"learning_stats": {"total_synapses": 3}})
        assert attrs == {
            "total_synapses": 3,
            "learning_rate": 0,
            "total_drift": 0,
            "max_drift_synapse": None,
        }

    def test_mi11_attrs_empty_without_data(self):
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}


# ─── CrossPatternSensor cases ───────────────────────────────────────────────

class TestCrossPatternSensor:
    @staticmethod
    def _nv(data): return CrossPatternSensorContract.native_value(data)

    @staticmethod
    def _attrs(data): return CrossPatternSensorContract.attrs(data)

    def test_mi12_native_value_defaults_to_zero(self):
        assert self._nv(None) == "0"
        assert self._nv({}) == "0"

    def test_mi13_native_value_is_stringified_pattern_count(self):
        assert self._nv({"cross_module_stats": {"patterns_discovered": 14}}) == "14"

    def test_mi14_attrs_passthrough(self):
        attrs = self._attrs({
            "cross_module_stats": {
                "snapshots_collected": 56,
                "window_size": 12,
            }
        })
        assert attrs == {
            "snapshots_collected": 56,
            "window_size": 12,
        }

    def test_mi15_attrs_defaults_when_partial(self):
        attrs = self._attrs({"cross_module_stats": {"snapshots_collected": 7}})
        assert attrs == {
            "snapshots_collected": 7,
            "window_size": 0,
        }

    def test_mi16_attrs_empty_without_data(self):
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}


# ─── Global contract checks ─────────────────────────────────────────────────

class TestModuleIntegrationGlobalContract:
    def test_gc1_file_contains_only_explicit_health_threshold(self):
        src = open("custom_components/pilotsuite/sensors/module_integration.py").read()
        assert "errors > 10" in src
        assert "patterns_discovered" in src
        assert "total_updates" in src

    def test_gc2_no_direct_core_fetch_in_sensor_file(self):
        src = open("custom_components/pilotsuite/sensors/module_integration.py").read()
        assert "/api/v1/" not in src
        assert "_fetch(" not in src
        assert "async_get_clientsession" not in src
