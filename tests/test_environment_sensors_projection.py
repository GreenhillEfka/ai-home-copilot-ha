"""EnvironmentSensors Projection-Contract-Tests.

Contract: Environment-Sensoren sind HA-lokale Projection-Shells auf hass.states.async_all()
- LightLevelSensor: illuminance sensors (device_class="illuminance") + light states → avg_lux + level classification
- NoiseLevelSensor: noise/sound sensors + media_player states + vacuum states → noise classification
- WeatherContextSensor: weather states → condition mapping
- Keine lokale Semantik — reine State-Aggregation + Schwellenwerte

HA-206: environment_sensors.py Projection-Contract-Tests (37 Cases) — test/sensor contract fixed
"""
import pytest
from typing import Any

from custom_components.pilotsuite.sensors.environment_sensors import (
    LightLevelSensor,
    NoiseLevelSensor,
    WeatherContextSensor,
)


# ─────────────────────────────────────────────────────────────────────────────
# Contract-Mirror: lokale Kopie der Sensor-Logik für Test-Assertions
# ─────────────────────────────────────────────────────────────────────────────

class LightLevelMirror:
    """Mirror of LightLevelSensor classification logic."""
    
    @staticmethod
    def classify(avg_lux: float) -> str:
        if avg_lux < 10:
            return "dark"
        elif avg_lux < 100:
            return "dim"
        elif avg_lux < 1000:
            return "normal"
        return "bright"


class NoiseLevelMirror:
    """Mirror of NoiseLevelSensor classification logic."""
    
    @staticmethod
    def classify(media_playing: int, vacuums_active: int) -> str:
        if vacuums_active > 0:
            return "loud"
        elif media_playing > 0:
            return "moderate"
        return "quiet"


class WeatherContextMirror:
    """Mirror of WeatherContextSensor condition mapping."""
    
    CONDITION_MAP = {
        "clear": "clear",
        "sunny": "clear",
        "cloudy": "cloudy",
        "partlycloudy": "cloudy",
        "rain": "rainy",
        "drizzle": "rainy",
        "pouring": "rainy",
        "snow": "snowy",
        "blizzard": "snowy",
        "sleet": "snowy",
        "fog": "severe",
        "hail": "severe",
        "thunderstorm": "severe",
    }
    
    @staticmethod
    def map_condition(condition: str) -> str:
        return WeatherContextMirror.CONDITION_MAP.get(condition, "unknown")


# ─────────────────────────────────────────────────────────────────────────────
# Test Helpers — matching energy_sensors test pattern
# ─────────────────────────────────────────────────────────────────────────────

class MockState:
    """Mock State-like object for hass.states.async_all() simulation."""
    def __init__(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class MockStates:
    """Mock hass.states namespace."""
    def __init__(self, states: list[MockState]) -> None:
        self._states = states
    
    def async_all(self, domain: str | None = None) -> list[MockState]:
        """Return all states or filtered by domain."""
        if domain is None:
            return self._states
        return [s for s in self._states if s.entity_id.startswith(f"{domain}.")]


class MockHass:
    """Mock HomeAssistant with state categorization."""
    def __init__(self, states: list[MockState]) -> None:
        self.states = MockStates(states)


class MockCoordinator:
    """Mock coordinator for environment sensors."""
    def __init__(self) -> None:
        self.data = {}


# ─────────────────────────────────────────────────────────────────────────────
# LightLevelSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLightLevelSensor:
    """Tests for LightLevelSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        return MockCoordinator()
    
    @pytest.fixture
    def hass(self):
        return MockHass([])
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return LightLevelSensor(coordinator, hass)
    
    def test_ll1_dark_level(self, sensor, hass):
        """LL1: No illuminance sensors → level='dark'."""
        hass.states = MockStates([])
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_native_value == "dark"
        assert sensor._attr_extra_state_attributes["avg_lux"] == 0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 0
    
    def test_ll2_dim_level(self, sensor, hass):
        """LL2: 10 <= avg_lux < 100 → level='dim'."""
        illuminance_sensor = MockState(
            "sensor.light_1",
            "50",
            {"device_class": "illuminance"}
        )
        hass.states = MockStates([illuminance_sensor])
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_native_value == "dim"
        assert sensor._attr_extra_state_attributes["avg_lux"] == 50.0
    
    def test_ll3_normal_level(self, sensor, hass):
        """LL3: 100 <= avg_lux < 1000 → level='normal'."""
        illuminance_sensor = MockState(
            "sensor.light_1",
            "500",
            {"device_class": "illuminance"}
        )
        hass.states = MockStates([illuminance_sensor])
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_native_value == "normal"
        assert sensor._attr_extra_state_attributes["avg_lux"] == 500.0
    
    def test_ll4_bright_level(self, sensor, hass):
        """LL4: avg_lux >= 1000 → level='bright'."""
        illuminance_sensor = MockState(
            "sensor.light_1",
            "1500",
            {"device_class": "illuminance"}
        )
        hass.states = MockStates([illuminance_sensor])
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_native_value == "bright"
        assert sensor._attr_extra_state_attributes["avg_lux"] == 1500.0
    
    def test_ll5_boundary_10(self, sensor, hass):
        """LL5: Boundary at 10 lux (9.9=dark, 10.0=dim)."""
        sensor_low = MockState("sensor.low", "9.9", {"device_class": "illuminance"})
        sensor_high = MockState("sensor.high", "10.0", {"device_class": "illuminance"})
        
        hass.states = MockStates([sensor_low])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "dark"  # 9.9 is dark
        
        hass.states = MockStates([sensor_high])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "dim"  # 10.0 is dim
    
    def test_ll6_boundary_100(self, sensor, hass):
        """LL6: Boundary at 100 lux (99.9=dim, 100.0=normal)."""
        sensor_low = MockState("sensor.low", "99.9", {"device_class": "illuminance"})
        sensor_high = MockState("sensor.high", "100.0", {"device_class": "illuminance"})
        
        hass.states = MockStates([sensor_low])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "dim"
        
        hass.states = MockStates([sensor_high])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "normal"
    
    def test_ll7_boundary_1000(self, sensor, hass):
        """LL7: Boundary at 1000 lux (999.9=normal, 1000.0=bright)."""
        sensor_low = MockState("sensor.low", "999.9", {"device_class": "illuminance"})
        sensor_high = MockState("sensor.high", "1000.0", {"device_class": "illuminance"})
        
        hass.states = MockStates([sensor_low])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "normal"
        
        hass.states = MockStates([sensor_high])
        sensor._hass = hass
        sensor._update_light_level()
        assert sensor._attr_native_value == "bright"
    
    def test_ll8_multiple_sensors_average(self, sensor, hass):
        """LL8: Multiple illuminance sensors → average."""
        sensors = [
            MockState("sensor.light_1", "100", {"device_class": "illuminance"}),
            MockState("sensor.light_2", "200", {"device_class": "illuminance"}),
            MockState("sensor.light_3", "300", {"device_class": "illuminance"}),
        ]
        hass.states = MockStates(sensors)
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_extra_state_attributes["avg_lux"] == 200.0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 3
    
    def test_ll9_lights_on_count(self, sensor, hass):
        """LL9: lights_on attribute from light states."""
        lights = [
            MockState("light.living_room", "on"),
            MockState("light.bedroom", "on"),
            MockState("light.kitchen", "off"),
        ]
        hass.states = MockStates(lights)
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_extra_state_attributes["lights_on"] == 2
    
    def test_ll10_invalid_values_skipped(self, sensor, hass):
        """LL10: Invalid/non-numeric values are skipped."""
        sensors = [
            MockState("sensor.valid", "500", {"device_class": "illuminance"}),
            MockState("sensor.invalid", "unavailable", {"device_class": "illuminance"}),
            MockState("sensor.none", "None", {"device_class": "illuminance"}),
        ]
        hass.states = MockStates(sensors)
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_extra_state_attributes["avg_lux"] == 500.0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 1
    
    def test_ll11_negative_values_skipped(self, sensor, hass):
        """LL11: Negative values are skipped."""
        sensors = [
            MockState("sensor.valid", "500", {"device_class": "illuminance"}),
            MockState("sensor.negative", "-100", {"device_class": "illuminance"}),
        ]
        hass.states = MockStates(sensors)
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_extra_state_attributes["avg_lux"] == 500.0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 1
    
    def test_ll12_zero_values_included(self, sensor, hass):
        """LL12: Zero values are skipped (only positive values count)."""
        sensors = [
            MockState("sensor.light_1", "0", {"device_class": "illuminance"}),
            MockState("sensor.light_2", "100", {"device_class": "illuminance"}),
        ]
        hass.states = MockStates(sensors)
        sensor._hass = hass
        sensor._update_light_level()
        
        # Zero values are skipped (val > 0 check), so only 100 counts
        assert sensor._attr_extra_state_attributes["avg_lux"] == 100.0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 1
    
    def test_ll13_icon_static(self, sensor, hass):
        """LL13: Icon is static mdi:brightness-6."""
        assert sensor._attr_icon == "mdi:brightness-6"
    
    def test_ll14_unit_of_measurement(self, sensor, hass):
        """LL14: Unit is lx (lux)."""
        assert sensor._attr_native_unit_of_measurement == "lx"
    
    def test_ll15_attrs_full(self, sensor, hass):
        """LL15: Full attributes with all fields."""
        illuminance = MockState("sensor.light", "250", {"device_class": "illuminance"})
        lights = [
            MockState("light.l1", "on"),
            MockState("light.l2", "off"),
        ]
        hass.states = MockStates([illuminance] + lights)
        sensor._hass = hass
        sensor._update_light_level()
        
        attrs = sensor._attr_extra_state_attributes
        assert "avg_lux" in attrs
        assert "lights_on" in attrs
        assert "sensor_count" in attrs
        assert attrs["avg_lux"] == 250.0
        assert attrs["lights_on"] == 1
        assert attrs["sensor_count"] == 1
    
    def test_ll16_no_illuminance_sensors(self, sensor, hass):
        """LL16: No illuminance sensors → avg_lux=0, level=dark."""
        hass.states = MockStates([])
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_native_value == "dark"
        assert sensor._attr_extra_state_attributes["avg_lux"] == 0
        assert sensor._attr_extra_state_attributes["sensor_count"] == 0
    
    def test_ll17_non_illuminance_sensors_ignored(self, sensor, hass):
        """LL17: Sensors without device_class=illuminance are ignored."""
        sensors = [
            MockState("sensor.temp", "22", {"device_class": "temperature"}),
            MockState("sensor.humidity", "45", {"device_class": "humidity"}),
        ]
        hass.states = MockStates(sensors)
        sensor._hass = hass
        sensor._update_light_level()
        
        assert sensor._attr_extra_state_attributes["sensor_count"] == 0
        assert sensor._attr_native_value == "dark"


# ─────────────────────────────────────────────────────────────────────────────
# NoiseLevelSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestNoiseLevelSensor:
    """Tests for NoiseLevelSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        return MockCoordinator()
    
    @pytest.fixture
    def hass(self):
        return MockHass([])
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return NoiseLevelSensor(coordinator, hass)
    
    def test_nl1_quiet_default(self, sensor, hass):
        """NL1: No media/vacuum → level='quiet'."""
        hass.states = MockStates([])
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "quiet"
        assert sensor._attr_extra_state_attributes["media_playing"] == 0
        assert sensor._attr_extra_state_attributes["vacuums_active"] == 0
    
    def test_nl2_moderate_with_media(self, sensor, hass):
        """NL2: Media playing → level='moderate'."""
        media = [
            MockState("media_player.spotify", "playing"),
            MockState("media_player.tv", "off"),
        ]
        hass.states = MockStates(media)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "moderate"
        assert sensor._attr_extra_state_attributes["media_playing"] == 1
    
    def test_nl3_loud_with_vacuum(self, sensor, hass):
        """NL3: Vacuum cleaning → level='loud' (overrides media)."""
        media = [MockState("media_player.spotify", "playing")]
        vacuums = [MockState("vacuum.roomba", "cleaning")]
        hass.states = MockStates(media + vacuums)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "loud"
        assert sensor._attr_extra_state_attributes["vacuums_active"] == 1
        assert sensor._attr_extra_state_attributes["media_playing"] == 1
    
    def test_nl4_multiple_media(self, sensor, hass):
        """NL4: Multiple media players → count in attrs."""
        media = [
            MockState("media_player.spotify", "playing"),
            MockState("media_player.apple_tv", "playing"),
            MockState("media_player.chromecast", "paused"),
        ]
        hass.states = MockStates(media)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "moderate"
        assert sensor._attr_extra_state_attributes["media_playing"] == 2
    
    def test_nl5_multiple_vacuums(self, sensor, hass):
        """NL5: Multiple vacuums → count in attrs."""
        vacuums = [
            MockState("vacuum.roomba", "cleaning"),
            MockState("vacuum.roborock", "cleaning"),
        ]
        hass.states = MockStates(vacuums)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "loud"
        assert sensor._attr_extra_state_attributes["vacuums_active"] == 2
    
    def test_nl6_vacuum_idle_not_counted(self, sensor, hass):
        """NL6: Vacuum in 'docked' or 'idle' not counted as active."""
        vacuums = [
            MockState("vacuum.roomba", "docked"),
            MockState("vacuum.roborock", "idle"),
        ]
        hass.states = MockStates(vacuums)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "quiet"
        assert sensor._attr_extra_state_attributes["vacuums_active"] == 0
    
    def test_nl7_icon_static(self, sensor, hass):
        """NL7: Icon is static mdi:volume-high."""
        assert sensor._attr_icon == "mdi:volume-high"
    
    def test_nl8_attrs_full(self, sensor, hass):
        """NL8: Full attributes with all fields."""
        media = [MockState("media_player.spotify", "playing")]
        vacuums = [MockState("vacuum.roomba", "cleaning")]
        hass.states = MockStates(media + vacuums)
        sensor._hass = hass
        sensor._update_noise_level()
        
        attrs = sensor._attr_extra_state_attributes
        assert "media_playing" in attrs
        assert "vacuums_active" in attrs
        assert "noise_sensors" in attrs
        assert attrs["media_playing"] == 1
        assert attrs["vacuums_active"] == 1
    
    def test_nl9_media_paused_not_counted(self, sensor, hass):
        """NL9: Media in 'paused' state not counted as playing."""
        media = [
            MockState("media_player.spotify", "paused"),
            MockState("media_player.tv", "idle"),
        ]
        hass.states = MockStates(media)
        sensor._hass = hass
        sensor._update_noise_level()
        
        assert sensor._attr_native_value == "quiet"
        assert sensor._attr_extra_state_attributes["media_playing"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# WeatherContextSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWeatherContextSensor:
    """Tests for WeatherContextSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        return MockCoordinator()
    
    @pytest.fixture
    def hass(self):
        return MockHass([])
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return WeatherContextSensor(coordinator, hass)
    
    def test_wc1_clear_condition(self, sensor, hass):
        """WC1: sunny/clear → context='clear'."""
        weather = MockState("weather.home", "sunny", {"temperature": 22.5})
        hass.states = MockStates([weather])
        sensor._hass = hass
        sensor._update_weather_context()
        
        assert sensor._attr_native_value == "clear"
        assert sensor._attr_extra_state_attributes["condition"] == "sunny"
        assert sensor._attr_extra_state_attributes["temperature"] == 22.5
    
    def test_wc2_cloudy_condition(self, sensor, hass):
        """WC2: cloudy/partlycloudy → context='cloudy'."""
        for condition in ["cloudy", "partlycloudy"]:
            weather = MockState("weather.home", condition, {"temperature": 18.0})
            hass.states = MockStates([weather])
            sensor._hass = hass
            sensor._update_weather_context()
            
            assert sensor._attr_native_value == "cloudy"
    
    def test_wc3_rainy_condition(self, sensor, hass):
        """WC3: rain/drizzle/pouring → context='rainy'."""
        for condition in ["rain", "drizzle", "pouring"]:
            weather = MockState("weather.home", condition, {"temperature": 12.0})
            hass.states = MockStates([weather])
            sensor._hass = hass
            sensor._update_weather_context()
            
            assert sensor._attr_native_value == "rainy"
    
    def test_wc4_snowy_condition(self, sensor, hass):
        """WC4: snow/blizzard/sleet → context='snowy'."""
        for condition in ["snow", "blizzard", "sleet"]:
            weather = MockState("weather.home", condition, {"temperature": -5.0})
            hass.states = MockStates([weather])
            sensor._hass = hass
            sensor._update_weather_context()
            
            assert sensor._attr_native_value == "snowy"
    
    def test_wc5_severe_condition(self, sensor, hass):
        """WC5: fog/hail/thunderstorm → context='severe'."""
        for condition in ["fog", "hail", "thunderstorm"]:
            weather = MockState("weather.home", condition, {"temperature": 15.0})
            hass.states = MockStates([weather])
            sensor._hass = hass
            sensor._update_weather_context()
            
            assert sensor._attr_native_value == "severe"
    
    def test_wc6_unknown_condition(self, sensor, hass):
        """WC6: Unknown condition → context='unknown'."""
        weather = MockState("weather.home", "weird", {"temperature": 20.0})
        hass.states = MockStates([weather])
        sensor._hass = hass
        sensor._update_weather_context()
        
        assert sensor._attr_native_value == "unknown"
        assert sensor._attr_extra_state_attributes["condition"] == "weird"
    
    def test_wc7_no_weather_entities(self, sensor, hass):
        """WC7: No weather entities → native_value='unknown'."""
        hass.states = MockStates([])
        sensor._hass = hass
        sensor._update_weather_context()
        
        assert sensor._attr_native_value == "unknown"
    
    def test_wc8_icon_static(self, sensor, hass):
        """WC8: Icon is static mdi:weather-partly-cloudy."""
        assert sensor._attr_icon == "mdi:weather-partly-cloudy"
    
    def test_wc9_attrs_full(self, sensor, hass):
        """WC9: Full attributes with condition, temperature, entity_id."""
        weather = MockState("weather.home", "sunny", {"temperature": 25.0})
        hass.states = MockStates([weather])
        sensor._hass = hass
        sensor._update_weather_context()
        
        attrs = sensor._attr_extra_state_attributes
        assert "condition" in attrs
        assert "temperature" in attrs
        assert "entity_id" in attrs
        assert attrs["condition"] == "sunny"
        assert attrs["temperature"] == 25.0
        assert attrs["entity_id"] == "weather.home"
    
    def test_wc10_temperature_missing(self, sensor, hass):
        """WC10: Temperature attribute missing → None in attrs."""
        weather = MockState("weather.home", "sunny", {})
        hass.states = MockStates([weather])
        sensor._hass = hass
        sensor._update_weather_context()
        
        assert sensor._attr_extra_state_attributes["temperature"] is None
    
    def test_wc11_first_weather_used(self, sensor, hass):
        """WC11: Multiple weather entities → first one used."""
        weathers = [
            MockState("weather.home", "sunny", {"temperature": 22.0}),
            MockState("weather.forecast", "rainy", {"temperature": 18.0}),
        ]
        hass.states = MockStates(weathers)
        sensor._hass = hass
        sensor._update_weather_context()
        
        assert sensor._attr_native_value == "clear"
        assert sensor._attr_extra_state_attributes["temperature"] == 22.0
        assert sensor._attr_extra_state_attributes["entity_id"] == "weather.home"


# ─────────────────────────────────────────────────────────────────────────────
# Global Contract Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGlobalContract:
    """Global contract verification for environment_sensors.py."""
    
    def test_gc1_ha_local_only_no_core_api(self):
        """GC1: All sensors use only hass.states.async_all() — no Core API calls."""
        import inspect
        from custom_components.pilotsuite.sensors import environment_sensors
        
        source = inspect.getsource(environment_sensors)
        
        # Verify no Core API patterns
        assert "_core_base_url" not in source
        assert "coordinator.data" not in source
        
        # Verify HA-local patterns present
        assert "hass.states.async_all" in source or "self._hass.states.async_all" in source
    
    def test_gc2_no_local_semantic_invention(self):
        """GC2: Sensors perform trivial state aggregation + threshold mapping only."""
        import inspect
        from custom_components.pilotsuite.sensors import environment_sensors
        
        source = inspect.getsource(environment_sensors)
        
        # No complex logic patterns
        assert "machine learning" not in source.lower()
        assert "neural" not in source.lower()
        assert "prediction" not in source.lower()
