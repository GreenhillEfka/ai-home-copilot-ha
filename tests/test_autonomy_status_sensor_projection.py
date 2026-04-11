"""Projection contract tests for autonomy_status_sensor.

Verifies AutonomyStatusSensor, AutonomyHistorySensor, and
ZoneHealthOverviewSensor are pure projection shells on Core
coordinator.data — no local semantic invention.

HA-122 / HA-335 — 2026-04-11
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any


# =============================================================================
# Contract Mirror Helpers
# =============================================================================

def _as_mapping(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}



def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []



def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default



def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
    return default



def _as_string(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


# =============================================================================
# Contract Mirror
# =============================================================================

class AutonomyStatusSensorContract:
    """Mirror of AutonomyStatusSensor projection logic."""

    def __init__(self, autonomy_data: dict | None):
        self._autonomy = _as_mapping(autonomy_data)

    @property
    def native_value(self) -> str:
        zones = _as_mapping(self._autonomy.get("zones"))
        active_zones = sum(
            1 for z in zones.values() if isinstance(z, dict) and z.get("mode") == "autonomy"
        )
        if active_zones > 0:
            return "aktiv"
        if any(isinstance(z, dict) and z.get("mode") == "learning" for z in zones.values()):
            return "lernend"
        return "inaktiv"

    @property
    def icon(self) -> str:
        return "mdi:robot"

    @property
    def extra_state_attributes(self) -> dict:
        zones = _as_mapping(self._autonomy.get("zones"))
        stats = _as_mapping(self._autonomy.get("stats"))
        active_zones = sum(
            1 for z in zones.values() if isinstance(z, dict) and z.get("mode") == "autonomy"
        )

        zone_modules = {}
        for zone_id, zone_data in zones.items():
            if isinstance(zone_data, dict):
                ms = zone_data.get("module_states")
                if ms and isinstance(ms, dict):
                    zone_modules[zone_id] = ms

        return {
            "active_zones": active_zones,
            "total_zones": len(zones),
            "total_executed": _as_int(stats.get("executed")),
            "total_suggested": _as_int(stats.get("suggested")),
            "total_skipped": _as_int(stats.get("skipped")),
            "total_errors": _as_int(stats.get("errors")),
            "total_events": _as_int(stats.get("total_events")),
            "zone_modules": zone_modules,
        }


class AutonomyHistorySensorContract:
    """Mirror of AutonomyHistorySensor projection logic."""

    def __init__(self, history_data: list | None):
        self._history = _as_list(history_data)

    @property
    def native_value(self) -> int:
        return len(self._history)

    @property
    def icon(self) -> str:
        return "mdi:history"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "recent_actions": self._history[:10],
            "total_count": len(self._history),
        }


class ZoneHealthOverviewSensorContract:
    """Mirror of ZoneHealthOverviewSensor projection logic."""

    def __init__(self, zone_health_data: dict | None):
        self._zh = _as_mapping(zone_health_data)

    @property
    def native_value(self) -> int:
        summary = _as_mapping(self._zh.get("summary"))
        avg_score = _as_float(summary.get("avg_score"))
        return round(avg_score)

    @property
    def icon(self) -> str:
        return "mdi:shield-check"

    @property
    def extra_state_attributes(self) -> dict:
        summary = _as_mapping(self._zh.get("summary"))
        zones = _as_list(self._zh.get("zones"))
        avg_score = _as_float(summary.get("avg_score"))

        zone_scores = {}
        for z in zones:
            if isinstance(z, dict):
                zone_scores[_as_string(z.get("zone_id"))] = {
                    "score": _as_int(z.get("health_score")),
                    "status": _as_string(z.get("status"), "unknown"),
                    "zone_name": _as_string(z.get("zone_name")),
                }

        return {
            "total_zones": _as_int(summary.get("total_zones")),
            "healthy": _as_int(summary.get("healthy")),
            "degraded": _as_int(summary.get("degraded")),
            "critical": _as_int(summary.get("critical")),
            "avg_score": avg_score,
            "zones": zone_scores,
        }


# =============================================================================
# AS1 — AutonomyStatusSensor native_value
# =============================================================================

class TestAutonomyStatusSensorNativeValue:
    def test_as1_aktiv_with_autonomy_zone(self):
        data = {
            "zones": {
                "zone_1": {"mode": "autonomy"},
                "zone_2": {"mode": "manual"},
            },
            "stats": {},
        }
        sensor = AutonomyStatusSensorContract(data)
        assert sensor.native_value == "aktiv"

    def test_as1_lernend_only_learning_zone(self):
        data = {
            "zones": {
                "zone_1": {"mode": "learning"},
                "zone_2": {"mode": "manual"},
            },
            "stats": {},
        }
        sensor = AutonomyStatusSensorContract(data)
        assert sensor.native_value == "lernend"

    def test_as1_inaktiv_no_active_zones(self):
        data = {
            "zones": {
                "zone_1": {"mode": "manual"},
                "zone_2": {"mode": "off"},
            },
            "stats": {},
        }
        sensor = AutonomyStatusSensorContract(data)
        assert sensor.native_value == "inaktiv"

    def test_as1_m1_non_dict_autonomy_payload_defaults_to_inaktiv(self):
        sensor = AutonomyStatusSensorContract("broken")
        assert sensor.native_value == "inaktiv"

    def test_as1_m2_non_dict_zones_payload_defaults_to_inaktiv(self):
        sensor = AutonomyStatusSensorContract({"zones": "broken", "stats": {}})
        assert sensor.native_value == "inaktiv"

    def test_as1_m3_non_dict_zone_items_are_ignored(self):
        sensor = AutonomyStatusSensorContract(
            {
                "zones": {
                    "zone_1": None,
                    "zone_2": "broken",
                    "zone_3": {"mode": "learning"},
                }
            }
        )
        assert sensor.native_value == "lernend"


class TestAutonomyStatusSensorIcon:
    def test_as2_icon_is_robot(self):
        sensor = AutonomyStatusSensorContract({})
        assert sensor.icon == "mdi:robot"


class TestAutonomyStatusSensorAttrs:
    def test_as3_attrs_full_data(self):
        data = {
            "zones": {
                "zone_1": {
                    "mode": "autonomy",
                    "module_states": {"habitus": "active", "memory": "idle"},
                },
                "zone_2": {"mode": "manual"},
            },
            "stats": {
                "executed": 42,
                "suggested": 10,
                "skipped": 3,
                "errors": 1,
                "total_events": 100,
            },
        }
        sensor = AutonomyStatusSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["active_zones"] == 1
        assert attrs["total_zones"] == 2
        assert attrs["total_executed"] == 42
        assert attrs["total_suggested"] == 10
        assert attrs["total_skipped"] == 3
        assert attrs["total_errors"] == 1
        assert attrs["total_events"] == 100
        assert attrs["zone_modules"] == {"zone_1": {"habitus": "active", "memory": "idle"}}

    def test_as3_m1_non_dict_stats_payload_defaults_counts_to_zero(self):
        sensor = AutonomyStatusSensorContract(
            {
                "zones": {"zone_1": {"mode": "manual"}},
                "stats": "broken",
            }
        )
        attrs = sensor.extra_state_attributes
        assert attrs["total_executed"] == 0
        assert attrs["total_suggested"] == 0
        assert attrs["total_skipped"] == 0
        assert attrs["total_errors"] == 0
        assert attrs["total_events"] == 0

    def test_as3_m2_string_bool_float_stat_fields_default_to_zero(self):
        sensor = AutonomyStatusSensorContract(
            {
                "zones": {},
                "stats": {
                    "executed": "42",
                    "suggested": True,
                    "skipped": 3.5,
                    "errors": None,
                    "total_events": [],
                },
            }
        )
        attrs = sensor.extra_state_attributes
        assert attrs["total_executed"] == 0
        assert attrs["total_suggested"] == 0
        assert attrs["total_skipped"] == 0
        assert attrs["total_errors"] == 0
        assert attrs["total_events"] == 0

    def test_as3_m3_zone_modules_ignore_non_dict_zone_items_and_non_dict_modules(self):
        sensor = AutonomyStatusSensorContract(
            {
                "zones": {
                    "zone_1": {"mode": "autonomy", "module_states": ["bad"]},
                    "zone_2": None,
                    "zone_3": {"mode": "manual", "module_states": {"memory": "idle"}},
                },
                "stats": {},
            }
        )
        attrs = sensor.extra_state_attributes
        assert attrs["active_zones"] == 1
        assert attrs["zone_modules"] == {"zone_3": {"memory": "idle"}}


# =============================================================================
# AH1 / AH2 — AutonomyHistorySensor
# =============================================================================

class TestAutonomyHistorySensor:
    def test_ah1_native_value_count(self):
        sensor = AutonomyHistorySensorContract(["action_1", "action_2", "action_3"])
        assert sensor.native_value == 3

    def test_ah1_native_value_none(self):
        sensor = AutonomyHistorySensorContract(None)
        assert sensor.native_value == 0

    def test_ah1_m1_non_list_history_payload_defaults_to_zero(self):
        sensor = AutonomyHistorySensorContract("broken")
        assert sensor.native_value == 0
        assert sensor.extra_state_attributes == {"recent_actions": [], "total_count": 0}

    def test_ah2_attrs_recent_capped_at_10(self):
        data = [f"action_{i}" for i in range(15)]
        sensor = AutonomyHistorySensorContract(data)
        attrs = sensor.extra_state_attributes
        assert len(attrs["recent_actions"]) == 10
        assert attrs["total_count"] == 15


# =============================================================================
# ZH1 / ZH2 — ZoneHealthOverviewSensor
# =============================================================================

class TestZoneHealthOverviewSensor:
    def test_zh1_native_value_rounds(self):
        sensor = ZoneHealthOverviewSensorContract({"summary": {"avg_score": 87.6}})
        assert sensor.native_value == 88

    def test_zh1_m1_non_dict_zone_health_payload_defaults_to_zero(self):
        sensor = ZoneHealthOverviewSensorContract("broken")
        assert sensor.native_value == 0

    def test_zh1_m2_non_dict_summary_payload_defaults_to_zero(self):
        sensor = ZoneHealthOverviewSensorContract({"summary": "broken"})
        assert sensor.native_value == 0

    def test_zh1_m3_non_finite_or_non_numeric_avg_score_defaults_to_zero(self):
        for value in ["87", True, None, float("inf"), float("nan")]:
            sensor = ZoneHealthOverviewSensorContract({"summary": {"avg_score": value}})
            assert sensor.native_value == 0
            assert sensor.extra_state_attributes["avg_score"] == 0.0

    def test_zh2_attrs_full_data(self):
        data = {
            "summary": {
                "total_zones": 3,
                "healthy": 2,
                "degraded": 1,
                "critical": 0,
                "avg_score": 75.5,
            },
            "zones": [
                {"zone_id": "z1", "health_score": 90, "status": "healthy", "zone_name": "Zone 1"},
                {"zone_id": "z2", "health_score": 61, "status": "degraded", "zone_name": "Zone 2"},
                {"zone_id": "z3", "health_score": 75, "status": "healthy", "zone_name": "Zone 3"},
            ],
        }
        sensor = ZoneHealthOverviewSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 3
        assert attrs["healthy"] == 2
        assert attrs["degraded"] == 1
        assert attrs["critical"] == 0
        assert attrs["avg_score"] == 75.5
        assert attrs["zones"]["z1"]["score"] == 90
        assert attrs["zones"]["z2"]["status"] == "degraded"

    def test_zh2_m1_non_list_zones_payload_defaults_to_empty(self):
        sensor = ZoneHealthOverviewSensorContract({"summary": {}, "zones": "broken"})
        assert sensor.extra_state_attributes["zones"] == {}

    def test_zh2_m2_non_dict_zone_items_are_skipped(self):
        sensor = ZoneHealthOverviewSensorContract(
            {
                "summary": {},
                "zones": [None, "broken", {"zone_id": "z1", "health_score": 80}],
            }
        )
        assert sensor.extra_state_attributes["zones"] == {
            "z1": {"score": 80, "status": "unknown", "zone_name": ""}
        }

    def test_zh2_m3_malformed_zone_fields_fall_back_to_safe_defaults(self):
        sensor = ZoneHealthOverviewSensorContract(
            {
                "summary": {
                    "total_zones": "3",
                    "healthy": True,
                    "degraded": 1.0,
                    "critical": None,
                },
                "zones": [
                    {
                        "zone_id": "   ",
                        "health_score": 85.5,
                        "status": 7,
                        "zone_name": None,
                    }
                ],
            }
        )
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 0
        assert attrs["healthy"] == 0
        assert attrs["degraded"] == 0
        assert attrs["critical"] == 0
        assert attrs["zones"] == {
            "": {"score": 0, "status": "unknown", "zone_name": ""}
        }


# =============================================================================
# GC — Source guard
# =============================================================================

class TestGlobalContract:
    def test_gc1_source_guards_present(self):
        source = Path(
            "custom_components/pilotsuite/sensors/autonomy_status_sensor.py"
        ).read_text(encoding="utf-8")
        assert "def _as_mapping" in source
        assert "def _as_list" in source
        assert "def _as_int" in source
        assert "def _as_float" in source
        assert "def _as_string" in source
        assert "math.isfinite" in source
        assert "isinstance(z, dict)" in source
        assert "_as_mapping(self.coordinator.data)" in source
        assert "_as_list(data.get(\"autonomy_history\"))" in source
        assert "_as_mapping(data.get(\"zone_health\"))" in source
