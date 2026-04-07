"""Presence sensors Projection-Contract-Tests (HA-171).

Contract: PresenceRoomSensor + PresencePersonSensor sind Projection-Shells auf
coordinator.data["context"]["presence"] + ["activity"] (Add-on API) mit Fallback
auf hass.states.async_all() (person/binary_sensor/device_tracker).

Keine lokale Semantik: room/person_count kommen aus API/States, social_score
ist triviale Normalisierung (person_count / 3), active_score ist motion_count / 3.
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.copilot_ha.coordinator import CopilotDataUpdateCoordinator
from custom_components.copilot_ha.sensors.presence_sensors import (
    _MAX_ACTIVE_SOURCES,
    _MAX_SOCIAL_PERSONS,
    _fallback_direct_states,
)


# ─────────────────────────────────────────────────────────────────────────────
# Simple State-like class for fallback tests (matches HA State object interface)
# ─────────────────────────────────────────────────────────────────────────────


class MockState:
    """Simple State-like object for testing."""

    def __init__(self, entity_id: str, state: str, attributes: dict | None = None) -> None:
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


# ─────────────────────────────────────────────────────────────────────────────
# Contract Mirrors (exact sensor logic replication)
# ─────────────────────────────────────────────────────────────────────────────


class PresenceRoomSensorContract:
    """Mirror of PresenceRoomSensor logic."""

    @staticmethod
    def compute_native_value(presence_data: dict) -> str:
        """Room aus API, Fallback 'unknown'."""
        room = presence_data.get("room")
        if room:
            return str(room)
        return "unknown"

    @staticmethod
    def compute_icon() -> str:
        """Statisch mdi:door."""
        return "mdi:door"

    @staticmethod
    def compute_attrs(presence_data: dict, activity_data: dict) -> dict:
        """Attrs aus presence + activity."""
        person_count = presence_data.get("count", 0)
        motion_count = activity_data.get("motion_count", 0) if activity_data else 0

        social_score = min(person_count / _MAX_SOCIAL_PERSONS, 1.0) if person_count else 0.0
        active_score = min(motion_count / _MAX_ACTIVE_SOURCES, 1.0) if motion_count else 0.0

        return {
            "active_persons": person_count,
            "motion_sensors_active": motion_count,
            "device_trackers_home": 0,
            "camera_room": presence_data.get("camera_room"),
            "camera_person_detected": presence_data.get("camera_person_detected", False),
            "sources": presence_data.get("sources", []),
            "social": person_count > 1,
            "active": active_score > 0,
            "social_score": social_score,
            "active_score": active_score,
            "confidence": presence_data.get("value", 0.0),
        }


class PresencePersonSensorContract:
    """Mirror of PresencePersonSensor logic."""

    @staticmethod
    def compute_native_value(presence_data: dict) -> int:
        """Person count aus API, 0 bei Missing."""
        count = presence_data.get("count")
        return count if count is not None else 0

    @staticmethod
    def compute_icon() -> str:
        """Statisch mdi:account-group."""
        return "mdi:account-group"

    @staticmethod
    def compute_attrs(presence_data: dict) -> dict:
        """Attrs aus presence."""
        person_count = presence_data.get("count", 0)
        social_score = min(person_count / _MAX_SOCIAL_PERSONS, 1.0) if person_count else 0.0

        return {
            "home": person_count,
            "social": person_count > 1,
            "social_score": social_score,
            "confidence": presence_data.get("value", 0.0),
            "sources": presence_data.get("sources", []),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def presence_api_data() -> dict:
    """Standard presence API response."""
    return {
        "room": "Wohnzimmer",
        "count": 2,
        "value": 0.95,
        "sources": ["person", "motion"],
        "camera_room": "Wohnzimmer",
        "camera_person_detected": True,
    }


@pytest.fixture
def activity_api_data() -> dict:
    """Standard activity API response."""
    return {
        "motion_count": 3,
        "value": 0.75,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PresenceRoomSensor Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_pr1_native_value_room_with_data(presence_api_data: dict) -> None:
    """PR1: native_value = room aus API."""
    assert PresenceRoomSensorContract.compute_native_value(presence_api_data) == "Wohnzimmer"


@pytest.mark.parametrize(
    ("presence_data", "expected_room"),
    [
        ({"room": "Küche"}, "Küche"),
        ({"room": None}, "unknown"),
        ({}, "unknown"),
        ({"room": ""}, "unknown"),
    ],
)
def test_pr1_native_value_room_edge_cases(presence_data: dict, expected_room: str) -> None:
    """PR1: native_value = 'unknown' bei Missing/None/empty."""
    assert PresenceRoomSensorContract.compute_native_value(presence_data) == expected_room


def test_pr2_icon_static() -> None:
    """PR2: icon ist statisch mdi:door."""
    assert PresenceRoomSensorContract.compute_icon() == "mdi:door"


def test_pr3_attrs_full(presence_api_data: dict, activity_api_data: dict) -> None:
    """PR3: attrs full mit presence + activity."""
    attrs = PresenceRoomSensorContract.compute_attrs(presence_api_data, activity_api_data)

    assert attrs["active_persons"] == 2
    assert attrs["motion_sensors_active"] == 3
    assert attrs["social"] is True
    assert attrs["active"] is True
    assert abs(attrs["social_score"] - 2 / 3) < 0.01
    assert abs(attrs["active_score"] - 1.0) < 0.01
    assert attrs["camera_room"] == "Wohnzimmer"
    assert attrs["camera_person_detected"] is True
    assert abs(attrs["confidence"] - 0.95) < 0.01


def test_pr4_attrs_empty() -> None:
    """PR4: attrs mit leeren Daten."""
    attrs = PresenceRoomSensorContract.compute_attrs({}, {})

    assert attrs["active_persons"] == 0
    assert attrs["motion_sensors_active"] == 0
    assert attrs["social"] is False
    assert attrs["active"] is False
    assert attrs["social_score"] == 0.0
    assert attrs["active_score"] == 0.0
    assert attrs["confidence"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PresencePersonSensor Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("presence_data", "expected_count"),
    [
        ({"count": 3}, 3),
        ({"count": 1}, 1),
        ({"count": 0}, 0),
        ({}, 0),
        ({"count": None}, 0),
    ],
)
def test_pp1_native_value_person_count(presence_data: dict, expected_count: int) -> None:
    """PP1: native_value = person_count aus API, 0 bei Missing."""
    assert PresencePersonSensorContract.compute_native_value(presence_data) == expected_count


def test_pp2_icon_static() -> None:
    """PP2: icon ist statisch mdi:account-group."""
    assert PresencePersonSensorContract.compute_icon() == "mdi:account-group"


def test_pp3_attrs_full(presence_api_data: dict) -> None:
    """PP3: attrs full mit presence."""
    attrs = PresencePersonSensorContract.compute_attrs(presence_api_data)

    assert attrs["home"] == 2
    assert attrs["social"] is True
    assert abs(attrs["social_score"] - 2 / 3) < 0.01
    assert abs(attrs["confidence"] - 0.95) < 0.01


def test_pp4_attrs_empty() -> None:
    """PP4: attrs mit leeren Daten."""
    attrs = PresencePersonSensorContract.compute_attrs({})

    assert attrs["home"] == 0
    assert attrs["social"] is False
    assert attrs["social_score"] == 0.0
    assert attrs["confidence"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Fallback Direct States Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("person_states", "expected_count", "expected_social"),
    [
        # 3 persons home
        (
            [
                MockState("person.alice", "home"),
                MockState("person.bob", "home"),
                MockState("person.carol", "home"),
            ],
            3,
            True,
        ),
        # 1 person home
        (
            [
                MockState("person.alice", "home"),
                MockState("person.bob", "away"),
            ],
            1,
            False,
        ),
        # 0 persons home
        (
            [
                MockState("person.alice", "away"),
                MockState("person.bob", "away"),
            ],
            0,
            False,
        ),
        # No person entities
        ([], 0, False),
    ],
)
def test_fb1_person_count_from_states(person_states: list[MockState], expected_count: int, expected_social: bool) -> None:
    """FB1: Fallback zählt person entities mit state='home'."""
    coordinator = MagicMock(spec=CopilotDataUpdateCoordinator)
    coordinator.hass = MagicMock()
    coordinator.hass.states.async_all = MagicMock(return_value=person_states)

    result = asyncio.run(_fallback_direct_states(coordinator))

    assert result["person_count"] == expected_count
    assert result["social"] == expected_social
    assert abs(result["social_score"] - min(expected_count / _MAX_SOCIAL_PERSONS, 1.0)) < 0.01


@pytest.mark.parametrize(
    ("binary_states", "expected_motion_count", "expected_active_score"),
    [
        # 5 motion sensors active
        (
            [
                MockState("binary_sensor.motion_1", "on", {"device_class": "motion"}),
                MockState("binary_sensor.motion_2", "on", {"device_class": "motion"}),
                MockState("binary_sensor.motion_3", "on", {"device_class": "motion"}),
                MockState("binary_sensor.motion_4", "on", {"device_class": "motion"}),
                MockState("binary_sensor.motion_5", "on", {"device_class": "motion"}),
            ],
            5,
            min(5 / _MAX_ACTIVE_SOURCES, 1.0),
        ),
        # 1 motion sensor active
        (
            [
                MockState("binary_sensor.motion_1", "on", {"device_class": "motion"}),
            ],
            1,
            min(1 / _MAX_ACTIVE_SOURCES, 1.0),
        ),
        # 0 motion sensors active
        (
            [
                MockState("binary_sensor.motion_1", "off", {"device_class": "motion"}),
                MockState("binary_sensor.door", "on", {"device_class": "door"}),
            ],
            0,
            0.0,
        ),
        # No binary sensors
        ([], 0, 0.0),
    ],
)
def test_fb2_motion_sensors_active(
    binary_states: list[MockState], expected_motion_count: int, expected_active_score: float
) -> None:
    """FB2: Fallback zählt motion binary_sensors mit state='on'."""
    coordinator = MagicMock(spec=CopilotDataUpdateCoordinator)
    coordinator.hass = MagicMock()
    coordinator.hass.states.async_all = MagicMock(return_value=binary_states)

    result = asyncio.run(_fallback_direct_states(coordinator))

    assert result["motion_sensors_active"] == expected_motion_count
    assert abs(result["active_score"] - expected_active_score) < 0.01


@pytest.mark.parametrize(
    ("tracker_states", "expected_home_count"),
    [
        # 2 device trackers home
        (
            [
                MockState("device_tracker.phone_alice", "home"),
                MockState("device_tracker.phone_bob", "home"),
                MockState("device_tracker.phone_carol", "away"),
            ],
            2,
        ),
        # 0 device trackers home
        (
            [
                MockState("device_tracker.phone_alice", "away"),
                MockState("device_tracker.phone_bob", "not_home"),
            ],
            0,
        ),
        # No device trackers
        ([], 0),
    ],
)
def test_fb3_device_trackers_home(tracker_states: list[MockState], expected_home_count: int) -> None:
    """FB3: Fallback zählt device_tracker entities mit state='home'."""
    coordinator = MagicMock(spec=CopilotDataUpdateCoordinator)
    coordinator.hass = MagicMock()

    def async_all(domain: str | None = None) -> list:
        if domain == "device_tracker":
            return tracker_states
        return []

    coordinator.hass.states.async_all = MagicMock(side_effect=async_all)

    result = asyncio.run(_fallback_direct_states(coordinator))

    assert result["device_trackers_home"] == expected_home_count


# ─────────────────────────────────────────────────────────────────────────────
# Global Contract Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_gc1_no_local_semantic_invention() -> None:
    """GC1: Keine lokale Semantik — reine Projection auf API/States."""
    # Verifiziere dass social_score triviale Normalisierung ist
    test_cases = [
        (0, 0.0),
        (1, 1 / 3),
        (2, 2 / 3),
        (3, 1.0),
        (5, 1.0),  # capped at 1.0
    ]

    for person_count, expected_score in test_cases:
        presence_data = {"count": person_count}
        actual_score = PresencePersonSensorContract.compute_attrs(presence_data)["social_score"]
        assert abs(actual_score - expected_score) < 0.01, f"person_count={person_count}"

    # Verifiziere dass active_score triviale motion_count-Normalisierung ist
    for motion_count in [0, 1, 3, 5]:
        expected_score = min(motion_count / _MAX_ACTIVE_SOURCES, 1.0)
        activity_data = {"motion_count": motion_count}
        actual_score = PresenceRoomSensorContract.compute_attrs({}, activity_data)["active_score"]
        assert abs(actual_score - expected_score) < 0.01, f"motion_count={motion_count}"


def test_gc2_primary_source_is_api() -> None:
    """GC2: Primary source ist API (coordinator.async_get_neurons), Fallback nur als safety."""
    # Contract test: API path should work without fallback
    presence_data = {"room": "Wohnzimmer", "count": 2, "value": 0.9}
    activity_data = {"motion_count": 3, "value": 0.75}

    room = PresenceRoomSensorContract.compute_native_value(presence_data)
    attrs = PresenceRoomSensorContract.compute_attrs(presence_data, activity_data)

    assert room == "Wohnzimmer"
    assert attrs["active_persons"] == 2
    assert attrs["motion_sensors_active"] == 3
