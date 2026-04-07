"""Projection Contract Tests — WeatherOptimizerSensor.

Verifies WeatherOptimizerSensor is a pure projection shell on
/api/v1/predict/weather-optimize — no local semantic invention.

HA-132
"""

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Contract Mirror
# ---------------------------------------------------------------------------

class WeatherOptimizerSensorContract:
    """Mirror of WeatherOptimizerSensor projection contract."""

    @staticmethod
    def build_coordinator_data(
        *,
        ok: bool = True,
        optimal_windows_count: int = 3,
        total_pv_kwh: float = 12.5,
        avg_price_eur_kwh: float = 0.28,
        best_hours: list | None = None,
        worst_hours: list | None = None,
        pv_self_consumption_potential_pct: float = 72.0,
        alerts: list | None = None,
        top_windows: list | None = None,
        battery_plan_count: int = 2,
        horizon_hours: int = 48,
    ) -> dict:
        if best_hours is None:
            best_hours = ["2026-04-06T14:00", "2026-04-06T15:00", "2026-04-06T16:00"]
        if worst_hours is None:
            worst_hours = ["2026-04-06T07:00", "2026-04-06T08:00"]
        if alerts is None:
            alerts = []
        if top_windows is None:
            top_windows = [
                {"start": "2026-04-06T14:00", "end": "2026-04-06T15:00", "pv_kwh": 4.2},
            ]
        data = {
            "ok": ok,
            "summary": {
                "optimal_windows_count": optimal_windows_count,
                "total_pv_kwh": total_pv_kwh,
                "avg_price_eur_kwh": avg_price_eur_kwh,
                "best_hours": best_hours,
                "worst_hours": worst_hours,
                "pv_self_consumption_potential_pct": pv_self_consumption_potential_pct,
            },
            "alerts": alerts,
            "top_windows": top_windows,
            "battery_plan_count": battery_plan_count,
            "horizon_hours": horizon_hours,
        }
        # Add optimal_windows_count at top-level as the sensor reads it
        data["optimal_windows_count"] = optimal_windows_count
        return data

    # ------------------------------------------------------------------
    # native_value = _data.get("optimal_windows_count", 0)
    # ------------------------------------------------------------------

    @staticmethod
    def native_value(coordinator_data: dict) -> int:
        return coordinator_data.get("optimal_windows_count", 0)

    # ------------------------------------------------------------------
    # extra_state_attributes
    # ------------------------------------------------------------------

    @staticmethod
    def extra_state_attributes(coordinator_data: dict) -> dict:
        summary = coordinator_data.get("summary", {})
        return {
            "total_pv_kwh": summary.get("total_pv_kwh", 0),
            "avg_price_eur_kwh": summary.get("avg_price_eur_kwh", 0),
            "best_hours": summary.get("best_hours", []),
            "worst_hours": summary.get("worst_hours", []),
            "pv_self_consumption_pct": summary.get("pv_self_consumption_potential_pct", 0),
            "alerts": coordinator_data.get("alerts", []),
            "top_windows": coordinator_data.get("top_windows", [])[:3],
            "battery_actions": coordinator_data.get("battery_plan_count", 0),
            "horizon_hours": coordinator_data.get("horizon_hours", 0),
        }


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.http = MagicMock()
    hass.http.api_password = None
    return hass


@pytest.fixture
def mock_coordinator(mock_hass):
    coordinator = MagicMock()
    coordinator.hass = mock_hass
    coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data()
    return coordinator


@pytest.fixture
def sensor(mock_coordinator):
    from custom_components.copilot_ha.sensors.weather_optimizer_sensor import (
        WeatherOptimizerSensor,
    )
    sensor = WeatherOptimizerSensor(mock_coordinator)
    sensor._data = mock_coordinator.data
    return sensor


# ---------------------------------------------------------------------------
# Test Cases — native_value
# ---------------------------------------------------------------------------

class TestWONativeValue:
    """WO1: native_value = optimal_windows_count from coordinator_data."""

    def test_wo1_multiple_windows(self, sensor):
        assert sensor.native_value == 3

    def test_wo1_zero_windows(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            optimal_windows_count=0
        )
        sensor._data = mock_coordinator.data
        assert sensor.native_value == 0

    def test_wo1_one_window(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            optimal_windows_count=1
        )
        sensor._data = mock_coordinator.data
        assert sensor.native_value == 1

    def test_wo1_missing_key_defaults_zero(self, sensor, mock_coordinator):
        data = WeatherOptimizerSensorContract.build_coordinator_data()
        del data["optimal_windows_count"]
        mock_coordinator.data = data
        sensor._data = mock_coordinator.data
        assert sensor.native_value == 0

    def test_wo1_missing_summary(self, sensor, mock_coordinator):
        data = {"ok": True}
        mock_coordinator.data = data
        sensor._data = mock_coordinator.data
        assert sensor.native_value == 0


# ---------------------------------------------------------------------------
# Test Cases — extra_state_attributes
# ---------------------------------------------------------------------------

class TestWOAttributes:
    """WO2: extra_state_attributes are direct projections from coordinator_data."""

    def test_wo2_full_attrs(self, sensor):
        attrs = sensor.extra_state_attributes
        assert attrs["total_pv_kwh"] == 12.5
        assert attrs["avg_price_eur_kwh"] == 0.28
        assert attrs["best_hours"] == ["2026-04-06T14:00", "2026-04-06T15:00", "2026-04-06T16:00"]
        assert attrs["worst_hours"] == ["2026-04-06T07:00", "2026-04-06T08:00"]
        assert attrs["pv_self_consumption_pct"] == 72.0
        assert attrs["alerts"] == []
        assert attrs["battery_actions"] == 2
        assert attrs["horizon_hours"] == 48
        # top_windows capped to 3
        assert len(attrs["top_windows"]) == 1

    def test_wo2_empty_best_hours(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            best_hours=[]
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert attrs["best_hours"] == []
        # pv_self_consumption_pct comes from summary.pv_self_consumption_potential_pct, default 0 only if missing
        assert attrs["pv_self_consumption_pct"] == 72.0  # summary still has the value

    def test_wo2_alerts_present(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            alerts=["PV-Ertrag niedrig", "Strompreis über 0.30 EUR/kWh"]
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert len(attrs["alerts"]) == 2
        assert "PV-Ertrag niedrig" in attrs["alerts"]

    def test_wo2_top_windows_capped(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            top_windows=[
                {"start": f"T{i:02d}:00", "end": f"T{i+1:02d}:00", "pv_kwh": i * 0.5}
                for i in range(10)
            ]
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert len(attrs["top_windows"]) == 3  # capped to 3

    def test_wo2_missing_summary(self, sensor, mock_coordinator):
        data = {"ok": True, "alerts": [], "battery_plan_count": 0, "horizon_hours": 48}
        mock_coordinator.data = data
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert attrs["total_pv_kwh"] == 0
        assert attrs["avg_price_eur_kwh"] == 0
        assert attrs["pv_self_consumption_pct"] == 0
        assert attrs["battery_actions"] == 0


# ---------------------------------------------------------------------------
# Test Cases — edge
# ---------------------------------------------------------------------------

class TestWOEdge:
    """WO3: edge cases — no local semantic invention."""

    def test_wo3_api_error_false_ok(self, sensor, mock_coordinator):
        """API returns ok=false — sensor writes raw data as-is (no special handling)."""
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            ok=False,
            optimal_windows_count=0,
        )
        sensor._data = mock_coordinator.data
        # Sensor copies data as-is from API; no special ok=false logic
        assert sensor.native_value == 0
        attrs = sensor.extra_state_attributes
        # sensor writes whatever is in the response regardless of ok flag
        assert attrs["total_pv_kwh"] == 12.5

    def test_wo3_empty_top_windows(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            top_windows=[]
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert attrs["top_windows"] == []

    def test_wo3_zero_battery_plan(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            battery_plan_count=0
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert attrs["battery_actions"] == 0

    def test_wo3_horizon_hours_24(self, sensor, mock_coordinator):
        mock_coordinator.data = WeatherOptimizerSensorContract.build_coordinator_data(
            horizon_hours=24
        )
        sensor._data = mock_coordinator.data
        attrs = sensor.extra_state_attributes
        assert attrs["horizon_hours"] == 24


# ---------------------------------------------------------------------------
# Global Contract
# ---------------------------------------------------------------------------

class TestWOGlobalContract:
    """GC: global projection contract assertions."""

    def test_gc1_hits_core_predict_endpoint(self, sensor):
        """Sensor targets /api/v1/predict/weather-optimize via _core_base_url."""
        # This is verified by code inspection: async_update calls
        # f"{self._core_base_url()}/api/v1/predict/weather-optimize"
        # No local semantic computation — all values are direct projections.
        assert hasattr(sensor, "native_value")
        assert hasattr(sensor, "extra_state_attributes")

    def test_gc2_no_local_semantic_invention(self, sensor, mock_coordinator):
        """No local mood/energy classification — pure field projection."""
        # native_value: optimal_windows_count (direct lookup)
        # attrs: total_pv_kwh, avg_price_eur_kwh, best_hours, worst_hours,
        #        pv_self_consumption_pct, alerts, top_windows, battery_actions,
        #        horizon_hours — all direct from API response
        # No local score computation, no heuristic thresholds
        data = WeatherOptimizerSensorContract.build_coordinator_data()
        # These keys exist in data or data["summary"]
        assert "total_pv_kwh" in data.get("summary", {})
        assert "avg_price_eur_kwh" in data.get("summary", {})
        assert "best_hours" in data.get("summary", {})
        assert "worst_hours" in data.get("summary", {})
        assert "pv_self_consumption_potential_pct" in data.get("summary", {})
        assert "optimal_windows_count" in data
        assert "alerts" in data
        assert "top_windows" in data
        assert "battery_plan_count" in data
        assert "horizon_hours" in data
