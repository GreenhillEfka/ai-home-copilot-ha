"""Projection Contract Tests: weather_optimizer_sensor.py

Verifies: WeatherOptimizerSensor projects weather-aware optimization data
fetched from Core API. Uses _core_base_url() and _core_headers() —
requires FakeResp mock + patch.

Contract verified:
- state = optimal_windows_count
- attrs = processed summary and optimization plan data
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class FakeResp:
    """Fake aiohttp response for patching Core API calls."""
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status = status

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


# === Fixtures ===

@pytest.fixture
def coordinator():
    c = MagicMock()
    c.data = {}
    c._config = {"host": "localhost", "port": 8909, "token": "test_token"}
    return c


@pytest.fixture
def sensor(coordinator):
    from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor
    return WeatherOptimizerSensor(coordinator)


# === WO1: native_value ===

def test_weather_optimizer_wo1_no_data(sensor):
    """WO1: No data → 0"""
    assert sensor.native_value == 0


def test_weather_optimizer_wo1_with_windows(sensor):
    """WO1: With optimal windows → count"""
    sensor._data = {"optimal_windows_count": 5}
    assert sensor.native_value == 5


def test_weather_optimizer_wo1_zero_windows(sensor):
    """WO1: Zero windows → 0"""
    sensor._data = {"optimal_windows_count": 0}
    assert sensor.native_value == 0


# === WO2: extra_state_attributes ===

def test_weather_optimizer_wo2_attrs_structure(sensor):
    """WO2: attrs contain optimization summary"""
    sensor._data = {
        "summary": {
            "total_pv_kwh": 25.5,
            "avg_price_eur_kwh": 0.15,
            "best_hours": [10, 11, 12],
            "worst_hours": [18, 19, 20],
            "pv_self_consumption_potential_pct": 85,
        },
        "alerts": [{"type": "weather", "message": "Cloudy afternoon"}],
        "top_windows": [
            {"hour": 10, "savings": 0.5},
            {"hour": 11, "savings": 0.6},
            {"hour": 12, "savings": 0.55},
            {"hour": 13, "savings": 0.4},  # Should be truncated
        ],
        "battery_plan_count": 3,
        "horizon_hours": 48,
    }
    attrs = sensor.extra_state_attributes
    assert attrs["total_pv_kwh"] == 25.5
    assert attrs["avg_price_eur_kwh"] == 0.15
    assert attrs["best_hours"] == [10, 11, 12]
    assert attrs["worst_hours"] == [18, 19, 20]
    assert attrs["pv_self_consumption_pct"] == 85
    assert len(attrs["alerts"]) == 1
    assert len(attrs["top_windows"]) == 3  # Limited to 3
    assert attrs["battery_actions"] == 3
    assert attrs["horizon_hours"] == 48


def test_weather_optimizer_wo2_empty_summary(sensor):
    """WO2: Empty summary → default values in attrs"""
    sensor._data = {"summary": {}}
    attrs = sensor.extra_state_attributes
    assert attrs["total_pv_kwh"] == 0
    assert attrs["avg_price_eur_kwh"] == 0
    assert attrs["best_hours"] == []
    assert attrs["worst_hours"] == []
    assert attrs["pv_self_consumption_pct"] == 0


def test_weather_optimizer_wo2_no_data_attrs(sensor):
    """WO2: No data → empty attrs with defaults"""
    sensor._data = {}
    attrs = sensor.extra_state_attributes
    assert attrs["total_pv_kwh"] == 0
    assert attrs["best_hours"] == []
    assert attrs["top_windows"] == []
    assert attrs["battery_actions"] == 0
    assert attrs["horizon_hours"] == 0


# === WO3: async_update ===

@pytest.mark.asyncio
async def test_weather_optimizer_wo3_fetch_success(sensor):
    """WO3: async_update fetches optimization data from Core API"""
    response_data = {
        "ok": True,
        "summary": {
            "optimal_windows_count": 4,
            "total_pv_kwh": 30.0,
            "avg_price_eur_kwh": 0.12,
        },
        "alerts": [],
        "top_windows": [],
        "battery_plan_count": 2,
        "horizon_hours": 48,
    }
    with patch("aiohttp.ClientSession.get", return_value=FakeResp(response_data)):
        await sensor.async_update()
        assert sensor._data["optimal_windows_count"] == 4
        assert sensor._data["summary"]["total_pv_kwh"] == 30.0


@pytest.mark.asyncio
async def test_weather_optimizer_wo3_fetch_not_ok(sensor):
    """WO3: Response ok=False → data not updated"""
    response_data = {"ok": False}
    with patch("aiohttp.ClientSession.get", return_value=FakeResp(response_data)):
        await sensor.async_update()
        assert sensor._data == {}


@pytest.mark.asyncio
async def test_weather_optimizer_wo3_fetch_error_status(sensor):
    """WO3: Non-200 status → data not updated"""
    with patch("aiohttp.ClientSession.get", return_value=FakeResp({}, status=500)):
        await sensor.async_update()
        assert sensor._data == {}


@pytest.mark.asyncio
async def test_weather_optimizer_wo3_fetch_exception(sensor):
    """WO3: Exception during fetch → data not updated"""
    with patch("aiohttp.ClientSession.get", side_effect=Exception("Connection error")):
        await sensor.async_update()
        assert sensor._data == {}


# === WO4: Sensor configuration ===

def test_weather_optimizer_wo4_sensor_config(sensor):
    """WO4: WeatherOptimizerSensor has correct configuration"""
    assert sensor._attr_name == "Weather Optimizer"
    assert sensor._attr_unique_id == "copilot_weather_optimizer"
    assert sensor._attr_icon == "mdi:weather-sunny-alert"
    assert sensor._attr_native_unit_of_measurement == "windows"


# === GC: Global Contract ===

def test_weather_optimizer_gc1_projection_from_api_data(sensor):
    """GC1: Sensor state derived from API response projection"""
    sensor._data = {
        "optimal_windows_count": 6,
        "summary": {
            "total_pv_kwh": 45.0,
            "avg_price_eur_kwh": 0.10,
            "best_hours": [9, 10, 11, 12],
            "worst_hours": [17, 18],
            "pv_self_consumption_potential_pct": 90,
        },
        "alerts": [{"type": "price", "message": "Low price period"}],
        "top_windows": [{"hour": 10, "savings": 0.8}],
        "battery_plan_count": 4,
        "horizon_hours": 48,
    }
    assert sensor.native_value == 6
    attrs = sensor.extra_state_attributes
    assert attrs["total_pv_kwh"] == 45.0
    assert attrs["best_hours"] == [9, 10, 11, 12]
    assert attrs["pv_self_consumption_pct"] == 90


def test_weather_optimizer_gc2_window_limiting(sensor):
    """GC2: Top windows limited to 3 in attrs"""
    sensor._data = {
        "summary": {},
        "top_windows": [
            {"hour": i, "savings": i * 0.1}
            for i in range(10)
        ],
    }
    attrs = sensor.extra_state_attributes
    assert len(attrs["top_windows"]) == 3
