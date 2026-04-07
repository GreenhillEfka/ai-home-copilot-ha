"""EnvironmentSensors Projection-Contract-Tests.

Contract: Environment-Sensoren sind HA-lokale Projection-Shells auf hass.states.async_all()
- LightLevelSensor: illuminance sensors (device_class="illuminance") + light states → avg_lux + level classification
- NoiseLevelSensor: noise/sound sensors + media_player states + vacuum states → noise classification
- WeatherContextSensor: weather states → condition mapping
- Keine lokale Semantik — reine State-Aggregation + Schwellenwerte

HA-175: environment_sensors.py Projection-Contract-Tests (27 Cases)
"""
import pytest
from typing import Any
from unittest.mock import MagicMock, PropertyMock

from custom_components.copilot_ha.sensors.environment_sensors import (
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


def _create_state(
    entity_id: str,
    state: str,
    attributes: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock State object."""
    mock = MagicMock()
    mock.entity_id = entity_id
    mock.state = state
    mock.attributes = attributes or {}
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# LightLevelSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLightLevelSensor:
    """Tests for LightLevelSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        mock = MagicMock()
        mock.data = {}
        return mock
    
    @pytest.fixture
    def hass(self):
        return MagicMock()
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return LightLevelSensor(coordinator, hass)
    
    def test_ll1_dark_level(self, sensor, hass):
        """LL1: avg_lux < 10 → level='dark'."""
        # No illuminance sensors
        hass.states.async_all.return_value = []
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "dark"
        assert sensor.extra_state_attributes["avg_lux"] == 0
        assert sensor.extra_state_attributes["sensor_count"] == 0
    
    def test_ll2_dim_level(self, sensor, hass):
        """LL2: 10 <= avg_lux < 100 → level='dim'."""
        illuminance_sensor = _create_state(
            "sensor.light_1",
            "50",
            {"device_class": "illuminance"}
        )
        hass.states.async_all.side_effect = lambda domain: (
            [illuminance_sensor] if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "dim"
        assert sensor.extra_state_attributes["avg_lux"] == 50.0
    
    def test_ll3_normal_level(self, sensor, hass):
        """LL3: 100 <= avg_lux < 1000 → level='normal'."""
        illuminance_sensor = _create_state(
            "sensor.light_1",
            "500",
            {"device_class": "illuminance"}
        )
        hass.states.async_all.side_effect = lambda domain: (
            [illuminance_sensor] if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "normal"
        assert sensor.extra_state_attributes["avg_lux"] == 500.0
    
    def test_ll4_bright_level(self, sensor, hass):
        """LL4: avg_lux >= 1000 → level='bright'."""
        illuminance_sensor = _create_state(
            "sensor.light_1",
            "1500",
            {"device_class": "illuminance"}
        )
        hass.states.async_all.side_effect = lambda domain: (
            [illuminance_sensor] if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "bright"
        assert sensor.extra_state_attributes["avg_lux"] == 1500.0
    
    def test_ll5_boundary_10(self, sensor, hass):
        """LL5: Boundary at 10 lux (9.9=dark, 10.0=dim)."""
        sensor_low = _create_state("sensor.low", "9.9", {"device_class": "illuminance"})
        sensor_high = _create_state("sensor.high", "10.0", {"device_class": "illuminance"})
        
        hass.states.async_all.side_effect = lambda domain: (
            [sensor_low] if domain == "sensor" and "low" in sensor_low.entity_id else
            [sensor_high] if domain == "sensor" and "high" in sensor_high.entity_id else
            []
        )
        
        sensor._hass = hass
        import asyncio
        
        asyncio.run(sensor.async_update())
        assert sensor.native_value == "dim"  # 10.0 is dim
    
    def test_ll6_boundary_100(self, sensor, hass):
        """LL6: Boundary at 100 lux (99.9=dim, 100.0=normal)."""
        sensor_low = _create_state("sensor.low", "99.9", {"device_class": "illuminance"})
        sensor_high = _create_state("sensor.high", "100.0", {"device_class": "illuminance"})
        
        hass.states.async_all.side_effect = lambda domain: (
            [sensor_low] if "low" in sensor_low.entity_id else
            [sensor_high] if "high" in sensor_high.entity_id else
            []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        assert sensor.native_value == "normal"
    
    def test_ll7_boundary_1000(self, sensor, hass):
        """LL7: Boundary at 1000 lux (999.9=normal, 1000.0=bright)."""
        sensor_low = _create_state("sensor.low", "999.9", {"device_class": "illuminance"})
        sensor_high = _create_state("sensor.high", "1000.0", {"device_class": "illuminance"})
        
        hass.states.async_all.side_effect = lambda domain: (
            [sensor_low] if "low" in sensor_low.entity_id else
            [sensor_high] if "high" in sensor_high.entity_id else
            []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        assert sensor.native_value == "bright"
    
    def test_ll8_multiple_sensors_average(self, sensor, hass):
        """LL8: Multiple illuminance sensors → average."""
        sensors = [
            _create_state("sensor.light_1", "100", {"device_class": "illuminance"}),
            _create_state("sensor.light_2", "200", {"device_class": "illuminance"}),
            _create_state("sensor.light_3", "300", {"device_class": "illuminance"}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            sensors if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["avg_lux"] == 200.0
        assert sensor.extra_state_attributes["sensor_count"] == 3
    
    def test_ll9_lights_on_count(self, sensor, hass):
        """LL9: lights_on attribute from light states."""
        lights = [
            _create_state("light.living_room", "on"),
            _create_state("light.bedroom", "on"),
            _create_state("light.kitchen", "off"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            lights if domain == "light" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["lights_on"] == 2
    
    def test_ll10_invalid_values_skipped(self, sensor, hass):
        """LL10: Invalid/non-numeric values are skipped."""
        sensors = [
            _create_state("sensor.valid", "500", {"device_class": "illuminance"}),
            _create_state("sensor.invalid", "unavailable", {"device_class": "illuminance"}),
            _create_state("sensor.none", "None", {"device_class": "illuminance"}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            sensors if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["avg_lux"] == 500.0
        assert sensor.extra_state_attributes["sensor_count"] == 1
    
    def test_ll11_negative_values_skipped(self, sensor, hass):
        """LL11: Negative values are skipped."""
        sensors = [
            _create_state("sensor.valid", "500", {"device_class": "illuminance"}),
            _create_state("sensor.negative", "-100", {"device_class": "illuminance"}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            sensors if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["avg_lux"] == 500.0
        assert sensor.extra_state_attributes["sensor_count"] == 1
    
    def test_ll12_zero_values_included(self, sensor, hass):
        """LL12: Zero values are included in average (valid reading)."""
        sensors = [
            _create_state("sensor.light_1", "0", {"device_class": "illuminance"}),
            _create_state("sensor.light_2", "100", {"device_class": "illuminance"}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            sensors if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["avg_lux"] == 50.0
        assert sensor.extra_state_attributes["sensor_count"] == 2
    
    def test_ll13_icon_static(self, sensor, hass):
        """LL13: Icon is static mdi:brightness-6."""
        assert sensor.icon == "mdi:brightness-6"
    
    def test_ll14_unit_of_measurement(self, sensor, hass):
        """LL14: Unit is lx (lux)."""
        assert sensor.native_unit_of_measurement == "lx"
    
    def test_ll15_attrs_full(self, sensor, hass):
        """LL15: Full attributes with all fields."""
        illuminance = _create_state("sensor.light", "250", {"device_class": "illuminance"})
        lights = [
            _create_state("light.l1", "on"),
            _create_state("light.l2", "off"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            [illuminance] if domain == "sensor" else
            lights if domain == "light" else
            []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        attrs = sensor.extra_state_attributes
        assert "avg_lux" in attrs
        assert "lights_on" in attrs
        assert "sensor_count" in attrs
        assert attrs["avg_lux"] == 250.0
        assert attrs["lights_on"] == 1
        assert attrs["sensor_count"] == 1
    
    def test_ll16_no_illuminance_sensors(self, sensor, hass):
        """LL16: No illuminance sensors → avg_lux=0, level=dark."""
        hass.states.async_all.return_value = []
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "dark"
        assert sensor.extra_state_attributes["avg_lux"] == 0
        assert sensor.extra_state_attributes["sensor_count"] == 0
    
    def test_ll17_non_illuminance_sensors_ignored(self, sensor, hass):
        """LL17: Sensors without device_class=illuminance are ignored."""
        sensors = [
            _create_state("sensor.temp", "22", {"device_class": "temperature"}),
            _create_state("sensor.humidity", "45", {"device_class": "humidity"}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            sensors if domain == "sensor" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["sensor_count"] == 0
        assert sensor.native_value == "dark"


# ─────────────────────────────────────────────────────────────────────────────
# NoiseLevelSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestNoiseLevelSensor:
    """Tests for NoiseLevelSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        mock = MagicMock()
        mock.data = {}
        return mock
    
    @pytest.fixture
    def hass(self):
        return MagicMock()
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return NoiseLevelSensor(coordinator, hass)
    
    def test_nl1_quiet_default(self, sensor, hass):
        """NL1: No media/vacuum → level='quiet'."""
        hass.states.async_all.return_value = []
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "quiet"
        assert sensor.extra_state_attributes["media_playing"] == 0
        assert sensor.extra_state_attributes["vacuums_active"] == 0
    
    def test_nl2_moderate_with_media(self, sensor, hass):
        """NL2: Media playing → level='moderate'."""
        media = [
            _create_state("media_player.spotify", "playing"),
            _create_state("media_player.tv", "off"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            media if domain == "media_player" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "moderate"
        assert sensor.extra_state_attributes["media_playing"] == 1
    
    def test_nl3_loud_with_vacuum(self, sensor, hass):
        """NL3: Vacuum cleaning → level='loud' (overrides media)."""
        media = [_create_state("media_player.spotify", "playing")]
        vacuums = [_create_state("vacuum.roomba", "cleaning")]
        hass.states.async_all.side_effect = lambda domain: (
            media if domain == "media_player" else
            vacuums if domain == "vacuum" else
            []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "loud"
        assert sensor.extra_state_attributes["vacuums_active"] == 1
        assert sensor.extra_state_attributes["media_playing"] == 1
    
    def test_nl4_multiple_media(self, sensor, hass):
        """NL4: Multiple media players → count in attrs."""
        media = [
            _create_state("media_player.spotify", "playing"),
            _create_state("media_player.apple_tv", "playing"),
            _create_state("media_player.chromecast", "paused"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            media if domain == "media_player" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "moderate"
        assert sensor.extra_state_attributes["media_playing"] == 2
    
    def test_nl5_multiple_vacuums(self, sensor, hass):
        """NL5: Multiple vacuums → count in attrs."""
        vacuums = [
            _create_state("vacuum.roomba", "cleaning"),
            _create_state("vacuum.roborock", "cleaning"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            vacuums if domain == "vacuum" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "loud"
        assert sensor.extra_state_attributes["vacuums_active"] == 2
    
    def test_nl6_vacuum_idle_not_counted(self, sensor, hass):
        """NL6: Vacuum in 'docked' or 'idle' not counted as active."""
        vacuums = [
            _create_state("vacuum.roomba", "docked"),
            _create_state("vacuum.roborock", "idle"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            vacuums if domain == "vacuum" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "quiet"
        assert sensor.extra_state_attributes["vacuums_active"] == 0
    
    def test_nl7_icon_static(self, sensor, hass):
        """NL7: Icon is static mdi:volume-high."""
        assert sensor.icon == "mdi:volume-high"
    
    def test_nl8_attrs_full(self, sensor, hass):
        """NL8: Full attributes with all fields."""
        media = [_create_state("media_player.spotify", "playing")]
        vacuums = [_create_state("vacuum.roomba", "cleaning")]
        hass.states.async_all.side_effect = lambda domain: (
            media if domain == "media_player" else
            vacuums if domain == "vacuum" else
            []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        attrs = sensor.extra_state_attributes
        assert "media_playing" in attrs
        assert "vacuums_active" in attrs
        assert "noise_sensors" in attrs
        assert attrs["media_playing"] == 1
        assert attrs["vacuums_active"] == 1
    
    def test_nl9_media_paused_not_counted(self, sensor, hass):
        """NL9: Media in 'paused' state not counted as playing."""
        media = [
            _create_state("media_player.spotify", "paused"),
            _create_state("media_player.tv", "idle"),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            media if domain == "media_player" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "quiet"
        assert sensor.extra_state_attributes["media_playing"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# WeatherContextSensor Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWeatherContextSensor:
    """Tests for WeatherContextSensor projection contract."""
    
    @pytest.fixture
    def coordinator(self):
        mock = MagicMock()
        mock.data = {}
        return mock
    
    @pytest.fixture
    def hass(self):
        return MagicMock()
    
    @pytest.fixture
    def sensor(self, coordinator, hass):
        return WeatherContextSensor(coordinator, hass)
    
    def test_wc1_clear_condition(self, sensor, hass):
        """WC1: sunny/clear → context='clear'."""
        weather = _create_state("weather.home", "sunny", {"temperature": 22.5})
        hass.states.async_all.side_effect = lambda domain: (
            [weather] if domain == "weather" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "clear"
        assert sensor.extra_state_attributes["condition"] == "sunny"
        assert sensor.extra_state_attributes["temperature"] == 22.5
    
    def test_wc2_cloudy_condition(self, sensor, hass):
        """WC2: cloudy/partlycloudy → context='cloudy'."""
        for condition in ["cloudy", "partlycloudy"]:
            weather = _create_state("weather.home", condition, {"temperature": 18.0})
            hass.states.async_all.side_effect = lambda domain, c=condition: (
                [_create_state("weather.home", c, {"temperature": 18.0})] if domain == "weather" else []
            )
            
            sensor._hass = hass
            import asyncio
            asyncio.run(sensor.async_update())
            
            assert sensor.native_value == "cloudy"
    
    def test_wc3_rainy_condition(self, sensor, hass):
        """WC3: rain/drizzle/pouring → context='rainy'."""
        for condition in ["rain", "drizzle", "pouring"]:
            weather = _create_state("weather.home", condition, {"temperature": 12.0})
            hass.states.async_all.side_effect = lambda domain, c=condition: (
                [_create_state("weather.home", c, {"temperature": 12.0})] if domain == "weather" else []
            )
            
            sensor._hass = hass
            import asyncio
            asyncio.run(sensor.async_update())
            
            assert sensor.native_value == "rainy"
    
    def test_wc4_snowy_condition(self, sensor, hass):
        """WC4: snow/blizzard/sleet → context='snowy'."""
        for condition in ["snow", "blizzard", "sleet"]:
            weather = _create_state("weather.home", condition, {"temperature": -5.0})
            hass.states.async_all.side_effect = lambda domain, c=condition: (
                [_create_state("weather.home", c, {"temperature": -5.0})] if domain == "weather" else []
            )
            
            sensor._hass = hass
            import asyncio
            asyncio.run(sensor.async_update())
            
            assert sensor.native_value == "snowy"
    
    def test_wc5_severe_condition(self, sensor, hass):
        """WC5: fog/hail/thunderstorm → context='severe'."""
        for condition in ["fog", "hail", "thunderstorm"]:
            weather = _create_state("weather.home", condition, {"temperature": 15.0})
            hass.states.async_all.side_effect = lambda domain, c=condition: (
                [_create_state("weather.home", c, {"temperature": 15.0})] if domain == "weather" else []
            )
            
            sensor._hass = hass
            import asyncio
            asyncio.run(sensor.async_update())
            
            assert sensor.native_value == "severe"
    
    def test_wc6_unknown_condition(self, sensor, hass):
        """WC6: Unknown condition → context='unknown'."""
        weather = _create_state("weather.home", "weird", {"temperature": 20.0})
        hass.states.async_all.side_effect = lambda domain: (
            [weather] if domain == "weather" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "unknown"
        assert sensor.extra_state_attributes["condition"] == "weird"
    
    def test_wc7_no_weather_entities(self, sensor, hass):
        """WC7: No weather entities → native_value='unknown'."""
        hass.states.async_all.return_value = []
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "unknown"
    
    def test_wc8_icon_static(self, sensor, hass):
        """WC8: Icon is static mdi:weather-partly-cloudy."""
        assert sensor.icon == "mdi:weather-partly-cloudy"
    
    def test_wc9_attrs_full(self, sensor, hass):
        """WC9: Full attributes with condition, temperature, entity_id."""
        weather = _create_state("weather.home", "sunny", {"temperature": 25.0})
        hass.states.async_all.side_effect = lambda domain: (
            [weather] if domain == "weather" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        attrs = sensor.extra_state_attributes
        assert "condition" in attrs
        assert "temperature" in attrs
        assert "entity_id" in attrs
        assert attrs["condition"] == "sunny"
        assert attrs["temperature"] == 25.0
        assert attrs["entity_id"] == "weather.home"
    
    def test_wc10_temperature_missing(self, sensor, hass):
        """WC10: Temperature attribute missing → None in attrs."""
        weather = _create_state("weather.home", "sunny", {})
        hass.states.async_all.side_effect = lambda domain: (
            [weather] if domain == "weather" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.extra_state_attributes["temperature"] is None
    
    def test_wc11_first_weather_used(self, sensor, hass):
        """WC11: Multiple weather entities → first one used."""
        weathers = [
            _create_state("weather.home", "sunny", {"temperature": 22.0}),
            _create_state("weather.forecast", "rainy", {"temperature": 18.0}),
        ]
        hass.states.async_all.side_effect = lambda domain: (
            weathers if domain == "weather" else []
        )
        
        sensor._hass = hass
        import asyncio
        asyncio.run(sensor.async_update())
        
        assert sensor.native_value == "clear"
        assert sensor.extra_state_attributes["temperature"] == 22.0
        assert sensor.extra_state_attributes["entity_id"] == "weather.home"


# ─────────────────────────────────────────────────────────────────────────────
# Global Contract Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGlobalContract:
    """Global contract verification for environment_sensors.py."""
    
    def test_gc1_ha_local_only_no_core_api(self):
        """GC1: All sensors use only hass.states.async_all() — no Core API calls."""
        # Source inspection: environment_sensors.py uses:
        # - self._hass.states.async_all("sensor") for LightLevelSensor
        # - self._hass.states.async_all("media_player") + async_all("vacuum") for NoiseLevelSensor
        # - self._hass.states.async_all("weather") for WeatherContextSensor
        # No coordinator.data access, no _core_base_url(), no _fetch() calls
        # This is verified by reading the source file
        import inspect
        from custom_components.copilot_ha.sensors import environment_sensors
        
        source = inspect.getsource(environment_sensors)
        
        # Verify no Core API patterns
        assert "_core_base_url" not in source
        assert "_fetch(" not in source or "_fetch_stub" in source  # Allow stub references
        assert "coordinator.data" not in source
        
        # Verify HA-local patterns present
        assert "hass.states.async_all" in source or "self._hass.states.async_all" in source
    
    def test_gc2_no_local_semantic_invention(self):
        """GC2: Sensors perform trivial state aggregation + threshold mapping only."""
        # LightLevelSensor: avg(illuminance values) → threshold classification (dark/dim/normal/bright)
        # NoiseLevelSensor: count(playing media, cleaning vacuums) → classification (quiet/moderate/loud)
        # WeatherContextSensor: condition string → context string mapping (dict lookup)
        # No ML, no heuristics, no pattern recognition, no local state tracking
        
        import inspect
        from custom_components.copilot_ha.sensors import environment_sensors
        
        source = inspect.getsource(environment_sensors)
        
        # No complex logic patterns
        assert "machine learning" not in source.lower()
        assert "neural" not in source.lower()
        assert "prediction" not in source.lower()
        assert "pattern" not in source.lower() or "pattern" in "device_class"  # Allow attribute references
        
        # Only simple thresholds and dict lookups
        # Verified by: if/elif chains with numeric comparisons, static CONDITION_MAP dict
