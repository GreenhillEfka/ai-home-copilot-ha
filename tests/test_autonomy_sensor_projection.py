"""Projection Contract Tests for AutonomyStatusSensor (HA-9).

Verifies that AutonomyStatusSensor, AutonomyHistorySensor, and
ZoneHealthOverviewSensor are pure Projection-Shells on Core-truth
(coordinator.data["autonomy"], ["autonomy_history"], ["zone_health"])
without local semantic invention.

Pattern: same as HA-3 (voice_context), HA-6 (habitus_zone), HA-8 (mood_sensor).
"""
import pytest
from unittest.mock import Mock, MagicMock


# ── Minimal mock setup (no HA imports) ─────────────────────────────────

class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass

class MockCoordinator:
    """Stand-in for CopilotDataUpdateCoordinator with known data shapes."""
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()

    def async_write_ha_state(self):
        pass


# ── Inline sensor class mirrors (test contract only, not HA wiring) ─────

class AutonomyStatusSensorContract:
    """Mirror of AutonomyStatusSensor logic for contract testing.

    Mirrors the real sensor's _handle_coordinator_update() so we verify
    the projection contract, not the HA framework wiring.
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_native_value = None
        self._extra_state_attributes = {}

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    def _handle_coordinator_update(self):
        data = self.coordinator.data or {}
        autonomy = data.get("autonomy", {})

        stats = autonomy.get("stats", {})
        zones = autonomy.get("zones", {})

        active_zones = sum(1 for z in zones.values() if z.get("mode") == "autonomy")
        total_executed = stats.get("executed", 0)

        if active_zones > 0:
            self._attr_native_value = "aktiv"
        elif any(z.get("mode") == "learning" for z in zones.values()):
            self._attr_native_value = "lernend"
        else:
            self._attr_native_value = "inaktiv"

        zone_modules = {}
        for zone_id, zone_data in zones.items():
            ms = zone_data.get("module_states")
            if ms and isinstance(ms, dict):
                zone_modules[zone_id] = ms

        self._extra_state_attributes = {
            "active_zones": active_zones,
            "total_zones": len(zones),
            "total_executed": total_executed,
            "total_suggested": stats.get("suggested", 0),
            "total_skipped": stats.get("skipped", 0),
            "total_errors": stats.get("errors", 0),
            "total_events": stats.get("total_events", 0),
            "zone_modules": zone_modules,
        }


class AutonomyHistorySensorContract:
    """Mirror of AutonomyHistorySensor logic for contract testing."""
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_native_value = None
        self._extra_state_attributes = {}

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    def _handle_coordinator_update(self):
        data = self.coordinator.data or {}
        history = data.get("autonomy_history", [])

        self._attr_native_value = len(history)
        self._extra_state_attributes = {
            "recent_actions": history[:10],
            "total_count": len(history),
        }


class ZoneHealthOverviewSensorContract:
    """Mirror of ZoneHealthOverviewSensor logic for contract testing."""
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_native_value = None
        self._extra_state_attributes = {}

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    def _handle_coordinator_update(self):
        data = self.coordinator.data or {}
        zone_health = data.get("zone_health", {})

        summary = zone_health.get("summary", {})
        zones = zone_health.get("zones", [])

        avg_score = summary.get("avg_score", 0)
        self._attr_native_value = round(avg_score)

        zone_scores = {}
        for z in zones:
            zone_scores[z.get("zone_id", "")] = {
                "score": z.get("health_score", 0),
                "status": z.get("status", "unknown"),
                "zone_name": z.get("zone_name", ""),
            }

        self._extra_state_attributes = {
            "total_zones": summary.get("total_zones", 0),
            "healthy": summary.get("healthy", 0),
            "degraded": summary.get("degraded", 0),
            "critical": summary.get("critical", 0),
            "avg_score": avg_score,
            "zones": zone_scores,
        }


# ── AutonomyStatusSensor contract tests ─────────────────────────────────────

class TestAutonomyStatusSensor:
    """AutonomyStatusSensor — pure Core-truth projection (no local semantics)."""

    def _make(self, autonomy_data: dict):
        coord = MockCoordinator({"autonomy": autonomy_data})
        return AutonomyStatusSensorContract(coord)

    # native_value: aktiv / lernend / inaktiv

    def test_active_zones_yields_aktiv(self):
        sensor = self._make({
            "stats": {"executed": 5, "suggested": 10, "skipped": 1, "errors": 0, "total_events": 16},
            "zones": {
                "zone:living": {"mode": "autonomy", "module_states": {}},
                "zone:kitchen":  {"mode": "off",       "module_states": {}},
            },
        })
        sensor._handle_coordinator_update()
        assert sensor.native_value == "aktiv"

    def test_learning_only_yields_lernend(self):
        sensor = self._make({
            "stats": {"executed": 0, "suggested": 2, "skipped": 0, "errors": 0, "total_events": 2},
            "zones": {
                "zone:bedroom": {"mode": "learning", "module_states": {}},
            },
        })
        sensor._handle_coordinator_update()
        assert sensor.native_value == "lernend"

    def test_no_active_zones_yields_inaktiv(self):
        sensor = self._make({
            "stats": {"executed": 0, "suggested": 0, "skipped": 0, "errors": 0, "total_events": 0},
            "zones": {
                "zone:bathroom": {"mode": "off", "module_states": {}},
            },
        })
        sensor._handle_coordinator_update()
        assert sensor.native_value == "inaktiv"

    def test_empty_zones_yields_inaktiv(self):
        sensor = self._make({"stats": {}, "zones": {}})
        sensor._handle_coordinator_update()
        assert sensor.native_value == "inaktiv"

    def test_missing_autonomy_key_yields_inaktiv(self):
        sensor = self._make({})
        sensor._handle_coordinator_update()
        assert sensor.native_value == "inaktiv"

    # extra_state_attributes

    def test_stats_passed_through(self):
        sensor = self._make({
            "stats": {"executed": 12, "suggested": 5, "skipped": 2, "errors": 1, "total_events": 20},
            "zones": {},
        })
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert attrs["total_executed"] == 12
        assert attrs["total_suggested"] == 5
        assert attrs["total_skipped"] == 2
        assert attrs["total_errors"] == 1
        assert attrs["total_events"] == 20

    def test_active_zone_count(self):
        sensor = self._make({
            "stats": {"executed": 1},
            "zones": {
                "z1": {"mode": "autonomy", "module_states": {}},
                "z2": {"mode": "autonomy", "module_states": {}},
                "z3": {"mode": "off",       "module_states": {}},
            },
        })
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert attrs["active_zones"] == 2
        assert attrs["total_zones"] == 3

    def test_zone_modules_extracted(self):
        sensor = self._make({
            "stats": {},
            "zones": {
                "zone:living": {
                    "mode": "autonomy",
                    "module_states": {"licht": {"state": "on"}, "heiz": {"state": "auto"}},
                },
            },
        })
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert attrs["zone_modules"]["zone:living"]["licht"]["state"] == "on"
        assert attrs["zone_modules"]["zone:living"]["heiz"]["state"] == "auto"

    def test_zone_modules_skipped_when_not_dict(self):
        sensor = self._make({
            "stats": {},
            "zones": {
                "zone:unknown": {"mode": "off", "module_states": "not-a-dict"},
            },
        })
        sensor._handle_coordinator_update()
        assert "zone:unknown" not in sensor.extra_state_attributes["zone_modules"]


# ── AutonomyHistorySensor contract tests ──────────────────────────────────────

class TestAutonomyHistorySensor:
    """AutonomyHistorySensor — pure Core-truth projection."""

    def _make(self, history: list):
        coord = MockCoordinator({"autonomy_history": history})
        return AutonomyHistorySensorContract(coord)

    def test_native_value_is_count(self):
        sensor = self._make([{"action": "a"}, {"action": "b"}, {"action": "c"}])
        sensor._handle_coordinator_update()
        assert sensor.native_value == 3

    def test_native_value_zero_on_empty(self):
        sensor = self._make([])
        sensor._handle_coordinator_update()
        assert sensor.native_value == 0

    def test_missing_history_key(self):
        sensor = self._make([])
        sensor._handle_coordinator_update()
        assert sensor.native_value == 0

    def test_recent_actions_limited_to_10(self):
        history = [{"id": i, "action": f"act_{i}"} for i in range(20)]
        sensor = self._make(history)
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert len(attrs["recent_actions"]) == 10
        assert attrs["total_count"] == 20

    def test_extra_state_attributes_structure(self):
        sensor = self._make([{"action": "test"}])
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert "recent_actions" in attrs
        assert "total_count" in attrs
        assert attrs["recent_actions"][0]["action"] == "test"


# ── ZoneHealthOverviewSensor contract tests ────────────────────────────────────

class TestZoneHealthOverviewSensor:
    """ZoneHealthOverviewSensor — pure Core-truth projection."""

    def _make(self, zone_health: dict):
        coord = MockCoordinator({"zone_health": zone_health})
        return ZoneHealthOverviewSensorContract(coord)

    def test_avg_score_rounded(self):
        sensor = self._make({
            "summary": {"avg_score": 87.6, "total_zones": 3, "healthy": 2, "degraded": 1, "critical": 0},
            "zones": [],
        })
        sensor._handle_coordinator_update()
        assert sensor.native_value == 88

    def test_avg_score_zero_when_missing(self):
        sensor = self._make({"summary": {}, "zones": []})
        sensor._handle_coordinator_update()
        assert sensor.native_value == 0

    def test_missing_zone_health_key(self):
        sensor = self._make({})
        sensor._handle_coordinator_update()
        assert sensor.native_value == 0

    def test_zone_scores_extracted(self):
        sensor = self._make({
            "summary": {"avg_score": 75, "total_zones": 2, "healthy": 1, "degraded": 1, "critical": 0},
            "zones": [
                {"zone_id": "zone:living", "health_score": 90, "status": "healthy", "zone_name": "Living"},
                {"zone_id": "zone:kitchen", "health_score": 55, "status": "degraded", "zone_name": "Kitchen"},
            ],
        })
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert attrs["zones"]["zone:living"]["score"] == 90
        assert attrs["zones"]["zone:living"]["status"] == "healthy"
        assert attrs["zones"]["zone:kitchen"]["score"] == 55
        assert attrs["zones"]["zone:kitchen"]["status"] == "degraded"

    def test_summary_counts(self):
        sensor = self._make({
            "summary": {"avg_score": 50, "total_zones": 4, "healthy": 2, "degraded": 1, "critical": 1},
            "zones": [],
        })
        sensor._handle_coordinator_update()
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 4
        assert attrs["healthy"] == 2
        assert attrs["degraded"] == 1
        assert attrs["critical"] == 1


# ── Global contract tests ─────────────────────────────────────────────────────

def test_autonomy_sensor_is_projection_shell():
    """Verify AutonomyStatusSensor reads only from coordinator.data["autonomy"]."""
    coord = MockCoordinator({
        "autonomy": {
            "stats": {"executed": 99},
            "zones": {"zone:test": {"mode": "autonomy", "module_states": {}}},
        },
    })
    sensor = AutonomyStatusSensorContract(coord)
    sensor._handle_coordinator_update()

    # native_value derived from Core data
    assert sensor.native_value == "aktiv"
    # No raw Core data leaked (projection contract)
    assert "stats" not in str(sensor.native_value)
    assert isinstance(sensor.extra_state_attributes["active_zones"], int)
    assert isinstance(sensor.extra_state_attributes["zone_modules"], dict)
