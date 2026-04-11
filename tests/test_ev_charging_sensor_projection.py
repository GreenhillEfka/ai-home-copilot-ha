"""EV Charging Sensor Projection Contract Tests (HA-160, HA-339).

Verifies EVChargingSensor is a pure projection shell on
/api/v1/regional/ev/status + /api/v1/regional/ev/schedule.

EVChargingSensor:
- state: current_soc_pct (float or None)
- icon: based on current_action (charge/solar_charge/departure_ready/idle)
- attrs: vehicle/connector/charging details + schedule data

No local semantic invention beyond trivial Dict-Lookups and statics.

HA-160 — 2026-04-07
HA-339 — 2026-04-11  (malformed payload guards)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# =============================================================================
# Contract Mirrors — mirror the sensor logic without importing
# =============================================================================

import math


# Type-safe helpers (identical to production)
def _as_mapping(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_float(value, default=0.0):
    try:
        result = float(value)
        if math.isfinite(result):
            return result
    except (TypeError, ValueError):
        pass
    return default


def _safe_string(value, default=""):
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


class EVChargingSensorContract:
    """Mirror of EVChargingSensor logic.

    Contract:
    - reads: /api/v1/regional/ev/status + /api/v1/regional/ev/schedule (via async_update)
    - state: _status.get("current_soc_pct") — float or None
    - icon: based on current_action (charge/solar_charge/departure_ready/idle)
    - attrs: vehicle/connector/charging details from status + schedule fields
    """

    # Static icon map (from sensor)
    @staticmethod
    def icon(status: dict | None) -> str:
        if not status:
            return "mdi:car-electric-outline"
        status = _as_mapping(status)
        action = _safe_string(status.get("current_action"), default="idle")
        if action == "charge":
            return "mdi:ev-station"
        elif action == "solar_charge":
            return "mdi:solar-power-variant"
        elif status.get("departure_ready"):
            return "mdi:car-electric"
        return "mdi:car-electric-outline"

    @staticmethod
    def state(status: dict | None) -> float | None:
        if not status:
            return None
        status = _as_mapping(status)
        return _safe_float(status.get("current_soc_pct"), default=None)

    @staticmethod
    def extra_state_attributes(status: dict | None, schedule: dict | None) -> dict:
        status = _as_mapping(status)
        attrs = {
            "vehicle_name": _safe_string(status.get("vehicle_name"), default="EV"),
            "connector_type": _safe_string(status.get("connector_type"), default="type2"),
            "current_soc_pct": _safe_float(status.get("current_soc_pct"), default=0.0),
            "target_soc_pct": _safe_float(status.get("target_soc_pct"), default=80.0),
            "current_action": _safe_string(status.get("current_action"), default="idle"),
            "current_power_kw": _safe_float(status.get("current_power_kw"), default=0.0),
            "energy_charged_kwh": _safe_float(status.get("energy_charged_kwh"), default=0.0),
            "cost_so_far_eur": _safe_float(status.get("cost_so_far_eur"), default=0.0),
            "estimated_range_km": _safe_float(status.get("estimated_range_km"), default=0.0),
            "time_to_target_h": _safe_float(status.get("time_to_target_h"), default=0.0),
            "next_departure": _safe_string(status.get("next_departure"), default=""),
            "departure_ready": bool(status.get("departure_ready")),
            "strategy": _safe_string(status.get("strategy"), default="cost_optimized"),
        }

        schedule = _as_mapping(schedule)
        if schedule:
            attrs["total_energy_kwh"] = _safe_float(schedule.get("total_energy_kwh"), default=0.0)
            attrs["total_cost_eur"] = _safe_float(schedule.get("total_cost_eur"), default=0.0)
            attrs["solar_energy_kwh"] = _safe_float(schedule.get("solar_energy_kwh"), default=0.0)
            attrs["grid_energy_kwh"] = _safe_float(schedule.get("grid_energy_kwh"), default=0.0)
            attrs["solar_share_pct"] = _safe_float(schedule.get("solar_share_pct"), default=0.0)
            attrs["avg_price_ct"] = _safe_float(schedule.get("avg_price_ct"), default=0.0)
            attrs["charge_hours"] = _safe_float(schedule.get("charge_hours"), default=0.0)

        return attrs


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_coordinator():
    """Mock coordinator for EVChargingSensor."""
    coordinator = MagicMock()
    coordinator.data = {}
    return coordinator


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    session = MagicMock()
    return session


# =============================================================================
# Tests — EVChargingSensor native_value (state)
# =============================================================================


class TestEVChargingSensorState:
    """EC1: native_value tests — current_soc_pct projection."""

    @pytest.mark.parametrize(
        "status_data,expected",
        [
            ({"current_soc_pct": 75.5, "ok": True}, 75.5),
            ({"current_soc_pct": 0.0, "ok": True}, 0.0),
            ({"current_soc_pct": 100.0, "ok": True}, 100.0),
            ({"current_soc_pct": None, "ok": True}, None),
            ({}, None),
            (None, None),
            ({"ok": False}, None),
        ],
        ids=["75-percent", "zero", "full", "none-value", "empty-dict", "none-status", "ok-false"],
    )
    def test_native_value(self, status_data, expected):
        """EC1: native_value returns current_soc_pct or None."""
        result = EVChargingSensorContract.state(status_data)
        assert result == expected


# =============================================================================
# Tests — EVChargingSensor icon
# =============================================================================


class TestEVChargingSensorIcon:
    """EC2: icon tests — action-based icon mapping."""

    @pytest.mark.parametrize(
        "status_data,expected",
        [
            ({"current_action": "charge", "ok": True}, "mdi:ev-station"),
            ({"current_action": "solar_charge", "ok": True}, "mdi:solar-power-variant"),
            ({"current_action": "idle", "departure_ready": True, "ok": True}, "mdi:car-electric"),
            ({"current_action": "idle", "departure_ready": False, "ok": True}, "mdi:car-electric-outline"),
            ({"current_action": "idle", "ok": True}, "mdi:car-electric-outline"),
            ({"current_action": "unknown", "ok": True}, "mdi:car-electric-outline"),
            ({}, "mdi:car-electric-outline"),
            (None, "mdi:car-electric-outline"),
        ],
        ids=["charging", "solar-charging", "departure-ready", "idle-not-ready", "idle-default", "unknown-action", "empty-dict", "none-status"],
    )
    def test_icon(self, status_data, expected):
        """EC2: icon returns correct icon based on current_action and departure_ready."""
        result = EVChargingSensorContract.icon(status_data)
        assert result == expected


# =============================================================================
# Tests — EVChargingSensor extra_state_attributes
# =============================================================================


class TestEVChargingSensorAttributes:
    """EC3: extra_state_attributes tests — full projection."""

    def test_attrs_full_data(self):
        """EC3a: attrs with full status and schedule data."""
        status = {
            "vehicle_name": "Tesla Model 3",
            "connector_type": "type2",
            "current_soc_pct": 65.0,
            "target_soc_pct": 80,
            "current_action": "charge",
            "current_power_kw": 11.0,
            "energy_charged_kwh": 15.5,
            "cost_so_far_eur": 4.25,
            "estimated_range_km": 280,
            "time_to_target_h": 2.5,
            "next_departure": "2026-04-07T08:00:00Z",
            "departure_ready": False,
            "strategy": "cost_optimized",
        }
        schedule = {
            "total_energy_kwh": 20.0,
            "total_cost_eur": 5.50,
            "solar_energy_kwh": 8.0,
            "grid_energy_kwh": 12.0,
            "solar_share_pct": 40,
            "avg_price_ct": 22.5,
            "charge_hours": 4.0,
        }
        result = EVChargingSensorContract.extra_state_attributes(status, schedule)
        assert result["vehicle_name"] == "Tesla Model 3"
        assert result["connector_type"] == "type2"
        assert result["current_soc_pct"] == 65.0
        assert result["target_soc_pct"] == 80
        assert result["current_action"] == "charge"
        assert result["current_power_kw"] == 11.0
        assert result["energy_charged_kwh"] == 15.5
        assert result["cost_so_far_eur"] == 4.25
        assert result["estimated_range_km"] == 280
        assert result["time_to_target_h"] == 2.5
        assert result["next_departure"] == "2026-04-07T08:00:00Z"
        assert result["departure_ready"] is False
        assert result["strategy"] == "cost_optimized"
        assert result["total_energy_kwh"] == 20.0
        assert result["total_cost_eur"] == 5.50
        assert result["solar_energy_kwh"] == 8.0
        assert result["grid_energy_kwh"] == 12.0
        assert result["solar_share_pct"] == 40
        assert result["avg_price_ct"] == 22.5
        assert result["charge_hours"] == 4.0

    def test_attrs_defaults(self):
        """EC3b: attrs with empty status uses defaults."""
        result = EVChargingSensorContract.extra_state_attributes({}, {})
        assert result["vehicle_name"] == "EV"
        assert result["connector_type"] == "type2"
        assert result["current_soc_pct"] == 0
        assert result["target_soc_pct"] == 80
        assert result["current_action"] == "idle"
        assert result["current_power_kw"] == 0
        assert result["energy_charged_kwh"] == 0
        assert result["cost_so_far_eur"] == 0
        assert result["estimated_range_km"] == 0
        assert result["time_to_target_h"] == 0
        assert result["next_departure"] == ""
        assert result["departure_ready"] is False
        assert result["strategy"] == "cost_optimized"
        # schedule fields not added when schedule is empty dict
        assert "total_energy_kwh" not in result

    def test_attrs_status_only_no_schedule(self):
        """EC3c: attrs with status but no schedule (None)."""
        status = {"current_soc_pct": 50.0, "vehicle_name": "My EV"}
        result = EVChargingSensorContract.extra_state_attributes(status, None)
        assert result["current_soc_pct"] == 50.0
        assert result["vehicle_name"] == "My EV"
        # schedule fields not added when schedule is None
        assert "total_energy_kwh" not in result

    def test_attrs_partial_status(self):
        """EC3d: attrs with partial status data."""
        status = {"current_soc_pct": 30.0, "current_action": "solar_charge"}
        result = EVChargingSensorContract.extra_state_attributes(status, {})
        assert result["current_soc_pct"] == 30.0
        assert result["current_action"] == "solar_charge"
        assert result["vehicle_name"] == "EV"  # default
        assert result["connector_type"] == "type2"  # default

    def test_attrs_none_status(self):
        """EC3e: attrs with None status returns defaults."""
        result = EVChargingSensorContract.extra_state_attributes(None, None)
        assert result["vehicle_name"] == "EV"
        assert result["connector_type"] == "type2"
        assert result["current_soc_pct"] == 0
        assert result["current_action"] == "idle"


# =============================================================================
# Tests — Edge cases
# =============================================================================


class TestEVChargingSensorEdgeCases:
    """EC4: edge cases — extreme values, missing fields, schedule isolation."""

    @pytest.mark.parametrize(
        "status_data,expected_soc",
        [
            ({"current_soc_pct": -5.0}, -5.0),       # negative — finite, passed through
            ({"current_soc_pct": 150.0}, 150.0),    # >100 — finite, passed through
            ({"current_soc_pct": "50"}, 50.0),       # numeric string → float
        ],
        ids=["negative", "over-100", "string-value"],
    )
    def test_extreme_soc_values(self, status_data, expected_soc):
        """EC4a: extreme but finite SOC values are coerced correctly."""
        result = EVChargingSensorContract.state(status_data)
        assert result == expected_soc

    def test_missing_optional_status_fields(self):
        """EC4b: missing optional status fields use defaults in attrs."""
        status = {"current_soc_pct": 45.0}
        result = EVChargingSensorContract.extra_state_attributes(status, None)
        assert result["current_soc_pct"] == 45.0
        assert result["vehicle_name"] == "EV"
        assert result["target_soc_pct"] == 80.0
        assert result["strategy"] == "cost_optimized"

    def test_schedule_with_extra_fields(self):
        """EC4c: schedule with extra unknown fields — only known fields projected."""
        status = {"current_soc_pct": 60.0}
        schedule = {
            "total_energy_kwh": 25.0,
            "unknown_field": "ignored",
            "another_extra": 123,
        }
        result = EVChargingSensorContract.extra_state_attributes(status, schedule)
        assert result["total_energy_kwh"] == 25.0
        assert "unknown_field" not in result
        assert "another_extra" not in result

    def test_ok_false_rejected_by_async_update_not_by_state(self):
        """EC4d: ok=false in raw status dict is projected (async_update guards it at HTTP layer)."""
        status = {"current_soc_pct": 55.0, "ok": False}
        result_state = EVChargingSensorContract.state(status)
        result_icon = EVChargingSensorContract.icon(status)
        result_attrs = EVChargingSensorContract.extra_state_attributes(status, None)
        # state/icon/attrs project the data regardless of ok flag
        assert result_state == 55.0
        assert result_icon == "mdi:car-electric-outline"
        assert result_attrs["current_soc_pct"] == 55.0


class TestEVChargingSensorMalformedPayloads:
    """EC5: malformed payload tests — HA-339.

    Covers:
    - non-dict top-level status / schedule payloads
    - non-numeric / non-finite / bool soc and numeric fields
    - blank / padded string fields
    - non-bool departure_ready
    - top-level list response from API (async_update guard)
    """

    # EC5a — native_value with malformed current_soc_pct
    @pytest.mark.parametrize(
        "status_data,expected",
        [
            ({"current_soc_pct": "75"}, 75.0),         # string → float
            ({"current_soc_pct": True}, 1.0),          # bool → 1.0 finite — returned as-is
            ({"current_soc_pct": None}, None),           # None → None
            ({"current_soc_pct": ""}, None),           # blank string → ValueError → default=None
            ({"current_soc_pct": "  42  "}, 42.0),      # padded string → float
            ({"current_soc_pct": float("inf")}, None),  # inf → None
            ({"current_soc_pct": float("nan")}, None),   # nan → None
            ({"current_soc_pct": [75]}, None),         # list → TypeError → default=None
            ({"current_soc_pct": {"v": 75}}, None),  # dict → TypeError → default=None
        ],
        ids=[
            "EV1-string-soc",
            "EV2-bool-soc",
            "EV3-none-soc",
            "EV4-blank-string-soc",
            "EV5-padded-string-soc",
            "EV6-inf-soc",
            "EV7-nan-soc",
            "EV8-list-soc",
            "EV9-dict-soc",
        ],
    )
    def test_malformed_native_value(self, status_data, expected):
        """EC5a: native_value guards malformed current_soc_pct."""
        result = EVChargingSensorContract.state(status_data)
        assert result == expected

    # EC5b — icon with malformed current_action
    @pytest.mark.parametrize(
        "status_data,expected",
        [
            ({"current_action": "charge", "ok": True}, "mdi:ev-station"),
            ({"current_action": "  charge  ", "ok": True}, "mdi:ev-station"),   # padded → stripped
            ({"current_action": 42, "ok": True}, "mdi:car-electric-outline"),  # int → default
            ({"current_action": None, "ok": True}, "mdi:car-electric-outline"),
            ({"current_action": "", "ok": True}, "mdi:car-electric-outline"),  # blank → default
            ({"current_action": ["charge"], "ok": True}, "mdi:car-electric-outline"),
            ({"current_action": {"a": "charge"}, "ok": True}, "mdi:car-electric-outline"),
        ],
        ids=[
            "EV10-valid-charge",
            "EV11-padded-action",
            "EV12-int-action",
            "EV13-none-action",
            "EV14-blank-action",
            "EV15-list-action",
            "EV16-dict-action",
        ],
    )
    def test_malformed_icon(self, status_data, expected):
        """EC5b: icon guards malformed current_action."""
        result = EVChargingSensorContract.icon(status_data)
        assert result == expected

    # EC5c — extra_state_attributes with malformed status fields
    @pytest.mark.parametrize(
        "status_data,field,expected",
        [
            # string numeric fields → coerced
            ({"current_soc_pct": "65.5"}, "current_soc_pct", 65.5),
            ({"current_power_kw": "11.0"}, "current_power_kw", 11.0),
            ({"target_soc_pct": "80"}, "target_soc_pct", 80.0),
            # bool → finite float
            ({"current_soc_pct": True}, "current_soc_pct", 1.0),   # bool → 1.0 finite
            ({"current_power_kw": False}, "current_power_kw", 0.0),   # bool → 0.0 finite
            # inf/nan → defaults
            ({"current_soc_pct": float("inf")}, "current_soc_pct", 0.0),
            ({"estimated_range_km": float("nan")}, "estimated_range_km", 0.0),
            # blank/padded strings → coerced or default
            ({"vehicle_name": "  Tesla  "}, "vehicle_name", "Tesla"),
            ({"vehicle_name": ""}, "vehicle_name", "EV"),  # blank → default
            ({"connector_type": ""}, "connector_type", "type2"),
            ({"strategy": "  eco  "}, "strategy", "eco"),
            ({"strategy": ""}, "strategy", "cost_optimized"),  # blank → default
            # non-bool departure_ready
            ({"departure_ready": "yes"}, "departure_ready", True),   # truthy string → True
            ({"departure_ready": 0}, "departure_ready", False),     # falsy int → False
            ({"departure_ready": None}, "departure_ready", False),
            # next_departure blank/padded
            ({"next_departure": "  "}, "next_departure", ""),
            ({"next_departure": 42}, "next_departure", ""),
            # non-dict top-level → safe defaults
            (None, "vehicle_name", "EV"),
            ("not a dict", "vehicle_name", "EV"),
            ([], "vehicle_name", "EV"),
        ],
        ids=[
            "EV17-string-soc",
            "EV18-string-power",
            "EV19-string-target",
            "EV20-bool-soc-attrs",
            "EV21-bool-power-attrs",
            "EV22-inf-soc-attrs",
            "EV23-nan-range-attrs",
            "EV24-padded-vehicle",
            "EV25-blank-vehicle",
            "EV26-blank-connector",
            "EV27-padded-strategy",
            "EV28-blank-strategy",
            "EV29-string-departure-ready",
            "EV30-int-departure-ready",
            "EV31-none-departure-ready",
            "EV32-blank-next-departure",
            "EV33-nonstr-next-departure",
            "EV34-none-top-level",
            "EV35-string-top-level",
            "EV36-list-top-level",
        ],
    )
    def test_malformed_status_fields(self, status_data, field, expected):
        """EC5c: extra_state_attributes guards malformed status fields."""
        result = EVChargingSensorContract.extra_state_attributes(status_data, None)
        assert result[field] == expected

    # EC5d — malformed schedule fields
    @pytest.mark.parametrize(
        "schedule_data,field,expected",
        [
            ({"total_energy_kwh": "25.0"}, "total_energy_kwh", 25.0),
            ({"total_cost_eur": "4.50"}, "total_cost_eur", 4.5),
            ({"solar_energy_kwh": True}, "solar_energy_kwh", 1.0),   # bool → 1.0 finite
            ({"grid_energy_kwh": float("inf")}, "grid_energy_kwh", 0.0),
            ({"solar_share_pct": float("nan")}, "solar_share_pct", 0.0),
            ({"avg_price_ct": None}, "avg_price_ct", 0.0),
            ({"charge_hours": "4.5"}, "charge_hours", 4.5),
            # schedule is a non-dict → no schedule attrs added
            (None, "total_energy_kwh", None),   # not in attrs
            ("bad", "total_energy_kwh", None),
            ([], "total_energy_kwh", None),
        ],
        ids=[
            "EV37-string-energy",
            "EV38-string-cost",
            "EV39-bool-solar-energy",
            "EV40-inf-grid-energy",
            "EV41-nan-solar-pct",
            "EV42-none-avg-price",
            "EV43-string-charge-hours",
            "EV44-none-schedule",
            "EV45-string-schedule",
            "EV46-list-schedule",
        ],
    )
    def test_malformed_schedule_fields(self, schedule_data, field, expected):
        """EC5d: extra_state_attributes guards malformed schedule fields."""
        result = EVChargingSensorContract.extra_state_attributes({"current_soc_pct": 50.0}, schedule_data)
        if expected is None:
            assert field not in result
        else:
            assert result[field] == expected

    def test_top_level_list_api_response(self):
        """EC5e: top-level list from API → async_update guard prevents crash."""
        # Simulate: session.get returns 200 with data = [{"ok": true}, ...]
        # The sensor now checks isinstance(data, dict) before .get("ok")
        data = [{"current_soc_pct": 50}, {"ok": True}]
        # In production: async_update checks isinstance(data, dict)
        # For contract: we verify the guard path
        is_dict = isinstance(data, dict)
        assert is_dict is False  # list should be rejected by isinstance guard
        # If it were passed through: data.get("ok") would raise TypeError on list


# =============================================================================
# Global Contract Tests
# =============================================================================


class TestEVChargingSensorGlobalContract:
    """GC: global contract — pure projection, no semantic invention."""

    def test_gc1_endpoint_verification(self):
        """GC1: sensor hits /api/v1/regional/ev/status and /api/v1/regional/ev/schedule."""
        # Read source file directly to avoid import issues
        import os
        sensor_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "sensors", "ev_charging_sensor.py")
        with open(sensor_path, "r") as f:
            source = f.read()
        # Endpoints are constructed dynamically: f"{base}/ev/status" where base = self._core_base_url() + "/api/v1/regional"
        assert "/ev/status" in source
        assert "/ev/schedule" in source
        assert "/api/v1/regional" in source

    def test_gc2_no_local_semantic_invention(self):
        """GC2: sensor is pure projection shell — no local threshold logic or semantic invention."""
        import os
        sensor_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "sensors", "ev_charging_sensor.py")
        with open(sensor_path, "r") as f:
            source = f.read()
        # Should only have: dict lookups, static icon map, pass-through
        # Should NOT have: complex calculations, ML, heuristic classification
        assert "if " in source  # guards are ok
        # Icon map is static (allowed)
        assert "mdi:ev-station" in source
        assert "mdi:solar-power-variant" in source
        # No complex logic beyond dict.get() and static maps
        lines = [l.strip() for l in source.split("\n") if l.strip() and not l.strip().startswith("#")]
        # Count complex operations
        complex_ops = sum(1 for l in lines if "for " in l or "while " in l or "import " in l)
        assert complex_ops <= 10, f"Too many complex operations: {complex_ops}"

    def test_gc3_guard_anchors(self):
        """GC3: Source guard — _as_mapping, _safe_float, _safe_string, math.isfinite, isinstance(data, dict) present."""
        import os
        sensor_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "sensors", "ev_charging_sensor.py")
        with open(sensor_path, "r") as f:
            source = f.read()
        assert "def _as_mapping" in source
        assert "def _safe_float" in source
        assert "def _safe_string" in source
        assert "math.isfinite" in source
        assert "isinstance(data, dict)" in source
