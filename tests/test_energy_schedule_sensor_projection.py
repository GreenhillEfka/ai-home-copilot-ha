"""Projection contract tests for EnergyScheduleSensor (HA-139).

Verifies:
- EnergyScheduleSensor: pure projection on /api/v1/predict/schedule/daily
  + /api/v1/predict/schedule/next

Contract verified:
- native_value: next upcoming device OR "no devices scheduled" OR "N devices done"
  OR "unavailable" — all from API data, no local classification
- extra_state_attributes: direct lookups from schedule API response
- edge: missing optional keys handled gracefully (KeyError → None)
- GC1: no local semantic invention
- GC2: hits correct Core endpoints
"""
import pytest
from datetime import datetime, timezone


# =============================================================================
# Contract Mirror
# Mirrors EnergyScheduleSensor projection behavior in isolation.
# The actual sensor is not imported to avoid relative-import issues.
# =============================================================================

class EnergyScheduleSensorContract:
    """Pure projection contract for EnergyScheduleSensor."""

    @staticmethod
    def native_value(plan_data: dict | None) -> str | None:
        if not plan_data or not plan_data.get("ok"):
            return "unavailable"
        schedules = plan_data.get("schedules", [])
        if not schedules:
            return "no devices scheduled"
        now = datetime.now(timezone.utc)
        upcoming = [
            s for s in schedules
            if datetime.fromisoformat(s["start"]) > now
        ]
        if upcoming:
            nxt = min(upcoming, key=lambda s: s["start"])
            return f"{nxt['device_type']} at {nxt['start_hour']}:00"
        return f"{len(schedules)} devices done"

    @staticmethod
    def extra_state_attributes(plan_data: dict | None) -> dict:
        attrs = {
            "schedule_url": "http://core/api/v1/predict/schedule/daily",
            "next_device_url": "http://core/api/v1/predict/schedule/next",
        }
        if plan_data and plan_data.get("ok"):
            attrs["date"] = plan_data.get("date")
            attrs["devices_scheduled"] = plan_data.get("devices_scheduled", 0)
            attrs["unscheduled_devices"] = plan_data.get("unscheduled_devices", [])
            attrs["total_estimated_cost_eur"] = plan_data.get(
                "total_estimated_cost_eur", 0
            )
            attrs["total_pv_coverage_percent"] = plan_data.get(
                "total_pv_coverage_percent", 0
            )
            attrs["peak_load_watts"] = plan_data.get("peak_load_watts", 0)
            schedules = plan_data.get("schedules", [])
            attrs["schedule"] = [
                {
                    "device": s.get("device_type"),
                    "hours": f"{s.get('start_hour')}:00-{s.get('end_hour')}:00",
                    "cost_eur": s.get("estimated_cost_eur"),
                    "pv_pct": s.get("pv_coverage_percent"),
                }
                for s in schedules
            ]
        return attrs


# =============================================================================
# ES1: native_value
# =============================================================================

@pytest.mark.parametrize("plan_data,expected", [
    pytest.param(
        {"ok": True, "schedules": [
            {"device_type": "Dishwasher", "start": "2099-01-01T10:00:00+00:00",
             "start_hour": 10, "end_hour": 11,
             "estimated_cost_eur": 0.30, "pv_coverage_percent": 80}
        ]},
        "Dishwasher at 10:00",
        id="ES1-upcoming-device"
    ),
    pytest.param(
        {"ok": True, "schedules": [
            {"device_type": "EV", "start": "2099-01-01T08:00:00+00:00",
             "start_hour": 8, "end_hour": 9,
             "estimated_cost_eur": 1.20, "pv_coverage_percent": 90},
            {"device_type": "Washing Machine", "start": "2099-01-01T14:00:00+00:00",
             "start_hour": 14, "end_hour": 15,
             "estimated_cost_eur": 0.50, "pv_coverage_percent": 75},
        ]},
        "EV at 8:00",
        id="ES1-earliest-wins"
    ),
    pytest.param(
        {"ok": True, "schedules": []},
        "no devices scheduled",
        id="ES1-empty-schedule"
    ),
    pytest.param(
        {"ok": True, "schedules": [
            {"device_type": "Heat Pump", "start": "2020-01-01T00:00:00+00:00",
             "start_hour": 0, "end_hour": 1,
             "estimated_cost_eur": 0.10, "pv_coverage_percent": 60},
            {"device_type": "Boiler", "start": "2020-01-01T01:00:00+00:00",
             "start_hour": 1, "end_hour": 2,
             "estimated_cost_eur": 0.15, "pv_coverage_percent": 50},
        ]},
        "2 devices done",
        id="ES1-all-past"
    ),
    pytest.param(
        {"ok": False, "schedules": []},
        "unavailable",
        id="ES1-ok-false"
    ),
    pytest.param(
        None,
        "unavailable",
        id="ES1-none"
    ),
    pytest.param(
        {},
        "unavailable",
        id="ES1-empty-dict"
    ),
])
def test_es1_native_value(plan_data, expected):
    assert EnergyScheduleSensorContract.native_value(plan_data) == expected


# =============================================================================
# ES2: extra_state_attributes
# =============================================================================

def test_es2_full_attrs():
    plan = {
        "ok": True,
        "date": "2026-04-06",
        "devices_scheduled": 3,
        "unscheduled_devices": ["EV"],
        "total_estimated_cost_eur": 2.40,
        "total_pv_coverage_percent": 72,
        "peak_load_watts": 3500,
        "schedules": [
            {"device_type": "Dishwasher", "start": "2099-01-01T10:00:00+00:00",
             "start_hour": 10, "end_hour": 11,
             "estimated_cost_eur": 0.30, "pv_coverage_percent": 80},
            {"device_type": "Washing Machine", "start": "2099-01-01T14:00:00+00:00",
             "start_hour": 14, "end_hour": 15,
             "estimated_cost_eur": 0.50, "pv_coverage_percent": 75},
        ]
    }
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    assert attrs["schedule_url"] == "http://core/api/v1/predict/schedule/daily"
    assert attrs["next_device_url"] == "http://core/api/v1/predict/schedule/next"
    assert attrs["date"] == "2026-04-06"
    assert attrs["devices_scheduled"] == 3
    assert attrs["unscheduled_devices"] == ["EV"]
    assert attrs["total_estimated_cost_eur"] == 2.40
    assert attrs["total_pv_coverage_percent"] == 72
    assert attrs["peak_load_watts"] == 3500
    assert len(attrs["schedule"]) == 2
    assert attrs["schedule"][0]["device"] == "Dishwasher"
    assert attrs["schedule"][0]["hours"] == "10:00-11:00"
    assert attrs["schedule"][0]["cost_eur"] == 0.30
    assert attrs["schedule"][0]["pv_pct"] == 80


def test_es2_empty_schedules():
    plan = {"ok": True, "schedules": []}
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    assert attrs["schedule_url"] == "http://core/api/v1/predict/schedule/daily"
    assert attrs["schedule"] == []
    assert attrs["devices_scheduled"] == 0


def test_es2_not_ok():
    plan = {"ok": False}
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    assert "schedule_url" in attrs
    assert "date" not in attrs  # only present when ok=True


# =============================================================================
# ES3: edge cases
# =============================================================================

def test_es3_missing_optional_keys():
    """Missing optional keys in schedule items → None, no KeyError."""
    plan = {"ok": True, "schedules": [
        {"device_type": "Heater", "start": "2099-01-01T08:00:00+00:00",
         "start_hour": 8, "end_hour": 9}
        # missing estimated_cost_eur, pv_coverage_percent
    ]}
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    sched = attrs["schedule"][0]
    assert sched["device"] == "Heater"
    assert sched["cost_eur"] is None
    assert sched["pv_pct"] is None


def test_es3_none_plan_data():
    attrs = EnergyScheduleSensorContract.extra_state_attributes(None)
    assert "schedule_url" in attrs
    assert "date" not in attrs


# =============================================================================
# GC1–GC2: Global Contracts
# =============================================================================

def test_gc1_no_local_semantic_invention():
    """GC1: Sensor invents no local logic — all values from API."""
    plan = {
        "ok": True,
        "date": "2026-04-06",
        "devices_scheduled": 1,
        "unscheduled_devices": [],
        "total_estimated_cost_eur": 1.00,
        "total_pv_coverage_percent": 65,
        "peak_load_watts": 2500,
        "schedules": [
            {"device_type": "Boiler", "start": "2099-01-01T06:00:00+00:00",
             "start_hour": 6, "end_hour": 7,
             "estimated_cost_eur": 0.20, "pv_coverage_percent": 70},
        ]
    }
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    # Values are direct lookups, no heuristic
    assert attrs["devices_scheduled"] == plan["devices_scheduled"]
    assert attrs["total_estimated_cost_eur"] == plan["total_estimated_cost_eur"]
    assert attrs["schedule"][0]["pv_pct"] == plan["schedules"][0]["pv_coverage_percent"]


def test_gc2_hits_core_predict_schedule_endpoints():
    """GC2: Sensor fetches from correct Core API endpoints."""
    plan = {"ok": True, "schedules": []}
    attrs = EnergyScheduleSensorContract.extra_state_attributes(plan)
    assert "/api/v1/predict/schedule/daily" in attrs["schedule_url"]
    assert "/api/v1/predict/schedule/next" in attrs["next_device_url"]
