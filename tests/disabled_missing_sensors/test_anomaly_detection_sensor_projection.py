"""
Projection Contract Tests: anomaly_detection_sensor
===================================================
Contract: AnomalyDetectionSensor ist reine Projection-Shell auf /api/v1/hub/anomalies
— triviale Stringformatierung (f"{N} kritisch"/f"{N} Anomalien"/"Normal"),
  icon-Map (critical/warning), Dict-Lookups, keine lokale Semantik.

HC-1 HC-2         — native_value: Normal / Anomalien / kritisch
HC-3 HC-4 HC-5    — icon mapping: critical / warning / normal
HC-6 HC-7 HC-8    — attrs: full / minimal / top_anomalies capping
HC-9 HC-10 HC-11  — edge: missing keys / None data / empty anomaly_types
GC1                — pure projection (hits /api/v1/hub/anomalies)
GC2                — no local semantic invention
"""

import pytest
from pathlib import Path

# Import the sensor file directly to inspect its structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from custom_components.copilot_ha.sensors.anomaly_detection_sensor import (
    AnomalyDetectionSensor,
)


# ---------------------------------------------------------------------------
# Contract Mirror — mirrors the sensor's runtime data shape exactly
# ---------------------------------------------------------------------------
class AnomalyDetectionSensorContract:
    """Reflects the runtime data shape AnomalyDetectionSensor reads from coordinator.data."""

    def __init__(self, total_entities=0, total_anomalies=0, critical=0, warning=0,
                 info=0, anomaly_types=None, top_anomalies=None):
        self.total_entities = total_entities
        self.total_anomalies = total_anomalies
        self.critical = critical
        self.warning = warning
        self.info = info
        self.anomaly_types = anomaly_types or {}
        self.top_anomalies = top_anomalies or []


# ---------------------------------------------------------------------------
# Helper: build a sensor instance with contract data
# NOTE: The sensor's async_update() does self._anomaly_data = await self._fetch(...)
# So _anomaly_data = the raw response dict from /api/v1/hub/anomalies.
# We simulate that by setting _anomaly_data directly.
# ---------------------------------------------------------------------------
def make_sensor(contract_data: AnomalyDetectionSensorContract | None):
    """Return AnomalyDetectionSensor with _anomaly_data set as if async_update ran."""

    class FakeCoordinator:
        pass

    coordinator = FakeCoordinator()
    sensor = AnomalyDetectionSensor.__new__(AnomalyDetectionSensor)
    sensor._coordinator = coordinator

    if contract_data is not None:
        sensor._anomaly_data = {
            "total_entities": contract_data.total_entities,
            "total_anomalies": contract_data.total_anomalies,
            "critical": contract_data.critical,
            "warning": contract_data.warning,
            "info": contract_data.info,
            "anomaly_types": contract_data.anomaly_types,
            "top_anomalies": contract_data.top_anomalies,
        }
    else:
        sensor._anomaly_data = {}

    return sensor


# ---------------------------------------------------------------------------
# Test Cases: native_value (state)
# ---------------------------------------------------------------------------
class TestAnomalyDetectionNativeValue:
    """HC-1 HC-2: state = 'Normal' / 'N Anomalien' / 'N kritisch'."""

    def test_hc1_normal(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=0, critical=0, warning=0, info=0,
            anomaly_types={}, top_anomalies=[],
        ))
        assert sensor.state == "Normal"

    def test_hc2_warnings_only(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=5, critical=0, warning=3, info=2,
            anomaly_types={"temperature": 2, "humidity": 3},
            top_anomalies=[{"entity": "e1", "type": "temperature"}],
        ))
        # warning > 0, critical == 0, total > 0 → "5 Anomalien"
        assert sensor.state == "5 Anomalien"

    def test_hc2b_anomalies_no_critical(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=3, critical=0, warning=3, info=0,
            anomaly_types={}, top_anomalies=[],
        ))
        assert sensor.state == "3 Anomalien"

    def test_hc3_critical(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=7, critical=2, warning=3, info=2,
            anomaly_types={"temperature": 4, "brightness": 3},
            top_anomalies=[{"entity": "e1"}, {"entity": "e2"}],
        ))
        # critical > 0 → "2 kritisch"
        assert sensor.state == "2 kritisch"

    def test_hc3b_multiple_critical(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=8, critical=5, warning=2, info=1,
            anomaly_types={}, top_anomalies=[],
        ))
        assert sensor.state == "5 kritisch"

    def test_hc4_zero_entities_but_anomaly(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=0, total_anomalies=1, critical=0, warning=1, info=0,
            anomaly_types={}, top_anomalies=[],
        ))
        assert sensor.state == "1 Anomalien"


# ---------------------------------------------------------------------------
# Test Cases: icon
# ---------------------------------------------------------------------------
class TestAnomalyDetectionIcon:
    """HC-3 HC-4 HC-5: icon mapping based on critical / warning."""

    def test_hc5_icon_critical(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=3, critical=2, warning=1, info=0,
        ))
        assert sensor.icon == "mdi:alert-octagon"

    def test_hc5b_icon_critical_zero_warning(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=2, critical=2, warning=0, info=0,
        ))
        assert sensor.icon == "mdi:alert-octagon"

    def test_hc6_icon_warning_no_critical(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=3, critical=0, warning=3, info=0,
        ))
        assert sensor.icon == "mdi:alert"

    def test_hc6b_icon_warning_only(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=1, critical=0, warning=1, info=0,
        ))
        assert sensor.icon == "mdi:alert"

    def test_hc7_icon_normal(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=0, critical=0, warning=0, info=0,
        ))
        assert sensor.icon == "mdi:check-decagram"

    def test_hc7b_icon_normal_with_anomalies_but_no_critical_or_warning(self):
        # Edge: anomalies exist but none critical/warning → icon = normal
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10, total_anomalies=2, critical=0, warning=0, info=2,
        ))
        assert sensor.icon == "mdi:check-decagram"


# ---------------------------------------------------------------------------
# Test Cases: extra_state_attributes
# ---------------------------------------------------------------------------
class TestAnomalyDetectionAttrs:
    """HC-6 HC-7 HC-8: attrs = total_entities / anomaly_types / top_anomalies."""

    def test_hc8_attrs_full(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10,
            total_anomalies=7,
            critical=2,
            warning=3,
            info=2,
            anomaly_types={"temperature": 4, "humidity": 2, "brightness": 1},
            top_anomalies=[
                {"entity": "sensor.temp_1", "type": "temperature", "value": 25.3},
                {"entity": "sensor.temp_2", "type": "temperature", "value": 26.1},
                {"entity": "sensor.hum_1", "type": "humidity", "value": 85.0},
            ],
        ))
        attrs = sensor.extra_state_attributes
        assert attrs["total_entities"] == 10
        assert attrs["total_anomalies"] == 7
        assert attrs["critical"] == 2
        assert attrs["warning"] == 3
        assert attrs["info"] == 2
        assert attrs["anomaly_types"] == {"temperature": 4, "humidity": 2, "brightness": 1}
        # top_anomalies capped at [:5]
        assert len(attrs["top_anomalies"]) == 3
        assert attrs["top_anomalies"][0]["entity"] == "sensor.temp_1"

    def test_hc9_attrs_top_anomalies_capped(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=10,
            total_anomalies=20,
            critical=5,
            warning=10,
            info=5,
            anomaly_types={},
            top_anomalies=[
                {"entity": f"e{i}", "type": "test", "value": i}
                for i in range(10)
            ],
        ))
        attrs = sensor.extra_state_attributes
        # sensor caps at [:5]
        assert len(attrs["top_anomalies"]) == 5

    def test_hc10_attrs_minimal(self):
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=0, total_anomalies=0, critical=0, warning=0, info=0,
            anomaly_types={}, top_anomalies=[],
        ))
        attrs = sensor.extra_state_attributes
        assert attrs["total_entities"] == 0
        assert attrs["total_anomalies"] == 0
        assert attrs["critical"] == 0
        assert attrs["warning"] == 0
        assert attrs["info"] == 0
        assert attrs["anomaly_types"] == {}
        assert attrs["top_anomalies"] == []


# ---------------------------------------------------------------------------
# Test Cases: edge cases
# ---------------------------------------------------------------------------
class TestAnomalyDetectionEdge:
    """HC-9 HC-10 HC-11: missing keys / None data / empty anomaly_types."""

    def test_hc11_missing_anomaly_detection_key(self):
        # No "anomaly_detection" key at all
        sensor = make_sensor(None)
        # _anomaly_data = {} → all .get() return 0/{} []
        assert sensor.state == "Normal"
        assert sensor.icon == "mdi:check-decagram"

    def test_hc12_empty_data(self):
        class FakeCoordinator:
            data = {"anomaly_detection": {}}
        sensor = AnomalyDetectionSensor.__new__(AnomalyDetectionSensor)
        sensor._coordinator = FakeCoordinator()
        sensor._anomaly_data = {}
        assert sensor.state == "Normal"
        assert sensor.icon == "mdi:check-decagram"

    def test_hc13_partial_keys(self):
        # Only critical present — _anomaly_data has critical=3 only, rest defaults
        class FakeCoordinator:
            pass
        sensor = AnomalyDetectionSensor.__new__(AnomalyDetectionSensor)
        sensor._coordinator = FakeCoordinator()
        sensor._anomaly_data = {"critical": 3}
        assert sensor.state == "3 kritisch"
        assert sensor.icon == "mdi:alert-octagon"


# ---------------------------------------------------------------------------
# Global Contract
# ---------------------------------------------------------------------------
class TestAnomalyDetectionGlobalContract:
    """GC1 GC2: pure projection / no local semantic invention."""

    def test_gc1_hits_core_api(self):
        # Sensor fetches from /api/v1/hub/anomalies (verified via source inspection)
        # The _fetch() method is inherited from CopilotBaseEntity and calls
        # self._core_base_url() + "/api/v1/hub/anomalies"
        import inspect
        source = inspect.getsource(AnomalyDetectionSensor.async_update)
        assert "/api/v1/hub/anomalies" in source

    def test_gc2_no_local_semantic_invention(self):
        # state: f"{critical} kritisch" / f"{total} Anomalien" / "Normal"
        # icon: static mdi map based on critical/warning counts
        # attrs: direct .get() passthrough + [:5] cap on top_anomalies
        # No classification, no scoring, no ML, no threshold computation
        # critical > 0 always wins over total_anomalies > 0
        sensor = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=3, critical=1, warning=1, info=1,
            anomaly_types={"temp": 3},
            top_anomalies=[{"entity": "e1"}],
        ))
        # critical > 0 → "1 kritisch" (critical wins over total > 0)
        assert sensor.state == "1 kritisch"
        sensor2 = make_sensor(AnomalyDetectionSensorContract(
            total_entities=5, total_anomalies=3, critical=2, warning=1, info=0,
            anomaly_types={}, top_anomalies=[],
        ))
        assert sensor2.state == "2 kritisch"  # critical overrides
        # critical > 0 → icon = mdi:alert-octagon (critical always wins in sensor)
        assert sensor.icon == "mdi:alert-octagon"  # critical > 0 wins
        assert sensor2.icon == "mdi:alert-octagon"  # critical > 0 wins
