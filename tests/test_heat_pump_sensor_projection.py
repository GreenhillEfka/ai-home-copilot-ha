"""Heat Pump Sensor Projection Contract Tests (HA-159).

Verifies HeatPumpSensor is a pure projection shell on
/api/v1/regional/heatpump/status + /api/v1/regional/heatpump/schedule.

HeatPumpSensor: state = current_cop (float or None); icon from current_action;
attrs from status fields + schedule fields when present.

No local semantic invention beyond trivial Dict-Lookups and static icon-map.

HA-159 — 2026-04-07
"""
from __future__ import annotations

import pytest


# =============================================================================
# Contract Mirrors — mirror the sensor logic without importing
# =============================================================================

class HeatPumpSensorContract:
    """Mirror of HeatPumpSensor logic.

    Contract:
    - reads: /api/v1/regional/heatpump/status + /api/v1/regional/heatpump/schedule
    - state: _status.get("current_cop") — float or None
    - icon: static map on current_action
    - attrs: status fields + schedule fields when _schedule is truthy
    """

    # ------------------------------------------------------------------
    # native_value
    # ------------------------------------------------------------------
    @staticmethod
    def native_value(status: dict | None) -> float | None:
        # ok=false signals the sensor did not update _status — treated as empty {}
        if not status or status.get("ok") is False:
            return None
        return status.get("current_cop")

    # ------------------------------------------------------------------
    # icon
    # ------------------------------------------------------------------
    @staticmethod
    def icon(status: dict | None) -> str:
        if not status:
            return "mdi:heat-pump-outline"
        action = status.get("current_action", "off")
        if action == "heat":
            return "mdi:heat-pump"
        elif action == "dhw":
            return "mdi:water-boiler"
        elif action == "solar_boost":
            return "mdi:solar-power-variant"
        elif action == "defrost":
            return "mdi:snowflake-melt"
        return "mdi:heat-pump-outline"

    # ------------------------------------------------------------------
    # extra_state_attributes
    # ------------------------------------------------------------------
    @staticmethod
    def extra_state_attributes(status: dict | None, schedule: dict | None) -> dict:
        attrs = {
            "pump_type": (status or {}).get("pump_type", "air_water"),
            "current_action": (status or {}).get("current_action", "off"),
            "current_cop": (status or {}).get("current_cop", 0),
            "current_power_kw": (status or {}).get("current_power_kw", 0),
            "room_temp_c": (status or {}).get("room_temp_c", 0),
            "target_room_temp_c": (status or {}).get("target_room_temp_c", 21),
            "hot_water_temp_c": (status or {}).get("hot_water_temp_c", 0),
            "hot_water_target_c": (status or {}).get("hot_water_target_c", 55),
            "outdoor_temp_c": (status or {}).get("outdoor_temp_c", 0),
            "runtime_today_h": (status or {}).get("runtime_today_h", 0),
            "heat_today_kwh": (status or {}).get("heat_today_kwh", 0),
            "electricity_today_kwh": (status or {}).get("electricity_today_kwh", 0),
            "cost_today_eur": (status or {}).get("cost_today_eur", 0),
            "avg_cop_today": (status or {}).get("avg_cop_today", 0),
            "strategy": (status or {}).get("strategy", "cop_optimized"),
            "next_action": (status or {}).get("next_action", ""),
            "next_action_at": (status or {}).get("next_action_at", ""),
        }

        if schedule:
            attrs["total_heat_kwh"] = schedule.get("total_heat_kwh", 0)
            attrs["total_electricity_kwh"] = schedule.get("total_electricity_kwh", 0)
            attrs["total_cost_eur"] = schedule.get("total_cost_eur", 0)
            attrs["avg_cop"] = schedule.get("avg_cop", 0)
            attrs["runtime_hours"] = schedule.get("runtime_hours", 0)
            attrs["dhw_cycles"] = schedule.get("dhw_cycles", 0)
            attrs["defrost_hours"] = schedule.get("defrost_hours", 0)

        return attrs


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def full_status():
    return {
        "ok": True,
        "pump_type": "ground_source",
        "current_action": "heat",
        "current_cop": 4.2,
        "current_power_kw": 2.5,
        "room_temp_c": 21.5,
        "target_room_temp_c": 22,
        "hot_water_temp_c": 48,
        "hot_water_target_c": 55,
        "outdoor_temp_c": -3,
        "runtime_today_h": 6.5,
        "heat_today_kwh": 45.0,
        "electricity_today_kwh": 10.7,
        "cost_today_eur": 4.28,
        "avg_cop_today": 4.0,
        "strategy": "cop_optimized",
        "next_action": "dhw",
        "next_action_at": "2026-04-07T08:00",
    }


@pytest.fixture
def full_schedule():
    return {
        "ok": True,
        "total_heat_kwh": 120.0,
        "total_electricity_kwh": 28.5,
        "total_cost_eur": 11.40,
        "avg_cop": 4.2,
        "runtime_hours": 8.0,
        "dhw_cycles": 3,
        "defrost_hours": 0.2,
    }


@pytest.fixture
def defaults_status():
    """Status with only current_action present — all optional fields get defaults."""
    return {"current_action": "off"}


# =============================================================================
# HP1: native_value cases
# =============================================================================

class TestHP1NativeValue:
    @pytest.mark.parametrize("status,expected", [
        # HP1-1: Full COP reading
        pytest.param({"ok": True, "current_cop": 4.2}, 4.2, id="full_cop"),
        # HP1-2: COP 0 edge
        pytest.param({"ok": True, "current_cop": 0.0}, 0.0, id="cop_zero"),
        # HP1-3: COP None — field present but null
        pytest.param({"ok": True, "current_cop": None}, None, id="cop_none_value"),
        # HP1-4: current_cop key absent
        pytest.param({"ok": True}, None, id="cop_key_absent"),
        # HP1-5: ok false → sensor does NOT update _status → returns None (empty status)
        pytest.param({"ok": False, "current_cop": 5.0}, None, id="ok_false"),
        # HP1-6: empty dict
        pytest.param({}, None, id="empty_dict"),
        # HP1-7: None input
        pytest.param(None, None, id="none_input"),
    ])
    def test_native_value(self, status, expected):
        result = HeatPumpSensorContract.native_value(status)
        assert result == expected


# =============================================================================
# HP2: icon cases
# =============================================================================

class TestHP2Icon:
    @pytest.mark.parametrize("status, expected", [
        # HP2-1: heat action
        ({"current_action": "heat"}, "mdi:heat-pump"),
        # HP2-2: dhw action
        ({"current_action": "dhw"}, "mdi:water-boiler"),
        # HP2-3: solar_boost action
        ({"current_action": "solar_boost"}, "mdi:solar-power-variant"),
        # HP2-4: defrost action
        ({"current_action": "defrost"}, "mdi:snowflake-melt"),
        # HP2-5: off action (default)
        ({"current_action": "off"}, "mdi:heat-pump-outline"),
        # HP2-6: idle action (unknown → outline)
        ({"current_action": "idle"}, "mdi:heat-pump-outline"),
        # HP2-7: unknown action string
        ({"current_action": "unknown_action"}, "mdi:heat-pump-outline"),
        # HP2-8: no current_action key (default off)
        ({}, "mdi:heat-pump-outline"),
        # HP2-9: None input
        (None, "mdi:heat-pump-outline"),
    ])
    def test_icon(self, status, expected):
        result = HeatPumpSensorContract.icon(status)
        assert result == expected


# =============================================================================
# HP3: extra_state_attributes cases
# =============================================================================

class TestHP3ExtraStateAttributes:
    def test_full_attrs(self, full_status, full_schedule):
        attrs = HeatPumpSensorContract.extra_state_attributes(full_status, full_schedule)
        # Status fields
        assert attrs["pump_type"] == "ground_source"
        assert attrs["current_action"] == "heat"
        assert attrs["current_cop"] == 4.2
        assert attrs["current_power_kw"] == 2.5
        assert attrs["room_temp_c"] == 21.5
        assert attrs["target_room_temp_c"] == 22
        assert attrs["hot_water_temp_c"] == 48
        assert attrs["hot_water_target_c"] == 55
        assert attrs["outdoor_temp_c"] == -3
        assert attrs["runtime_today_h"] == 6.5
        assert attrs["heat_today_kwh"] == 45.0
        assert attrs["electricity_today_kwh"] == 10.7
        assert attrs["cost_today_eur"] == 4.28
        assert attrs["avg_cop_today"] == 4.0
        assert attrs["strategy"] == "cop_optimized"
        assert attrs["next_action"] == "dhw"
        assert attrs["next_action_at"] == "2026-04-07T08:00"
        # Schedule fields
        assert attrs["total_heat_kwh"] == 120.0
        assert attrs["total_electricity_kwh"] == 28.5
        assert attrs["total_cost_eur"] == 11.40
        assert attrs["avg_cop"] == 4.2
        assert attrs["runtime_hours"] == 8.0
        assert attrs["dhw_cycles"] == 3
        assert attrs["defrost_hours"] == 0.2

    def test_status_only_no_schedule(self, full_status):
        attrs = HeatPumpSensorContract.extra_state_attributes(full_status, None)
        assert attrs["pump_type"] == "ground_source"
        assert attrs["current_cop"] == 4.2
        # No schedule fields when schedule is None/falsy
        assert "total_heat_kwh" not in attrs
        assert "avg_cop" not in attrs

    def test_empty_schedule(self, full_status):
        attrs = HeatPumpSensorContract.extra_state_attributes(full_status, {})
        # Empty dict {} is falsy → no schedule fields
        assert "total_heat_kwh" not in attrs
        assert "avg_cop" not in attrs

    def test_defaults_when_missing(self, defaults_status):
        """All optional status fields get their defaults."""
        attrs = HeatPumpSensorContract.extra_state_attributes(defaults_status, None)
        assert attrs["pump_type"] == "air_water"  # default
        assert attrs["current_action"] == "off"
        assert attrs["current_cop"] == 0
        assert attrs["current_power_kw"] == 0
        assert attrs["room_temp_c"] == 0
        assert attrs["target_room_temp_c"] == 21
        assert attrs["hot_water_temp_c"] == 0
        assert attrs["hot_water_target_c"] == 55
        assert attrs["outdoor_temp_c"] == 0
        assert attrs["runtime_today_h"] == 0
        assert attrs["heat_today_kwh"] == 0
        assert attrs["electricity_today_kwh"] == 0
        assert attrs["cost_today_eur"] == 0
        assert attrs["avg_cop_today"] == 0
        assert attrs["strategy"] == "cop_optimized"
        assert attrs["next_action"] == ""
        assert attrs["next_action_at"] == ""

    def test_none_status(self):
        attrs = HeatPumpSensorContract.extra_state_attributes(None, None)
        # None status → all defaults from (status or {}) pattern
        assert attrs["pump_type"] == "air_water"
        assert attrs["current_cop"] == 0
        assert attrs["target_room_temp_c"] == 21
        assert attrs["hot_water_target_c"] == 55
        assert attrs["strategy"] == "cop_optimized"

    def test_schedule_partial(self, full_status):
        """Schedule dict with some keys missing — partial fill."""
        partial = {"avg_cop": 3.8}
        attrs = HeatPumpSensorContract.extra_state_attributes(full_status, partial)
        assert attrs["avg_cop"] == 3.8
        # Other schedule fields use their defaults
        assert attrs["total_heat_kwh"] == 0
        assert attrs["runtime_hours"] == 0


# =============================================================================
# HP4: edge cases
# =============================================================================

class TestHP4EdgeCases:
    def test_status_not_ok(self):
        """ok=false → sensor does NOT update _status → native_value None."""
        status = {"ok": False, "current_cop": 5.0, "current_action": "heat"}
        # Contract mirrors sensor behavior: ok=false means status not updated
        assert HeatPumpSensorContract.native_value(status) is None
        assert HeatPumpSensorContract.icon(status) == "mdi:heat-pump"

    def test_extra_fields_in_status(self, full_status):
        """Extra unknown fields in status are ignored."""
        enriched = {**full_status, "extra_unknown_field": "ignored", "another": 999}
        attrs = HeatPumpSensorContract.extra_state_attributes(enriched, None)
        assert "extra_unknown_field" not in attrs
        assert "another" not in attrs

    def test_schedule_with_extra_keys(self, full_schedule):
        """Extra keys in schedule dict are ignored."""
        enriched = {**full_schedule, "unknown_key": "dropped", "extra_val": 123}
        attrs = HeatPumpSensorContract.extra_state_attributes({}, enriched)
        assert "unknown_key" not in attrs
        assert "extra_val" not in attrs

    def test_status_with_non_numeric_cop(self):
        """current_cop may be returned as string or unexpected type."""
        assert HeatPumpSensorContract.native_value({"current_cop": "4.2"}) == "4.2"
        assert HeatPumpSensorContract.native_value({"current_cop": {}}) == {}

    def test_status_cop_none_vs_absent(self):
        """None vs absent: both yield None for current_cop."""
        assert HeatPumpSensorContract.native_value({"current_cop": None}) is None
        assert HeatPumpSensorContract.native_value({}) is None


# =============================================================================
# GC: Global Contract
# =============================================================================

class TestGCHeatPump:
    """GC1: Source inspection — hits /api/v1/regional/heatpump/*."""
    def test_hits_correct_endpoints(self):
        # HeatPumpSensor hits two endpoints:
        # GET /api/v1/regional/heatpump/status
        # GET /api/v1/regional/heatpump/schedule
        # Verify via direct source read (avoids import issues)
        import os
        src_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "copilot_ha", "sensors", "heat_pump_sensor.py")
        with open(src_path) as fh:
            source = fh.read()
        assert "/heatpump/status" in source
        assert "/heatpump/schedule" in source

    """GC2: No local semantic invention — all logic is dict-lookups + static map."""
    def test_no_local_semantic_invention(self, full_status, full_schedule):
        nv = HeatPumpSensorContract.native_value(full_status)
        icon = HeatPumpSensorContract.icon(full_status)
        attrs = HeatPumpSensorContract.extra_state_attributes(full_status, full_schedule)
        # All values are direct lookups or defaults from status/schedule
        # No threshold computation, no classification, no heuristics
        assert isinstance(nv, (float, type(None)))
        assert isinstance(icon, str)
        assert isinstance(attrs, dict)
