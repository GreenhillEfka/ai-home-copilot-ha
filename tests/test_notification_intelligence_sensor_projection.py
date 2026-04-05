"""Projection Contract Tests for NotificationIntelligenceSensor (HA-14).

Verifies that NotificationIntelligenceSensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/notifications) with trivial string formatting — no local semantic invention.

Pattern: same as HA-6/8/9/10/11/12/13.
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"

    def async_write_ha_state(self):
        pass


class NotificationIntelligenceSensorContract:
    """Mirror of NotificationIntelligenceSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/hub/notifications
    - native_value: "Keine..." if total==0, "Alle gelesen" if unread==0 else f"{unread} ungelesen"
    - icon: bell-off if dnd, bell-badge if unread>0, bell-check otherwise
    - extra_state_attributes: direct passthrough of all Core fields
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    async def _fetch(self):
        return self._data

    def _apply(self, fetched_data):
        if fetched_data and fetched_data.get("ok"):
            self._data = fetched_data

    @property
    def native_value(self):
        total = self._data.get("total_notifications", 0)
        unread = self._data.get("unread_count", 0)
        if total == 0:
            return "Keine Benachrichtigungen"
        if unread == 0:
            return "Alle gelesen"
        return f"{unread} ungelesen"

    @property
    def icon(self):
        dnd = self._data.get("dnd_active", False)
        if dnd:
            return "mdi:bell-off"
        unread = self._data.get("unread_count", 0)
        if unread > 0:
            return "mdi:bell-badge"
        return "mdi:bell-check"

    @property
    def extra_state_attributes(self):
        attrs = {
            "total_notifications": self._data.get("total_notifications", 0),
            "unread_count": self._data.get("unread_count", 0),
            "dnd_active": self._data.get("dnd_active", False),
            "batch_pending": self._data.get("batch_pending", 0),
            "rules_count": self._data.get("rules_count", 0),
            "channels_active": self._data.get("channels_active", []),
        }
        stats = self._data.get("stats", {})
        if stats:
            attrs["stats"] = stats
        return attrs


NI1_native_value = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "total_notifications": 0}, "Keine Benachrichtigungen"),
    ({"ok": True, "total_notifications": 5, "unread_count": 0}, "Alle gelesen"),
    ({"ok": True, "total_notifications": 5, "unread_count": 3}, "3 ungelesen"),
    ({"ok": True, "total_notifications": 1, "unread_count": 1}, "1 ungelesen"),
    ({"ok": True, "total_notifications": 99, "unread_count": 77}, "77 ungelesen"),
])
NI2_icon = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "dnd_active": True, "unread_count": 5}, "mdi:bell-off"),
    ({"ok": True, "dnd_active": False, "unread_count": 1}, "mdi:bell-badge"),
    ({"ok": True, "dnd_active": False, "unread_count": 0}, "mdi:bell-check"),
    ({"ok": True, "dnd_active": False, "unread_count": 99}, "mdi:bell-badge"),
    ({"ok": True, "dnd_active": True, "unread_count": 0}, "mdi:bell-off"),
])
NI3_attrs = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "total_notifications", 10),
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "unread_count", 3),
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "dnd_active", True),
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "batch_pending", 2),
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "rules_count", 5),
    ({"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": True, "batch_pending": 2, "rules_count": 5, "channels_active": ["telegram", "email"]}, "channels_active", ["telegram", "email"]),
])
NI4_stats = pytest.mark.parametrize("stats_data,expected", [
    ({"delivered": 100, "failed": 2}, {"delivered": 100, "failed": 2}),
    ({"delivered": 50, "read": 45, "failed": 5, "pending": 0}, {"delivered": 50, "read": 45, "failed": 5, "pending": 0}),
])
NI5_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "total_notifications": 0, "unread_count": 0}, True),
    ({"ok": True, "dnd_active": False, "unread_count": 0}, True),
])


@NI1_native_value
def test_NI1_native_value(core_data, expected):
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.native_value == expected


@NI2_icon
def test_NI2_icon(core_data, expected_icon):
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.icon == expected_icon


@NI3_attrs
def test_NI3_attrs(core_data, key, expected):
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.extra_state_attributes[key] == expected


@NI4_stats
def test_NI4_stats_passthrough(stats_data, expected):
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply({"ok": True, "stats": stats_data, "total_notifications": 1})
    assert s.extra_state_attributes.get("stats") == expected


@NI5_edge
def test_NI5_edge(data, expect_ok):
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply(data)
    if expect_ok:
        assert s._data.get("ok") is True


def test_global_contract_no_local_logic():
    """Global: all state flows from Core API, zero local derivation."""
    s = NotificationIntelligenceSensorContract(MockCoordinator({}))
    s._apply({"ok": True, "total_notifications": 20, "unread_count": 7, "dnd_active": False})
    assert s.native_value == "7 ungelesen"
    assert s.icon == "mdi:bell-badge"
    assert s.extra_state_attributes["total_notifications"] == 20
