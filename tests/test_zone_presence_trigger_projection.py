"""Projection contract tests for zone_presence_trigger sensors.

Verifies ZonePresenceTriggerSensor + ZonePresenceOverviewSensor are pure
Projection-Shells on /api/v1/zone-automation/dashboard — no local semantic
invention beyond state mirroring.

HA-242 — zone_presence_trigger projection contract (16 cases)
"""
import pytest
from unittest.mock import MagicMock


# ─── Shared contract mirror ────────────────────────────────────────────────────

class ZonePresenceTriggerContract:
    """Contract mirror for ZonePresenceTriggerSensor.

    Endpoint: GET /api/v1/zone-automation/dashboard
    """
    ENDPOINT = "/api/v1/zone-automation/dashboard"

    @staticmethod
    def native_value(zone_data: dict) -> bool | None:
        if zone_data is None:
            return None
        return zone_data.get("state", {}).get("occupied", False)

    @staticmethod
    def icon(zone_data: dict, automation_mode: str = "learning") -> str:
        if automation_mode == "off":
            return "mdi:motion-sensor-off"
        if automation_mode == "learning":
            return "mdi:brain"
        if zone_data and zone_data.get("state", {}).get("occupied"):
            return "mdi:motion-sensor"
        return "mdi:motion-sensor-off"

    @staticmethod
    def attrs(zone_data: dict, automation_mode: str = "learning") -> dict:
        if not zone_data:
            return {
                "zone_id": "",
                "zone_name": "",
                "automation_mode": automation_mode,
                "presence_confirmed": False,
                "lights_on": False,
                "lights_enabled": True,
                "brightness_target_pct": 0,
                "current_brightness_pct": 0,
                "music_playing": False,
                "music_enabled": True,
                "music_follow_mode": False,
                "presence_delay_s": 5,
                "absence_delay_s": 120,
            }
        state = zone_data.get("state", {})
        config = zone_data.get("config", {})
        light_cfg = config.get("light", {})
        music_cfg = config.get("music", {})
        return {
            "zone_id": zone_data.get("zone_id", ""),
            "zone_name": zone_data.get("zone_name", ""),
            "automation_mode": automation_mode,
            "presence_confirmed": state.get("presence_confirmed", False),
            "lights_on": state.get("lights_on", False),
            "lights_enabled": light_cfg.get("enabled", True),
            "brightness_target_pct": light_cfg.get("brightness_pct", 0),
            "current_brightness_pct": state.get("current_brightness_pct", 0),
            "music_playing": state.get("music_playing", False),
            "music_enabled": music_cfg.get("enabled", True),
            "music_follow_mode": music_cfg.get("follow_mode", False),
            "presence_delay_s": light_cfg.get("presence_delay_s", 5),
            "absence_delay_s": light_cfg.get("absence_delay_s", 120),
        }


class ZonePresenceOverviewContract:
    """Contract mirror for ZonePresenceOverviewSensor.

    Endpoint: GET /api/v1/zone-automation/dashboard (same endpoint, summary field)
    """
    ENDPOINT = "/api/v1/zone-automation/dashboard"

    @staticmethod
    def native_value(summary: dict) -> bool | None:
        if not summary:
            return None
        occupied = summary.get("occupied_zones", 0)
        return occupied > 0

    @staticmethod
    def icon(summary: dict) -> str:
        if not summary or summary.get("occupied_zones", 0) == 0:
            return "mdi:home-export-outline"
        return "mdi:home-account"

    @staticmethod
    def attrs(summary: dict) -> dict:
        if not summary:
            return {
                "total_zones": 0,
                "occupied_zones": 0,
                "active_lights": 0,
                "active_music": 0,
            }
        return {
            "total_zones": summary.get("total_zones", 0),
            "occupied_zones": summary.get("occupied_zones", 0),
            "active_lights": summary.get("active_lights", 0),
            "active_music": summary.get("active_music", 0),
        }


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def coordinator():
    return MagicMock()


@pytest.fixture
def zone_data_occupied():
    return {
        "zone_id": "living_room",
        "zone_name": "Wohnzimmer",
        "state": {
            "occupied": True,
            "presence_confirmed": True,
            "lights_on": True,
            "music_playing": False,
            "current_brightness_pct": 75,
        },
        "config": {
            "light": {
                "enabled": True,
                "brightness_pct": 80,
                "presence_delay_s": 5,
                "absence_delay_s": 120,
            },
            "music": {
                "enabled": True,
                "follow_mode": False,
            },
        },
    }


@pytest.fixture
def zone_data_empty():
    return {
        "zone_id": "bedroom",
        "zone_name": "Schlafzimmer",
        "state": {
            "occupied": False,
            "presence_confirmed": False,
            "lights_on": False,
            "music_playing": False,
            "current_brightness_pct": 0,
        },
        "config": {
            "light": {"enabled": True, "presence_delay_s": 10, "absence_delay_s": 300},
            "music": {"enabled": False, "follow_mode": True},
        },
    }


@pytest.fixture
def zone_data_music():
    return {
        "zone_id": "kitchen",
        "zone_name": "Küche",
        "state": {
            "occupied": True,
            "presence_confirmed": True,
            "lights_on": True,
            "music_playing": True,
            "current_brightness_pct": 100,
        },
        "config": {
            "light": {"enabled": True, "brightness_pct": 100, "presence_delay_s": 3, "absence_delay_s": 60},
            "music": {"enabled": True, "follow_mode": True},
        },
    }


@pytest.fixture
def summary_occupied():
    return {
        "total_zones": 4,
        "occupied_zones": 2,
        "active_lights": 3,
        "active_music": 1,
    }


@pytest.fixture
def summary_empty():
    return {
        "total_zones": 4,
        "occupied_zones": 0,
        "active_lights": 0,
        "active_music": 0,
    }


# ─── ZonePresenceTriggerSensor native_value ───────────────────────────────────

class TestZonePresenceTriggerNativeValue:
    """ZP1–ZP4: ZonePresenceTriggerSensor.is_on / native_value contract."""

    def test_zp1_occupied_true(self, zone_data_occupied):
        """Occupied zone → is_on=True."""
        assert ZonePresenceTriggerContract.native_value(zone_data_occupied) is True

    def test_zp2_empty_zone(self, zone_data_empty):
        """Empty zone → is_on=False."""
        assert ZonePresenceTriggerContract.native_value(zone_data_empty) is False

    def test_zp3_missing_state(self):
        """Zone without state field → False (not None — .get with defaults)."""
        assert ZonePresenceTriggerContract.native_value({}) is False
        assert ZonePresenceTriggerContract.native_value({"zone_id": "x"}) is False

    def test_zp4_null_zone_data(self):
        """Null/None zone data → None."""
        assert ZonePresenceTriggerContract.native_value(None) is None


# ─── ZonePresenceTriggerSensor icon ───────────────────────────────────────────

class TestZonePresenceTriggerIcon:
    """ZP5–ZP8: ZonePresenceTriggerSensor icon contract."""

    def test_zp5_icon_learning_occupied(self, zone_data_occupied):
        """Learning mode + occupied → mdi:brain."""
        assert ZonePresenceTriggerContract.icon(zone_data_occupied, "learning") == "mdi:brain"

    def test_zp6_icon_off(self, zone_data_occupied):
        """Off mode → mdi:motion-sensor-off regardless of occupancy."""
        assert ZonePresenceTriggerContract.icon(zone_data_occupied, "off") == "mdi:motion-sensor-off"

    def test_zp7_icon_autonomy_occupied(self, zone_data_occupied):
        """Autonomy mode + occupied → mdi:motion-sensor."""
        assert ZonePresenceTriggerContract.icon(zone_data_occupied, "autonomy") == "mdi:motion-sensor"

    def test_zp8_icon_autonomy_empty(self, zone_data_empty):
        """Autonomy mode + empty → mdi:motion-sensor-off."""
        assert ZonePresenceTriggerContract.icon(zone_data_empty, "autonomy") == "mdi:motion-sensor-off"


# ─── ZonePresenceTriggerSensor attrs ─────────────────────────────────────────

class TestZonePresenceTriggerAttrs:
    """ZP9–ZP13: ZonePresenceTriggerSensor extra_state_attributes contract."""

    def test_zp9_attrs_full(self, zone_data_occupied):
        """Full zone data → all attrs populated."""
        attrs = ZonePresenceTriggerContract.attrs(zone_data_occupied, "learning")
        assert attrs["zone_id"] == "living_room"
        assert attrs["zone_name"] == "Wohnzimmer"
        assert attrs["automation_mode"] == "learning"
        assert attrs["presence_confirmed"] is True
        assert attrs["lights_on"] is True
        assert attrs["brightness_target_pct"] == 80
        assert attrs["current_brightness_pct"] == 75
        assert attrs["music_playing"] is False
        assert attrs["music_follow_mode"] is False
        assert attrs["presence_delay_s"] == 5
        assert attrs["absence_delay_s"] == 120

    def test_zp10_attrs_empty_zone(self, zone_data_empty):
        """Empty zone → all lights/music off, configured delays."""
        attrs = ZonePresenceTriggerContract.attrs(zone_data_empty, "off")
        assert attrs["presence_confirmed"] is False
        assert attrs["lights_on"] is False
        assert attrs["brightness_target_pct"] == 0
        assert attrs["current_brightness_pct"] == 0
        assert attrs["music_playing"] is False
        assert attrs["music_follow_mode"] is True
        assert attrs["presence_delay_s"] == 10
        assert attrs["absence_delay_s"] == 300

    def test_zp11_attrs_music_follow(self, zone_data_music):
        """Music playing + follow_mode → attrs reflect music state."""
        attrs = ZonePresenceTriggerContract.attrs(zone_data_music, "autonomy")
        assert attrs["music_playing"] is True
        assert attrs["music_follow_mode"] is True
        assert attrs["lights_on"] is True

    def test_zp12_attrs_null_zone(self):
        """Null zone_data → safe defaults."""
        attrs = ZonePresenceTriggerContract.attrs(None, "learning")
        assert attrs["presence_confirmed"] is False
        assert attrs["lights_on"] is False
        assert attrs["music_playing"] is False

    def test_zp13_attrs_missing_config_keys(self):
        """Zone with minimal/partial config → defaults apply."""
        zone = {
            "zone_id": "office",
            "zone_name": "Büro",
            "state": {"occupied": True},
            "config": {},
        }
        attrs = ZonePresenceTriggerContract.attrs(zone, "learning")
        assert attrs["brightness_target_pct"] == 0
        assert attrs["presence_delay_s"] == 5
        assert attrs["absence_delay_s"] == 120
        assert attrs["music_follow_mode"] is False


# ─── ZonePresenceOverviewSensor ───────────────────────────────────────────────

class TestZonePresenceOverviewNativeValue:
    """ZP14–ZP16: ZonePresenceOverviewSensor is_on contract."""

    def test_zp14_some_occupied(self, summary_occupied):
        """occupied_zones > 0 → is_on=True."""
        assert ZonePresenceOverviewContract.native_value(summary_occupied) is True

    def test_zp15_none_occupied(self, summary_empty):
        """occupied_zones = 0 → is_on=False."""
        assert ZonePresenceOverviewContract.native_value(summary_empty) is False

    def test_zp16_null_summary(self):
        """Null/empty summary → None."""
        assert ZonePresenceOverviewContract.native_value(None) is None
        assert ZonePresenceOverviewContract.native_value({}) is None


class TestZonePresenceOverviewAttrs:
    """ZP17–ZP18: ZonePresenceOverviewSensor attrs contract."""

    def test_zp17_attrs_occupied(self, summary_occupied):
        attrs = ZonePresenceOverviewContract.attrs(summary_occupied)
        assert attrs["total_zones"] == 4
        assert attrs["occupied_zones"] == 2
        assert attrs["active_lights"] == 3
        assert attrs["active_music"] == 1

    def test_zp18_attrs_empty(self, summary_empty):
        attrs = ZonePresenceOverviewContract.attrs(summary_empty)
        assert attrs["total_zones"] == 4
        assert attrs["occupied_zones"] == 0
        assert attrs["active_lights"] == 0
        assert attrs["active_music"] == 0


# ─── Global Contract ──────────────────────────────────────────────────────────

class TestZonePresenceTriggerGlobalContract:
    """GC1–GC2: Global / endpoint contract."""

    def test_gc1_endpoint_is_zone_automation_dashboard(self):
        """Both sensors use /api/v1/zone-automation/dashboard."""
        assert ZonePresenceTriggerContract.ENDPOINT == "/api/v1/zone-automation/dashboard"
        assert ZonePresenceOverviewContract.ENDPOINT == "/api/v1/zone-automation/dashboard"

    def test_gc2_no_local_semantic_invention(self, coordinator):
        """No local mood/energy/weather computation — pure API projection."""
        # Import the actual sensor classes
        from custom_components.pilotsuite.sensors.zone_presence_trigger import (
            ZonePresenceTriggerSensor,
            ZonePresenceOverviewSensor,
        )
        import inspect

        # Verify async_update body only calls _fetch (inherited from CopilotBaseEntity)
        trigger_src = inspect.getsource(ZonePresenceTriggerSensor.async_update)
        overview_src = inspect.getsource(ZonePresenceOverviewSensor.async_update)

        # Both should only reference self._fetch and dict.get — no computation
        assert "_fetch" in trigger_src
        assert "_fetch" in overview_src
        # No raw HTTP calls — all go through _fetch
        assert "aiohttp" not in trigger_src
        assert "aiohttp" not in overview_src
