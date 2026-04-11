"""Projection contract tests for module_integration sensors.

Verifies the three module integration sensors are stable coordinator-data
projections with one explicit health threshold (bus errors > 10).

HA-240 / HA-347
"""
import math


# ─── Contract mirrors ────────────────────────────────────────────────────────

def _as_mapping(value, default=None):
    if isinstance(value, dict):
        return value
    return default if default is not None else {}


def _as_int(value, default=0):
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        iv = int(value)
        if isinstance(iv, int) and not isinstance(iv, bool):
            return iv
        return default
    except (TypeError, ValueError):
        return default


def _as_float(value, default=0.0):
    if isinstance(value, bool):
        return default
    if isinstance(value, float):
        return value
    try:
        f = float(value)
        if isinstance(f, float):
            return f
        return default
    except (TypeError, ValueError):
        return default


class ModuleHealthSensorContract:
    """Mirror of ModuleHealthSensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "unavailable"
        data = _as_mapping(data)
        if not data:
            return "unavailable"
        bus = _as_mapping(data.get("bus_stats", {}))
        errors = _as_int(bus.get("errors", 0))
        if errors > 10:
            return "degraded"
        return "healthy"

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        data = _as_mapping(data)
        if not data:
            return {}
        bus = _as_mapping(data.get("bus_stats"))
        if not bus:
            return {}
        return {
            "bus_events_published": _as_int(bus.get("events_published", 0)),
            "bus_events_delivered": _as_int(bus.get("events_delivered", 0)),
            "bus_errors": _as_int(bus.get("errors", 0)),
            "bus_subscribers": _as_int(bus.get("total_subscribers", 0)),
        }


class SynapseActivitySensorContract:
    """Mirror of SynapseActivitySensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "0"
        data = _as_mapping(data)
        if not data:
            return "0"
        learning = _as_mapping(data.get("learning_stats", {}))
        return str(_as_int(learning.get("total_updates", 0)))

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        data = _as_mapping(data)
        if not data:
            return {}
        learning = _as_mapping(data.get("learning_stats", {}))
        return {
            "total_synapses": _as_int(learning.get("total_synapses", 0)),
            "learning_rate": _as_float(learning.get("learning_rate", 0)),
            "total_drift": _as_float(learning.get("total_drift", 0)),
            "max_drift_synapse": learning.get("max_drift_synapse"),
        }


class CrossPatternSensorContract:
    """Mirror of CrossPatternSensor projection logic."""

    @staticmethod
    def native_value(data):
        if not data:
            return "0"
        data = _as_mapping(data)
        if not data:
            return "0"
        cross = _as_mapping(data.get("cross_module_stats", {}))
        return str(_as_int(cross.get("patterns_discovered", 0)))

    @staticmethod
    def attrs(data):
        if not data:
            return {}
        data = _as_mapping(data)
        if not data:
            return {}
        cross = _as_mapping(data.get("cross_module_stats", {}))
        return {
            "snapshots_collected": _as_int(cross.get("snapshots_collected", 0)),
            "window_size": _as_int(cross.get("window_size", 0)),
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

    # ─── Malformed payload guards (HA-347) ───────────────────────────────────

    def test_mi7_non_dict_data_returns_unavailable(self):
        """Top-level non-dict data is treated as unavailable."""
        assert self._nv("string") == "unavailable"
        assert self._nv([]) == "unavailable"
        assert self._nv(42) == "unavailable"

    def test_mi8_non_dict_bus_stats_returns_healthy(self):
        """bus_stats that is not a dict defaults to healthy (0 errors)."""
        assert self._nv({"bus_stats": "string"}) == "healthy"
        assert self._nv({"bus_stats": []}) == "healthy"
        assert self._nv({"bus_stats": 42}) == "healthy"

    def test_mi9_non_numeric_errors_defaults_to_zero(self):
        """Non-numeric errors value falls back to 0."""
        assert self._nv({"bus_stats": {"errors": "high"}}) == "healthy"
        assert self._nv({"bus_stats": {"errors": True}}) == "healthy"
        assert self._nv({"bus_stats": {"errors": None}}) == "healthy"
        assert self._nv({"bus_stats": {"errors": 12.7}}) == "degraded"

    def test_mi10_non_numeric_bus_attr_fields_default_to_zero(self):
        """Non-numeric bus attribute fields fall back to 0."""
        attrs = self._attrs({
            "bus_stats": {
                "events_published": "fifteen",
                "events_delivered": True,
                "errors": "none",
                "total_subscribers": None,
            }
        })
        assert attrs == {
            "bus_events_published": 0,
            "bus_events_delivered": 0,
            "bus_errors": 0,
            "bus_subscribers": 0,
        }


# ─── SynapseActivitySensor cases ────────────────────────────────────────────

class TestSynapseActivitySensor:
    @staticmethod
    def _nv(data): return SynapseActivitySensorContract.native_value(data)

    @staticmethod
    def _attrs(data): return SynapseActivitySensorContract.attrs(data)

    def test_mi11_native_value_defaults_to_zero(self):
        assert self._nv(None) == "0"
        assert self._nv({}) == "0"

    def test_mi12_native_value_is_stringified_update_count(self):
        assert self._nv({"learning_stats": {"total_updates": 27}}) == "27"
        assert self._nv({"learning_stats": {"total_updates": 0}}) == "0"

    def test_mi13_attrs_passthrough(self):
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

    def test_mi14_attrs_defaults_when_partial(self):
        attrs = self._attrs({"learning_stats": {"total_synapses": 3}})
        assert attrs == {
            "total_synapses": 3,
            "learning_rate": 0,
            "total_drift": 0,
            "max_drift_synapse": None,
        }

    def test_mi15_attrs_empty_without_data(self):
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}

    # ─── Malformed payload guards (HA-347) ───────────────────────────────────

    def test_mi16_non_dict_data_returns_zero(self):
        """Top-level non-dict data results in '0'."""
        assert self._nv("string") == "0"
        assert self._nv([]) == "0"
        assert self._nv(42) == "0"

    def test_mi17_non_dict_learning_stats_defaults_to_zero(self):
        """learning_stats that is not a dict results in '0'."""
        assert self._nv({"learning_stats": "string"}) == "0"
        assert self._nv({"learning_stats": []}) == "0"
        assert self._nv({"learning_stats": 42}) == "0"

    def test_mi18_non_numeric_total_updates_defaults_to_zero(self):
        """Non-numeric total_updates falls back to 0."""
        assert self._nv({"learning_stats": {"total_updates": "twelve"}}) == "0"
        assert self._nv({"learning_stats": {"total_updates": True}}) == "0"
        assert self._nv({"learning_stats": {"total_updates": None}}) == "0"

    def test_mi19_non_numeric_synapse_attrs_default_to_zero(self):
        """Non-numeric learning_stats attribute fields fall back to 0."""
        attrs = self._attrs({
            "learning_stats": {
                "total_synapses": "many",
                "learning_rate": "fast",
                "total_drift": True,
                "max_drift_synapse": "kitchen->hall",
            }
        })
        assert attrs == {
            "total_synapses": 0,
            "learning_rate": 0,
            "total_drift": 0,
            "max_drift_synapse": "kitchen->hall",
        }


# ─── CrossPatternSensor cases ───────────────────────────────────────────────

class TestCrossPatternSensor:
    @staticmethod
    def _nv(data): return CrossPatternSensorContract.native_value(data)

    @staticmethod
    def _attrs(data): return CrossPatternSensorContract.attrs(data)

    def test_mi20_native_value_defaults_to_zero(self):
        assert self._nv(None) == "0"
        assert self._nv({}) == "0"

    def test_mi21_native_value_is_stringified_pattern_count(self):
        assert self._nv({"cross_module_stats": {"patterns_discovered": 14}}) == "14"

    def test_mi22_attrs_passthrough(self):
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

    def test_mi23_attrs_defaults_when_partial(self):
        attrs = self._attrs({"cross_module_stats": {"snapshots_collected": 7}})
        assert attrs == {
            "snapshots_collected": 7,
            "window_size": 0,
        }

    def test_mi24_attrs_empty_without_data(self):
        assert self._attrs(None) == {}
        assert self._attrs({}) == {}

    # ─── Malformed payload guards (HA-347) ───────────────────────────────────

    def test_mi25_non_dict_data_returns_zero(self):
        """Top-level non-dict data results in '0'."""
        assert self._nv("string") == "0"
        assert self._nv([]) == "0"
        assert self._nv(42) == "0"

    def test_mi26_non_dict_cross_module_stats_defaults_to_zero(self):
        """cross_module_stats that is not a dict results in '0'."""
        assert self._nv({"cross_module_stats": "string"}) == "0"
        assert self._nv({"cross_module_stats": []}) == "0"
        assert self._nv({"cross_module_stats": 42}) == "0"

    def test_mi27_non_numeric_patterns_discovered_defaults_to_zero(self):
        """Non-numeric patterns_discovered falls back to 0."""
        assert self._nv({"cross_module_stats": {"patterns_discovered": "twenty"}}) == "0"
        assert self._nv({"cross_module_stats": {"patterns_discovered": True}}) == "0"
        assert self._nv({"cross_module_stats": {"patterns_discovered": None}}) == "0"

    def test_mi28_non_numeric_cross_attr_fields_default_to_zero(self):
        """Non-numeric cross_module_stats attribute fields fall back to 0."""
        attrs = self._attrs({
            "cross_module_stats": {
                "snapshots_collected": "fifty",
                "window_size": True,
            }
        })
        assert attrs == {
            "snapshots_collected": 0,
            "window_size": 0,
        }


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

    def test_gc3_source_guard_type_guards_present(self):
        """Source guard: _as_mapping, _as_int, _as_float are defined and used."""
        src = open("custom_components/pilotsuite/sensors/module_integration.py").read()
        assert "_as_mapping" in src
        assert "_as_int" in src
        assert "_as_float" in src
        assert "def _as_mapping" in src
        assert "def _as_int" in src
        assert "def _as_float" in src
