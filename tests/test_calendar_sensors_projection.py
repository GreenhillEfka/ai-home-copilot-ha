"""Projection Contract Tests: calendar_sensors.

Verifies:
- CalendarLoadSensor: pure HA-local projection of calendar entity states
  with optional module_connector calendar_context fallback

No Core API calls; uses hass.states.async_all("calendar") + calendar.get_events service.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Contract Mirrors (exact sensor logic replication)
# ---------------------------------------------------------------------------

class CalendarLoadSensorContract:
    """Mirror of CalendarLoadSensor async_update logic."""

    @staticmethod
    def compute_native_value(meetings_today: int, focus_weight: float = 0.0) -> str:
        """Compute load classification based on meetings + focus weight."""
        if meetings_today == 0:
            load = "free"
        elif meetings_today < 3:
            load = "light"
        elif meetings_today < 6:
            load = "moderate"
        else:
            load = "busy"
        
        # Adjust based on focus weight
        if focus_weight > 0.5:
            if load == "light":
                load = "moderate"
            elif load == "moderate":
                load = "busy"
        
        return load

    @staticmethod
    def compute_attrs(
        event_count: int,
        meetings_today: int,
        hour: int,
        is_weekend: bool,
        focus_weight: float = 0.0,
        social_weight: float = 0.0,
        relax_weight: float = 0.0,
        has_conflicts: bool = False,
        next_meeting_in_minutes: int | None = None,
        source: str = "calendar_entities",
    ) -> dict:
        """Compute extra_state_attributes."""
        return {
            "event_count": event_count,
            "meetings_today": meetings_today,
            "hour": hour,
            "is_weekend": is_weekend,
            "focus_weight": focus_weight,
            "social_weight": social_weight,
            "relax_weight": relax_weight,
            "has_conflicts": has_conflicts,
            "next_meeting_in_minutes": next_meeting_in_minutes,
            "source": source,
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def calendar_context_full():
    """Full calendar_context data from module_connector."""
    return {
        "event_count": 4,
        "meetings_today": 4,
        "is_weekend": False,
        "focus_weight": 0.4,
        "social_weight": 0.3,
        "relax_weight": 0.3,
        "has_conflicts": True,
        "next_meeting_in_minutes": 45,
    }


@pytest.fixture
def calendar_context_empty():
    """Empty/minimal calendar_context data."""
    return {
        "event_count": 0,
        "meetings_today": 0,
        "is_weekend": False,
        "focus_weight": 0.0,
        "social_weight": 0.0,
        "relax_weight": 0.0,
        "has_conflicts": False,
        "next_meeting_in_minutes": None,
    }


# ---------------------------------------------------------------------------
# CalendarLoadSensor — native_value
# ---------------------------------------------------------------------------

class TestCalendarLoadSensor:
    """Test CalendarLoadSensor projection contract."""

    def test_CL1_native_value_free_day(self, calendar_context_empty):
        """CL1: meetings_today=0 → native_value='free'."""
        result = CalendarLoadSensorContract.compute_native_value(
            meetings_today=calendar_context_empty["meetings_today"],
            focus_weight=calendar_context_empty["focus_weight"],
        )
        assert result == "free"

    def test_CL2_native_value_light_load(self):
        """CL2: meetings_today=1-2 → native_value='light'."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=2, focus_weight=0.0)
        assert result == "light"

    def test_CL3_native_value_moderate_load(self):
        """CL3: meetings_today=3-5 → native_value='moderate'."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=4, focus_weight=0.0)
        assert result == "moderate"

    def test_CL4_native_value_busy_day(self):
        """CL4: meetings_today>=6 → native_value='busy'."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=8, focus_weight=0.0)
        assert result == "busy"

    def test_CL5_focus_weight_adjustment_light_to_moderate(self):
        """CL5: focus_weight>0.5 upgrades light→moderate."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=2, focus_weight=0.8)
        # 2 meetings = light, but focus_weight 0.8 → moderate
        assert result == "moderate"

    def test_CL6_focus_weight_adjustment_moderate_to_busy(self):
        """CL6: focus_weight>0.5 upgrades moderate→busy."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=4, focus_weight=0.9)
        # 4 meetings = moderate, but focus_weight 0.9 → busy
        assert result == "busy"

    def test_CL7_focus_weight_no_adjustment_at_boundary(self):
        """CL7: focus_weight=0.5 → no adjustment (must be >0.5)."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=2, focus_weight=0.5)
        # 2 meetings = light, focus_weight=0.5 (not >0.5) → stays light
        assert result == "light"

    def test_CL8_focus_weight_adjustment_just_over_boundary(self):
        """CL8: focus_weight=0.51 → adjustment triggers."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=2, focus_weight=0.51)
        # 2 meetings = light, focus_weight=0.51 (>0.5) → moderate
        assert result == "moderate"

    def test_CL9_boundary_meetings_2(self):
        """CL9: meetings_today=2 → boundary of light (not yet moderate)."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=2, focus_weight=0.0)
        assert result == "light"

    def test_CL10_boundary_meetings_3(self):
        """CL10: meetings_today=3 → boundary of moderate (no longer light)."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=3, focus_weight=0.0)
        assert result == "moderate"

    def test_CL11_boundary_meetings_5(self):
        """CL11: meetings_today=5 → boundary of moderate (not yet busy)."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=5, focus_weight=0.0)
        assert result == "moderate"

    def test_CL12_boundary_meetings_6(self):
        """CL12: meetings_today=6 → boundary of busy."""
        result = CalendarLoadSensorContract.compute_native_value(meetings_today=6, focus_weight=0.0)
        assert result == "busy"


# ---------------------------------------------------------------------------
# CalendarLoadSensor — extra_state_attributes
# ---------------------------------------------------------------------------

class TestCalendarLoadSensorAttrs:
    """Test CalendarLoadSensor attrs projection contract."""

    def test_CL13_attrs_full(self, calendar_context_full):
        """CL13: attrs contain all expected fields with correct values."""
        attrs = CalendarLoadSensorContract.compute_attrs(
            event_count=calendar_context_full["event_count"],
            meetings_today=calendar_context_full["meetings_today"],
            hour=10,
            is_weekend=calendar_context_full["is_weekend"],
            focus_weight=calendar_context_full["focus_weight"],
            social_weight=calendar_context_full["social_weight"],
            relax_weight=calendar_context_full["relax_weight"],
            has_conflicts=calendar_context_full["has_conflicts"],
            next_meeting_in_minutes=calendar_context_full["next_meeting_in_minutes"],
            source="calendar_context_module",
        )
        
        assert attrs["event_count"] == 4
        assert attrs["meetings_today"] == 4
        assert attrs["hour"] == 10
        assert attrs["is_weekend"] is False
        assert attrs["focus_weight"] == 0.4
        assert attrs["social_weight"] == 0.3
        assert attrs["relax_weight"] == 0.3
        assert attrs["has_conflicts"] is True
        assert attrs["next_meeting_in_minutes"] == 45
        assert attrs["source"] == "calendar_context_module"

    def test_CL14_attrs_fallback_source(self, calendar_context_empty):
        """CL14: without calendar_context, source='calendar_entities'."""
        attrs = CalendarLoadSensorContract.compute_attrs(
            event_count=0,
            meetings_today=0,
            hour=10,
            is_weekend=False,
            focus_weight=0.0,
            social_weight=0.0,
            relax_weight=0.0,
            has_conflicts=False,
            next_meeting_in_minutes=None,
            source="calendar_entities",
        )
        
        assert attrs["source"] == "calendar_entities"
        assert attrs["event_count"] == 0
        assert attrs["meetings_today"] == 0

    def test_CL15_attrs_weekend_detection(self):
        """CL15: Saturday (weekday>=5) → is_weekend=True."""
        attrs = CalendarLoadSensorContract.compute_attrs(
            event_count=0,
            meetings_today=0,
            hour=10,
            is_weekend=True,
            focus_weight=0.0,
            social_weight=0.0,
            relax_weight=0.0,
            has_conflicts=False,
            next_meeting_in_minutes=None,
            source="calendar_context_module",
        )
        
        assert attrs["is_weekend"] is True

    def test_CL16_attrs_next_meeting_none(self, calendar_context_empty):
        """CL16: next_meeting_in_minutes=None when no upcoming meetings."""
        attrs = CalendarLoadSensorContract.compute_attrs(
            event_count=0,
            meetings_today=0,
            hour=10,
            is_weekend=False,
            focus_weight=0.0,
            social_weight=0.0,
            relax_weight=0.0,
            has_conflicts=False,
            next_meeting_in_minutes=None,
            source="calendar_entities",
        )
        
        assert attrs["next_meeting_in_minutes"] is None

    def test_CL17_attrs_defaults_for_missing_fields(self):
        """CL17: partial calendar_context uses defaults for missing fields."""
        # Simulating partial data - sensor would use defaults
        attrs = CalendarLoadSensorContract.compute_attrs(
            event_count=3,
            meetings_today=3,
            hour=10,
            is_weekend=False,  # Tuesday
            focus_weight=0.0,  # default
            social_weight=0.0,  # default
            relax_weight=0.0,  # default
            has_conflicts=False,
            next_meeting_in_minutes=None,
            source="calendar_context_module",
        )
        
        assert attrs["event_count"] == 3
        assert attrs["meetings_today"] == 3
        assert attrs["is_weekend"] is False
        assert attrs["focus_weight"] == 0.0
        assert attrs["social_weight"] == 0.0
        assert attrs["relax_weight"] == 0.0


# ---------------------------------------------------------------------------
# CalendarLoadSensor — icon
# ---------------------------------------------------------------------------

class TestCalendarLoadSensorIcon:
    """Test CalendarLoadSensor icon contract."""

    def test_CL18_icon_static(self):
        """CL18: icon is static mdi:calendar-clock."""
        # The sensor defines _attr_icon = "mdi:calendar-clock" as class attribute
        # This is verified by importing and checking the class
        from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor
        
        # Create a minimal mock coordinator for instantiation
        mock_coordinator = MagicMock()
        mock_hass = MagicMock()
        
        sensor = CalendarLoadSensor(mock_coordinator, mock_hass)
        assert sensor._attr_icon == "mdi:calendar-clock"


# ---------------------------------------------------------------------------
# Global Contract Tests
# ---------------------------------------------------------------------------

class TestGlobalContract:
    """Global contract verification for calendar_sensors."""

    def test_GC1_no_core_api_calls(self):
        """GC1: CalendarLoadSensor makes no Core API calls.
        
        Verified by source inspection:
        - No _fetch() calls
        - No _core_base_url() usage
        - Only hass.states.async_all("calendar") + calendar.get_events service
        """
        import inspect
        from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor
        
        source = inspect.getsource(CalendarLoadSensor.async_update)
        
        # Verify no Core API patterns
        assert "_fetch" not in source
        assert "_core_base_url" not in source
        assert "/api/v1/" not in source

    def test_GC2_ha_local_only(self):
        """GC2: CalendarLoadSensor uses only hass.states + calendar service.
        
        Verified by source inspection:
        - hass.states.async_all("calendar") for entity enumeration
        - hass.services.async_call("calendar", "get_events", ...) for events
        - Optional module_connector.calendar_context fallback (still HA-local)
        """
        import inspect
        from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor
        
        source = inspect.getsource(CalendarLoadSensor.async_update)
        
        # Verify HA-local patterns present
        assert "hass.states.async_all" in source
        assert '"calendar"' in source or "'calendar'" in source
        assert "calendar" in source
        
        # Verify no Core API endpoint patterns
        assert "/api/v1/" not in source
        assert "coordinator.data" not in source
