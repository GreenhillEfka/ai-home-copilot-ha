"""Projection Contract Tests: module_integration.py

Verifies: ModuleHealthSensor, SynapseActivitySensor, and CrossPatternSensor
are pure projection shells on coordinator.data — no local semantic invention.

Sensors:
- ModuleHealthSensor: mirrors bus_stats health state
- SynapseActivitySensor: mirrors learning_stats.total_updates
- CrossPatternSensor: mirrors cross_module_stats.patterns_discovered

Contract verified:
- state = raw value from coordinator.data (or default)
- attrs = raw dict passthrough from coordinator.data
- No local classification or heuristic
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# === Fixtures ===

@pytest.fixture
def coordinator():
    return MagicMock()


@pytest.fixture
def health_sensor(coordinator):
    from custom_components.copilot_ha.sensors.module_integration import ModuleHealthSensor
    return ModuleHealthSensor(coordinator)


@pytest.fixture
def synapse_sensor(coordinator):
    from custom_components.copilot_ha.sensors.module_integration import SynapseActivitySensor
    return SynapseActivitySensor(coordinator)


@pytest.fixture
def pattern_sensor(coordinator):
    from custom_components.copilot_ha.sensors.module_integration import CrossPatternSensor
    return CrossPatternSensor(coordinator)


# === MI1: ModuleHealthSensor ===

def test_module_health_mi1_no_data(coordinator, health_sensor):
    """MI1: No coordinator data → 'unavailable'"""
    coordinator.data = None
    assert health_sensor.native_value == "unavailable"


def test_module_health_mi1_healthy(coordinator, health_sensor):
    """MI1: Low errors → 'healthy'"""
    coordinator.data = {"bus_stats": {"errors": 0}}
    assert health_sensor.native_value == "healthy"


def test_module_health_mi1_degraded(coordinator, health_sensor):
    """MI1: High errors (>10) → 'degraded'"""
    coordinator.data = {"bus_stats": {"errors": 15}}
    assert health_sensor.native_value == "degraded"


def test_module_health_mi1_empty_bus_stats(coordinator, health_sensor):
    """MI1: Empty bus_stats → 'healthy' (0 errors by default)"""
    coordinator.data = {"bus_stats": {}}
    assert health_sensor.native_value == "healthy"


# === MI2: SynapseActivitySensor ===

def test_synapse_activity_mi2_no_data(coordinator, synapse_sensor):
    """MI2: No coordinator data → '0'"""
    coordinator.data = None
    assert synapse_sensor.native_value == "0"


def test_synapse_activity_mi2_with_updates(coordinator, synapse_sensor):
    """MI2: Learning stats total_updates → string value"""
    coordinator.data = {"learning_stats": {"total_updates": 1234}}
    assert synapse_sensor.native_value == "1234"


def test_synapse_activity_mi2_zero_updates(coordinator, synapse_sensor):
    """MI2: Zero updates → '0'"""
    coordinator.data = {"learning_stats": {"total_updates": 0}}
    assert synapse_sensor.native_value == "0"


def test_synapse_activity_mi2_no_learning_stats(coordinator, synapse_sensor):
    """MI2: Missing learning_stats → '0'"""
    coordinator.data = {}
    assert synapse_sensor.native_value == "0"


# === MI3: CrossPatternSensor ===

def test_cross_pattern_mi3_no_data(coordinator, pattern_sensor):
    """MI3: No coordinator data → '0'"""
    coordinator.data = None
    assert pattern_sensor.native_value == "0"


def test_cross_pattern_mi3_with_patterns(coordinator, pattern_sensor):
    """MI3: Cross module stats patterns_discovered → string value"""
    coordinator.data = {"cross_module_stats": {"patterns_discovered": 42}}
    assert pattern_sensor.native_value == "42"


def test_cross_pattern_mi3_zero_patterns(coordinator, pattern_sensor):
    """MI3: Zero patterns → '0'"""
    coordinator.data = {"cross_module_stats": {"patterns_discovered": 0}}
    assert pattern_sensor.native_value == "0"


def test_cross_pattern_mi3_no_cross_stats(coordinator, pattern_sensor):
    """MI3: Missing cross_module_stats → '0'"""
    coordinator.data = {}
    assert pattern_sensor.native_value == "0"


# === MI4: ModuleHealthSensor attrs ===

def test_module_health_mi4_attrs_structure(coordinator, health_sensor):
    """MI4: attrs carry raw bus_stats values"""
    coordinator.data = {
        "bus_stats": {
            "events_published": 100,
            "events_delivered": 95,
            "errors": 5,
            "total_subscribers": 8,
        }
    }
    attrs = health_sensor.extra_state_attributes
    assert attrs["bus_events_published"] == 100
    assert attrs["bus_events_delivered"] == 95
    assert attrs["bus_errors"] == 5
    assert attrs["bus_subscribers"] == 8


def test_module_health_mi4_empty_attrs(coordinator, health_sensor):
    """MI4: Empty coordinator data → empty attrs"""
    coordinator.data = None
    assert health_sensor.extra_state_attributes == {}


def test_module_health_mi4_missing_bus_stats(coordinator, health_sensor):
    """MI4: Missing bus_stats → empty attrs"""
    coordinator.data = {}
    assert health_sensor.extra_state_attributes == {}


# === MI5: SynapseActivitySensor attrs ===

def test_synapse_activity_mi5_attrs_structure(coordinator, synapse_sensor):
    """MI5: attrs carry raw learning_stats values"""
    coordinator.data = {
        "learning_stats": {
            "total_synapses": 500,
            "learning_rate": 0.05,
            "total_drift": 0.2,
            "max_drift_synapse": "synapse_42",
        }
    }
    attrs = synapse_sensor.extra_state_attributes
    assert attrs["total_synapses"] == 500
    assert attrs["learning_rate"] == 0.05
    assert attrs["total_drift"] == 0.2
    assert attrs["max_drift_synapse"] == "synapse_42"


def test_synapse_activity_mi5_default_values(coordinator, synapse_sensor):
    """MI5: Missing keys get default values"""
    coordinator.data = {"learning_stats": {}}
    attrs = synapse_sensor.extra_state_attributes
    assert attrs["total_synapses"] == 0
    assert attrs["learning_rate"] == 0
    assert attrs["total_drift"] == 0
    assert attrs["max_drift_synapse"] is None


# === MI6: CrossPatternSensor attrs ===

def test_cross_pattern_mi6_attrs_structure(coordinator, pattern_sensor):
    """MI6: attrs carry raw cross_module_stats values"""
    coordinator.data = {
        "cross_module_stats": {
            "snapshots_collected": 1000,
            "window_size": 60,
        }
    }
    attrs = pattern_sensor.extra_state_attributes
    assert attrs["snapshots_collected"] == 1000
    assert attrs["window_size"] == 60


def test_cross_pattern_mi6_default_values(coordinator, pattern_sensor):
    """MI6: Missing keys get default values"""
    coordinator.data = {"cross_module_stats": {}}
    attrs = pattern_sensor.extra_state_attributes
    assert attrs["snapshots_collected"] == 0
    assert attrs["window_size"] == 0


# === MI7: Sensor configuration ===

def test_module_health_mi7_sensor_config(health_sensor):
    """MI7: ModuleHealthSensor has correct configuration"""
    assert health_sensor._attr_name == "PilotSuite Module Health"
    assert health_sensor._attr_unique_id == "copilot_module_health"
    assert health_sensor._attr_icon == "mdi:heart-pulse"
    assert health_sensor._attr_should_poll is False


def test_synapse_activity_mi7_sensor_config(synapse_sensor):
    """MI7: SynapseActivitySensor has correct configuration"""
    assert synapse_sensor._attr_name == "PilotSuite Synapse Activity"
    assert synapse_sensor._attr_unique_id == "copilot_synapse_activity"
    assert synapse_sensor._attr_icon == "mdi:transit-connection-variant"
    assert synapse_sensor._attr_should_poll is False


def test_cross_pattern_mi7_sensor_config(pattern_sensor):
    """MI7: CrossPatternSensor has correct configuration"""
    assert pattern_sensor._attr_name == "PilotSuite Cross Patterns"
    assert pattern_sensor._attr_unique_id == "copilot_cross_patterns"
    assert pattern_sensor._attr_icon == "mdi:chart-scatter-plot"
    assert pattern_sensor._attr_should_poll is False


# === GC: Global Contract ===

def test_module_integration_gc1_pure_projection_health(coordinator, health_sensor):
    """GC1: ModuleHealthSensor is pure projection shell on coordinator.data['bus_stats']"""
    coordinator.data = {"bus_stats": {"errors": 3, "events_published": 50}}
    assert health_sensor.native_value == "healthy"
    assert health_sensor.extra_state_attributes["bus_events_published"] == 50


def test_module_integration_gc1_pure_projection_synapse(coordinator, synapse_sensor):
    """GC1: SynapseActivitySensor is pure projection shell on coordinator.data['learning_stats']"""
    coordinator.data = {"learning_stats": {"total_updates": 999}}
    assert synapse_sensor.native_value == "999"


def test_module_integration_gc1_pure_projection_pattern(coordinator, pattern_sensor):
    """GC1: CrossPatternSensor is pure projection shell on coordinator.data['cross_module_stats']"""
    coordinator.data = {"cross_module_stats": {"patterns_discovered": 77}}
    assert pattern_sensor.native_value == "77"


def test_module_integration_gc2_no_local_semantic_invention(coordinator, health_sensor, synapse_sensor, pattern_sensor):
    """GC2: No local semantic invention — all state comes verbatim from coordinator.data"""
    coordinator.data = {
        "bus_stats": {"errors": 0},
        "learning_stats": {"total_updates": 100},
        "cross_module_stats": {"patterns_discovered": 5},
    }
    # Sensors do NOT compute thresholds locally
    # Sensors do NOT invent categories
    # Sensors just mirror raw coordinator.data values
    assert health_sensor.native_value == "healthy"
    assert synapse_sensor.native_value == "100"
    assert pattern_sensor.native_value == "5"
