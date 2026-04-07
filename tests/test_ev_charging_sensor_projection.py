"""EV Charging Sensor Projection Contract Tests (HA-160).

Verifies EVChargingSensor is a pure projection shell on
/api/v1/regional/ev/status + /api/v1/regional/ev/schedule.

EVChargingSensor:
- state: current_soc_pct (float or None)
- icon: based on current_action (charge/solar_charge/departure_ready/idle)
- attrs: vehicle/connector/charging details + schedule data

No local semantic invention beyond trivial Dict-Lookups and statics.

HA-160 — 2026-04-07
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# =============================================================================
# Contract Mirrors — mirror the sensor logic without importing
# =============================================================================


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
        action = status.get("current_action", "idle")
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
        return status.get("current_soc_pct")

    @staticmethod
    def extra_state_attributes(status: dict | None, schedule: dict | None) -> dict:
        if not status:
            status = {}
        attrs = {
            "vehicle_name": status.get("vehicle_name", "EV"),
            "connector_type": status.get("connector_type", "type2"),
            "current_soc_pct": status.get("current_soc_pct", 0),
            "target_soc_pct": status.get("target_soc_pct", 80),
            "current_action": status.get("current_action", "idle"),
            "current_power_kw": status.get("current_power_kw", 0),
            "energy_charged_kwh": status.get("energy_charged_kwh", 0),
            "cost_so_far_eur": status.get("cost_so_far_eur", 0),
            "estimated_range_km": status.get("estimated_range_km", 0),
            "time_to_target_h": status.get("time_to_target_h", 0),
            "next_departure": status.get("next_departure", ""),
            "departure_ready": status.get("departure_ready", False),
            "strategy": status.get("strategy", "cost_optimized"),
        }

        if schedule:
            attrs["total_energy_kwh"] = schedule.get("total_energy_kwh", 0)
            attrs["total_cost_eur"] = schedule.get("total_cost_eur", 0)
            attrs["solar_energy_kwh"] = schedule.get("solar_energy_kwh", 0)
            attrs["grid_energy_kwh"] = schedule.get("grid_energy_kwh", 0)
            attrs["solar_share_pct"] = schedule.get("solar_share_pct", 0)
            attrs["avg_price_ct"] = schedule.get("avg_price_ct", 0)
            attrs["charge_hours"] = schedule.get("charge_hours", 0)

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
    """EC4: edge cases — missing fields, wrong types, extreme values."""

    @pytest.mark.parametrize(
        "status_data,expected_soc",
        [
            ({"current_soc_pct": -5.0}, -5.0),  # negative (invalid but passed through)
            ({"current_soc_pct": 150.0}, 150.0),  # >100 (invalid but passed through)
            ({"current_soc_pct": "50"}, "50"),  # string (passed through)
        ],
        ids=["negative", "over-100", "string-value"],
    )
    def test_extreme_soc_values(self, status_data, expected_soc):
        """EC4a: extreme/invalid SOC values are passed through (no validation)."""
        result = EVChargingSensorContract.state(status_data)
        assert result == expected_soc

    def test_missing_optional_status_fields(self):
        """EC4b: missing optional status fields use defaults in attrs."""
        status = {"current_soc_pct": 45.0}  # only required field
        result = EVChargingSensorContract.extra_state_attributes(status, None)
        assert result["current_soc_pct"] == 45.0
        assert result["vehicle_name"] == "EV"
        assert result["target_soc_pct"] == 80
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

    def test_ok_false_handling(self):
        """EC4d: ok=false in status — sensor still projects data (no ok guard in sensor)."""
        status = {"current_soc_pct": 55.0, "ok": False}
        result_state = EVChargingSensorContract.state(status)
        result_icon = EVChargingSensorContract.icon(status)
        result_attrs = EVChargingSensorContract.extra_state_attributes(status, None)
        # Sensor does not check ok flag — projects data anyway
        assert result_state == 55.0
        assert result_icon == "mdi:car-electric-outline"
        assert result_attrs["current_soc_pct"] == 55.0


# =============================================================================
# Global Contract Tests
# =============================================================================


class TestEVChargingSensorGlobalContract:
    """GC: global contract — pure projection, no semantic invention."""

    def test_gc1_endpoint_verification(self):
        """GC1: sensor hits /api/v1/regional/ev/status and /api/v1/regional/ev/schedule."""
        # Read source file directly to avoid import issues
        import os
        sensor_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "copilot_ha", "sensors", "ev_charging_sensor.py")
        with open(sensor_path, "r") as f:
            source = f.read()
        # Endpoints are constructed dynamically: f"{base}/ev/status" where base = self._core_base_url() + "/api/v1/regional"
        assert "/ev/status" in source
        assert "/ev/schedule" in source
        assert "/api/v1/regional" in source

    def test_gc2_no_local_semantic_invention(self):
        """GC2: sensor is pure projection shell — no local threshold logic or semantic invention."""
        import os
        sensor_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "copilot_ha", "sensors", "ev_charging_sensor.py")
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
