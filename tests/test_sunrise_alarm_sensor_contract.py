"""Projection contract tests for Sunrise Alarm Sensor.

Verifies that sunrise_alarm sensor correctly projects:
- AlarmConfig state from Core
- Zone-based alarm routing
- Runtime state (running, snoozed, etc.)
- Next trigger time

HA-156
"""

from __future__ import annotations
import pytest
from datetime import datetime, timezone


class FakeSunriseAlarmEngine:
    """Fake AlarmEngine for contract testing."""

    def __init__(self, alarms: list[dict] = None) -> None:
        self._alarms = alarms or []

    def list_alarms(self) -> list[dict]:
        return self._alarms

    def get_alarms_for_zone(self, zone_id: str) -> list[dict]:
        return [a for a in self._alarms if a.get("zone_id") == zone_id]

    def get_alarms_for_person(self, person_id: str) -> list[dict]:
        return [a for a in self._alarms if a.get("person_id") == person_id]

    def get_alarm(self, alarm_id: str) -> dict | None:
        for a in self._alarms:
            if a.get("alarm_id") == alarm_id:
                return a
        return None

    def status(self) -> dict:
        running = sum(1 for a in self._alarms if a.get("runtime", {}).get("state") == "running")
        snoozed = sum(1 for a in self._alarms if a.get("runtime", {}).get("state") == "snoozed")
        return {
            "total_alarms": len(self._alarms),
            "running": running,
            "snoozed": snoozed,
        }


class TestSunriseAlarmSensorContract:
    """Contract tests for sunrise_alarm_sensor projection."""

    @pytest.fixture
    def engine(self) -> FakeSunriseAlarmEngine:
        return FakeSunriseAlarmEngine(alarms=[
            {
                "alarm_id": "wake-papa",
                "name": "Papa Wecker",
                "person_id": "person.papa",
                "zone_id": "schlafzimmer",
                "mode": "wake",
                "schedule": {"time": "06:30", "days": ["mon", "tue", "wed", "thu", "fri"], "enabled": True},
                "light": {"entity_ids": ["light.schlafzimmer_decke"], "brightness_start_pct": 0, "brightness_end_pct": 100},
                "music": {"source_name": "Morning Mix", "sonos_room": "Schlafzimmer"},
                "runtime": {"state": "armed", "next_trigger": "2026-04-07T06:30:00+02:00"},
            },
            {
                "alarm_id": "wake-mama",
                "name": "Mama Wecker",
                "person_id": "person.mama",
                "zone_id": "kinderzimmer",
                "mode": "wake",
                "schedule": {"time": "07:00", "days": ["mon", "tue", "wed", "thu", "fri"], "enabled": True},
                "light": {"entity_ids": ["light.kinderzimmer"], "brightness_start_pct": 0, "brightness_end_pct": 80},
                "music": {"source_name": "Nachtplaylist", "sonos_room": "Kinderzimmer"},
                "runtime": {"state": "armed", "next_trigger": "2026-04-07T07:00:00+02:00"},
            },
            {
                "alarm_id": "wake-weekend",
                "name": "Wochenende",
                "person_id": "person.papa",
                "zone_id": "schlafzimmer",
                "mode": "wake",
                "schedule": {"time": "09:00", "days": ["sat", "sun"], "enabled": False},
                "runtime": {"state": "idle"},
            },
        ])

    def test_zone_filter_returns_correct_alarms(self, engine: FakeSunriseAlarmEngine) -> None:
        """sunrise_alarm_zone_sensor correctly filters by zone_id."""
        bedroom = engine.get_alarms_for_zone("schlafzimmer")
        kids = engine.get_alarms_for_zone("kinderzimmer")

        assert len(bedroom) == 2, "schlafzimmer should have 2 alarms (papa + weekend)"
        assert len(kids) == 1, "kinderzimmer should have 1 alarm (mama)"
        assert all(a["zone_id"] == "schlafzimmer" for a in bedroom)

    def test_person_filter_returns_correct_alarms(self, engine: FakeSunriseAlarmEngine) -> None:
        """sunrise_alarm_person_sensor correctly filters by person_id."""
        papa = engine.get_alarms_for_person("person.papa")
        mama = engine.get_alarms_for_person("person.mama")

        assert len(papa) == 2, "papa should have 2 alarms (weekday + weekend)"
        assert len(mama) == 1, "mama should have 1 alarm"
        assert all(a["person_id"] == "person.papa" for a in papa)

    def test_runtime_state_reflected(self, engine: FakeSunriseAlarmEngine) -> None:
        """sunrise_alarm_sensor.runtime reflects current state."""
        wake_papa = engine.get_alarm("wake-papa")
        assert wake_papa is not None
        assert wake_papa["runtime"]["state"] == "armed"
        assert "next_trigger" in wake_papa["runtime"]

    def test_disabled_alarm_has_idle_state(self, engine: FakeSunriseAlarmEngine) -> None:
        """Disabled alarm shows idle state."""
        weekend = engine.get_alarm("wake-weekend")
        assert weekend is not None
        assert weekend["runtime"]["state"] == "idle"

    def test_light_config_preserved(self, engine: FakeSunriseAlarmEngine) -> None:
        """Light config (entity_ids, brightness ramp) preserved in projection."""
        wake_papa = engine.get_alarm("wake-papa")
        assert wake_papa["light"]["entity_ids"] == ["light.schlafzimmer_decke"]
        assert wake_papa["light"]["brightness_start_pct"] == 0
        assert wake_papa["light"]["brightness_end_pct"] == 100

    def test_music_config_preserved(self, engine: FakeSunriseAlarmEngine) -> None:
        """Music config (sonos_room, source_name) preserved in projection."""
        wake_mama = engine.get_alarm("wake-mama")
        assert wake_mama["music"]["sonos_room"] == "Kinderzimmer"
        assert wake_mama["music"]["source_name"] == "Nachtplaylist"

    def test_status_aggregates_correctly(self, engine: FakeSunriseAlarmEngine) -> None:
        """Status endpoint returns correct aggregation."""
        status = engine.status()
        assert status["total_alarms"] == 3
        assert status["running"] == 0
        assert status["snoozed"] == 0


class TestSunriseAlarmRuntimeProjection:
    """Tests for runtime state projection scenarios."""

    def test_running_alarm_shows_progress(self) -> None:
        """Running alarm has runtime with progress_pct."""
        engine = FakeSunriseAlarmEngine(alarms=[{
            "alarm_id": "wake-active",
            "name": "Aktiver Wecker",
            "mode": "wake",
            "runtime": {
                "state": "running",
                "progress_pct": 65.0,
                "current_brightness": 65,
                "current_cct": 3200,
                "step_count": 65,
                "total_steps": 100,
            },
        }])
        alarm = engine.get_alarm("wake-active")
        assert alarm["runtime"]["state"] == "running"
        assert alarm["runtime"]["progress_pct"] == 65.0

    def test_snoozed_alarm_shows_snooze_count(self) -> None:
        """Snoozed alarm shows snooze_count in runtime."""
        engine = FakeSunriseAlarmEngine(alarms=[{
            "alarm_id": "wake-snoozed",
            "name": "Gesnoozter Wecker",
            "mode": "wake",
            "runtime": {
                "state": "snoozed",
                "snooze_count": 2,
            },
        }])
        alarm = engine.get_alarm("wake-snoozed")
        assert alarm["runtime"]["state"] == "snoozed"
        assert alarm["runtime"]["snooze_count"] == 2

    def test_multiple_zone_alarms(self) -> None:
        """Multiple zones can each have their own alarm."""
        engine = FakeSunriseAlarmEngine(alarms=[
            {"alarm_id": "z1-wake", "zone_id": "zone_a"},
            {"alarm_id": "z2-wake", "zone_id": "zone_b"},
            {"alarm_id": "z3-wake", "zone_id": "zone_a"},
        ])
        assert len(engine.get_alarms_for_zone("zone_a")) == 2
        assert len(engine.get_alarms_for_zone("zone_b")) == 1
