"""Projection Contract Tests for Light Intelligence + Weather Optimizer Sensors (HA-22).

Verifies that these HA sensors are pure projection shells on Core API truth:
- LightIntelligenceSensor → /api/v1/hub/light
- WeatherOptimizerSensor → /api/v1/predict/weather-optimize

No local semantic invention — only trivial projection/display logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============== LightIntelligenceSensor Tests ==============

class TestLightIntelligenceSensorProjection:
    """LI1-LI5: LightIntelligenceSensor projects /api/v1/hub/light without local semantics."""

    @pytest.fixture
    def coordinator(self):
        coord = MagicMock()
        coord.data = {}
        return coord

    @pytest.fixture
    def sensor(self, coordinator):
        from custom_components.copilot_ha.sensors.light_intelligence_sensor import LightIntelligenceSensor
        return LightIntelligenceSensor(coordinator)

    def test_LI1_state_shows_suggested_scene_name_when_present(self, sensor):
        """LI1: state returns suggested_scene_name from Core API response."""
        sensor._light_data = {"suggested_scene_name": "Abendmodus"}
        assert sensor.state == "Abendmodus"

    def test_LI2_state_falls_back_to_sun_phase_mapping(self, sensor):
        """LI2: state maps sun.phase through trivial German mapping."""
        sensor._light_data = {"sun": {"phase": "dusk"}}
        assert sensor.state == "Abenddämmerung"

    def test_LI3_icon_maps_sun_phase_trivially(self, sensor):
        """LI3: icon is trivial phase→icon lookup, no semantic invention."""
        sensor._light_data = {"sun": {"phase": "night"}}
        assert sensor.icon == "mdi:weather-night"

    def test_LI4_extra_attrs_project_sun_elevation_azimuth_lux(self, sensor):
        """LI4: extra_state_attributes projects sun + lux data without transformation."""
        sensor._light_data = {
            "sun": {"elevation": 45.2, "azimuth": 180.5, "phase": "day"},
            "global_outdoor_lux": 12000,
        }
        attrs = sensor.extra_state_attributes
        assert attrs["sun_elevation"] == 45.2
        assert attrs["sun_azimuth"] == 180.5
        assert attrs["outdoor_lux"] == 12000

    def test_LI5_extra_attrs_project_zones_without_local_logic(self, sensor):
        """LI5: zone_count and zones_needing_light are direct projections."""
        sensor._light_data = {
            "zones": [
                {"needs_light": True},
                {"needs_light": False},
                {"needs_light": True},
            ]
        }
        attrs = sensor.extra_state_attributes
        assert attrs["zone_count"] == 3
        assert attrs["zones_needing_light"] == 2


# ============== WeatherOptimizerSensor Tests ==============

class TestWeatherOptimizerSensorProjection:
    """WO1-WO5: WeatherOptimizerSensor projects /api/v1/predict/weather-optimize without local semantics."""

    @pytest.fixture
    def coordinator(self):
        coord = MagicMock()
        coord.data = {}
        return coord

    @pytest.fixture
    def sensor(self, coordinator):
        from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor
        return WeatherOptimizerSensor(coordinator)

    def test_WO1_native_value_shows_optimal_windows_count(self, sensor):
        """WO1: native_value is direct projection of optimal_windows_count."""
        sensor._data = {"optimal_windows_count": 5}
        assert sensor.native_value == 5

    def test_WO2_native_value_defaults_to_zero_when_missing(self, sensor):
        """WO2: native_value defaults to 0 when data missing."""
        sensor._data = {}
        assert sensor.native_value == 0

    def test_WO3_extra_attrs_project_pv_kwh_and_price(self, sensor):
        """WO3: extra_state_attributes projects summary PV/price data."""
        sensor._data = {
            "summary": {
                "total_pv_kwh": 12.5,
                "avg_price_eur_kwh": 0.28,
                "optimal_windows_count": 4,
            }
        }
        attrs = sensor.extra_state_attributes
        assert attrs["total_pv_kwh"] == 12.5
        assert attrs["avg_price_eur_kwh"] == 0.28

    def test_WO4_extra_attrs_project_best_worst_hours_lists(self, sensor):
        """WO4: best_hours and worst_hours are projected as-is."""
        sensor._data = {
            "summary": {
                "best_hours": ["11:00", "12:00", "13:00"],
                "worst_hours": ["19:00", "20:00"],
            }
        }
        attrs = sensor.extra_state_attributes
        assert attrs["best_hours"] == ["11:00", "12:00", "13:00"]
        assert attrs["worst_hours"] == ["19:00", "20:00"]

    def test_WO5_extra_attrs_project_pv_self_consumption_and_alerts(self, sensor):
        """WO5: pv_self_consumption_potential_pct and alerts are direct projections."""
        sensor._data = {
            "summary": {"pv_self_consumption_potential_pct": 78},
            "alerts": ["high_wind_warning"],
            "battery_plan_count": 3,
        }
        attrs = sensor.extra_state_attributes
        assert attrs["pv_self_consumption_pct"] == 78
        assert attrs["alerts"] == ["high_wind_warning"]
        assert attrs["battery_actions"] == 3


# ============== Global Contract Test ==============

class TestHA22GlobalProjectionContract:
    """HA-22 Contract: Both sensors are pure projection shells, no local semantic invention."""

    def test_both_sensors_hit_core_api_endpoints_only(self):
        """Contract: Both sensors fetch from Core API, no local computation."""
        from custom_components.copilot_ha.sensors.light_intelligence_sensor import LightIntelligenceSensor
        from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor

        # Verify async_update methods exist and reference Core endpoints
        import inspect
        light_source = inspect.getsource(LightIntelligenceSensor.async_update)
        weather_source = inspect.getsource(WeatherOptimizerSensor.async_update)

        assert "/api/v1/hub/light" in light_source
        assert "/api/v1/predict/weather-optimize" in weather_source

    def test_no_local_semantic_invention_in_state_logic(self):
        """Contract: State logic is trivial projection/mapping only."""
        from custom_components.copilot_ha.sensors.light_intelligence_sensor import LightIntelligenceSensor
        from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor

        import inspect
        light_state_source = inspect.getsource(LightIntelligenceSensor.state.fget)
        weather_value_source = inspect.getsource(WeatherOptimizerSensor.native_value.fget)

        # Light state: only dict.get() and phase_map lookup
        assert "phase_map.get" in light_state_source or "suggested" in light_state_source
        # Weather value: only dict.get() with default
        assert ".get(" in weather_value_source
