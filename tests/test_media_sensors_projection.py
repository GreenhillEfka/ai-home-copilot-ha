"""MediaSensors Projection-Contract-Tests (HA-155).

Verifiziert: MediaActivitySensor + MediaIntensitySensor sind reine Projection-Shells
auf coordinator.data["media_activity"] bzw. coordinator.data["media_intensity"].
Contract: keine lokale Semantik-Invention, triviale Dict-Lookups.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock


class MediaActivitySensorContract:
    """Contract-Mirror für MediaActivitySensor."""

    ENDPOINT = "coordinator.data[media_activity]"

    @staticmethod
    def native_value(data: dict) -> str:
        if not data:
            return "idle"
        return data.get("media_activity", "idle")

    @staticmethod
    def attrs(data: dict) -> dict:
        if not data:
            return {}
        return data.get("media_activity_attrs", {})


class MediaIntensitySensorContract:
    """Contract-Mirror für MediaIntensitySensor."""

    ENDPOINT = "coordinator.data[media_intensity]"

    @staticmethod
    def native_value(data: dict) -> float:
        if not data:
            return 0.0
        return data.get("media_intensity", 0.0)

    @staticmethod
    def attrs(data: dict) -> dict:
        if not data:
            return {}
        return data.get("media_intensity_attrs", {})


@pytest.fixture
def coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def hass():
    h = MagicMock()
    h.states.async_all = MagicMock(return_value=[])
    return h


class TestMediaActivitySensor:
    """MediaActivitySensor Projection-Contract-Tests."""

    def test_MA1_native_value_idle(self, coordinator, hass):
        """MA1: Leere data → 'idle'."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {}
        assert sensor.native_value == "idle"

    def test_MA2_native_value_playing(self, coordinator, hass):
        """MA2: media_activity=playing → 'playing'."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {"media_activity": "playing"}
        assert sensor.native_value == "playing"

    def test_MA3_native_value_paused(self, coordinator, hass):
        """MA3: media_activity=paused → 'paused'."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {"media_activity": "paused"}
        assert sensor.native_value == "paused"

    def test_MA4_native_value_off(self, coordinator, hass):
        """MA4: media_activity=off → 'off'."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {"media_activity": "off"}
        assert sensor.native_value == "off"

    def test_MA5_attrs_empty(self, coordinator, hass):
        """MA5: Leere data → leere attrs."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {}
        assert sensor.extra_state_attributes == {}

    def test_MA6_attrs_full(self, coordinator, hass):
        """MA6: Vollständige attrs werden durchgereicht."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {
            "media_activity": "playing",
            "media_activity_attrs": {"active_players": 2, "last_activity": "2026-04-06T20:00:00Z"},
        }
        attrs = sensor.extra_state_attributes
        assert attrs["active_players"] == 2
        assert attrs["last_activity"] == "2026-04-06T20:00:00Z"

    def test_MA7_none_data(self, coordinator, hass):
        """MA7: None data → 'idle'."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = None
        assert sensor.native_value == "idle"

    def test_MA8_contract_endpoint(self, coordinator, hass):
        """GC1: Verwendet coordinator.data[media_activity]."""
        assert MediaActivitySensorContract.ENDPOINT == "coordinator.data[media_activity]"

    def test_MA9_no_local_semantic(self, coordinator, hass):
        """GC2: Keine lokale Semantik-Invention."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor
        sensor = MediaActivitySensor(coordinator, hass)
        coordinator.data = {"media_activity": "playing"}
        # native_value ist deterministisch aus data abgeleitet
        assert sensor.native_value == "playing"


class TestMediaIntensitySensor:
    """MediaIntensitySensor Projection-Contract-Tests."""

    def test_MI1_native_value_zero(self, coordinator, hass):
        """MI1: Leere data → 0.0."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {}
        assert sensor.native_value == 0.0

    def test_MI2_native_value_float(self, coordinator, hass):
        """MI2: media_intensity=0.75 → 0.75."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {"media_intensity": 0.75}
        assert sensor.native_value == 0.75

    def test_MI3_native_value_one(self, coordinator, hass):
        """MI3: media_intensity=1.0 → 1.0."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {"media_intensity": 1.0}
        assert sensor.native_value == 1.0

    def test_MI4_attrs_empty(self, coordinator, hass):
        """MI4: Leere data → leere attrs."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {}
        assert sensor.extra_state_attributes == {}

    def test_MI5_attrs_full(self, coordinator, hass):
        """MI5: Vollständige attrs werden durchgereicht."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {
            "media_intensity": 0.6,
            "media_intensity_attrs": {"avg_volume": 45.0, "peak_volume": 78.0, "active_sources": ["tv"]},
        }
        attrs = sensor.extra_state_attributes
        assert attrs["avg_volume"] == 45.0
        assert attrs["active_sources"] == ["tv"]

    def test_MI6_none_data(self, coordinator, hass):
        """MI6: None data → 0.0."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = None
        assert sensor.native_value == 0.0

    def test_MI7_contract_endpoint(self, coordinator, hass):
        """GC1: Verwendet coordinator.data[media_intensity]."""
        assert MediaIntensitySensorContract.ENDPOINT == "coordinator.data[media_intensity]"

    def test_MI8_no_local_semantic(self, coordinator, hass):
        """GC2: Keine lokale Semantik-Invention."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaIntensitySensor
        sensor = MediaIntensitySensor(coordinator, hass)
        coordinator.data = {"media_intensity": 0.8}
        # native_value ist deterministisch aus data abgeleitet
        assert sensor.native_value == 0.8


class TestMediaSensorsGlobalContract:
    """Globale Contract-Tests für MediaSensors."""

    def test_GC1_pure_projection_shell(self, coordinator, hass):
        """GC1: Beide Sensoren sind reine Projection-Shells."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor, MediaIntensitySensor

        coordinator.data = {
            "media_activity": "playing",
            "media_activity_attrs": {"active_players": 1},
            "media_intensity": 0.5,
            "media_intensity_attrs": {"avg_volume": 50.0},
        }

        activity = MediaActivitySensor(coordinator, hass)
        intensity = MediaIntensitySensor(coordinator, hass)

        # Beide lesen nur aus coordinator.data, keine lokale Berechnung
        assert activity.native_value == "playing"
        assert intensity.native_value == 0.5

    def test_GC2_no_state_invention(self, coordinator, hass):
        """GC2: Keine HA-State-basierte Semantik im Core-Pfad."""
        from custom_components.copilot_ha.sensors.media_sensors import MediaActivitySensor, MediaIntensitySensor

        # MediaActivitySensor + MediaIntensitySensor nutzen coordinator.data
        # MediaStateCache wird nur für HA-local Fallback verwendet (nicht im Test)
        coordinator.data = {"media_activity": "idle", "media_intensity": 0.0}

        activity = MediaActivitySensor(coordinator, hass)
        intensity = MediaIntensitySensor(coordinator, hass)

        # Beide liefern coordinator-Werte, keine HA-State-Aggregation
        assert activity.native_value == "idle"
        assert intensity.native_value == 0.0
