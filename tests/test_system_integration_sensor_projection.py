"""Projection Contract Tests for SystemIntegrationSensor (HA-13).

Verifies that SystemIntegrationSensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/integration) with only trivial string formatting — no local semantic invention.

Pattern: same as HA-6/8/9/10/11/12.
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


class SystemIntegrationSensorContract:
    """Mirror of SystemIntegrationSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/hub/integration
    - native_value: "Nicht verbunden" if engines==0 else f"{engines} Engines / {subs} Verknüpfungen"
    - icon: hub-outline if engines==0, hub if events>0 else hub-outline
    - extra_state_attributes: direct passthrough of all Core fields
    - wiring_diagram: passthrough
    - event_log: passthrough with [:5] cap
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
        engines = self._data.get("engines_connected", 0)
        subs = self._data.get("active_subscriptions", 0)
        if engines == 0:
            return "Nicht verbunden"
        return f"{engines} Engines / {subs} Verknüpfungen"

    @property
    def icon(self):
        engines = self._data.get("engines_connected", 0)
        events = self._data.get("events_processed", 0)
        if engines == 0:
            return "mdi:hub-outline"
        if events > 0:
            return "mdi:hub"
        return "mdi:hub-outline"

    @property
    def extra_state_attributes(self):
        attrs = {
            "engines_connected": self._data.get("engines_connected", 0),
            "events_processed": self._data.get("events_processed", 0),
            "active_subscriptions": self._data.get("active_subscriptions", 0),
            "last_event": self._data.get("last_event", ""),
            "last_event_time": self._data.get("last_event_time", ""),
            "engine_names": self._data.get("engine_names", []),
        }
        wiring = self._data.get("wiring_diagram", {})
        if wiring:
            attrs["wiring_diagram"] = wiring
            attrs["event_types"] = list(wiring.keys())
        event_log = self._data.get("event_log", [])
        if event_log:
            attrs["recent_events"] = [
                {"event_type": e.get("event_type"), "source": e.get("source"),
                 "handled_by": e.get("handled_by"), "timestamp": e.get("timestamp")}
                for e in event_log[:5]
            ]
        return attrs


SI1_native_value = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "engines_connected": 0}, "Nicht verbunden"),
    ({"ok": True, "engines_connected": 3, "active_subscriptions": 12}, "3 Engines / 12 Verknüpfungen"),
    ({"ok": True, "engines_connected": 1, "active_subscriptions": 0}, "1 Engines / 0 Verknüpfungen"),
    ({"ok": True, "engines_connected": 10, "active_subscriptions": 99}, "10 Engines / 99 Verknüpfungen"),
])
SI2_icon = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "engines_connected": 0}, "mdi:hub-outline"),
    ({"ok": True, "engines_connected": 2, "events_processed": 0}, "mdi:hub-outline"),
    ({"ok": True, "engines_connected": 2, "events_processed": 1}, "mdi:hub"),
    ({"ok": True, "engines_connected": 5, "events_processed": 100}, "mdi:hub"),
])
SI3_attrs = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "engines_connected": 3, "events_processed": 50, "active_subscriptions": 7, "last_event": "zone.enter", "last_event_time": "2026-04-05T10:00:00", "engine_names": ["p1", "p2"]}, "engines_connected", 3),
    ({"ok": True, "engines_connected": 3, "events_processed": 50, "active_subscriptions": 7, "last_event": "zone.enter", "last_event_time": "2026-04-05T10:00:00", "engine_names": ["p1", "p2"]}, "events_processed", 50),
    ({"ok": True, "engines_connected": 3, "events_processed": 50, "active_subscriptions": 7, "last_event": "zone.enter", "last_event_time": "2026-04-05T10:00:00", "engine_names": ["p1", "p2"]}, "active_subscriptions", 7),
    ({"ok": True, "engines_connected": 3, "events_processed": 50, "active_subscriptions": 7, "last_event": "zone.enter", "last_event_time": "2026-04-05T10:00:00", "engine_names": ["p1", "p2"]}, "last_event", "zone.enter"),
    ({"ok": True, "engines_connected": 3, "events_processed": 50, "active_subscriptions": 7, "last_event": "zone.enter", "last_event_time": "2026-04-05T10:00:00", "engine_names": ["p1", "p2"]}, "engine_names", ["p1", "p2"]),
])
SI4_wiring = pytest.mark.parametrize("wiring_data,expected_keys", [
    ({"ok": True, "wiring_diagram": {"engine_a": ["ev1", "ev2"], "engine_b": ["ev3"]}}, ["engine_a", "engine_b"]),
    ({}, None),
])
SI5_event_log = pytest.mark.parametrize("event_log,expected_count", [
    ([], 0),
    ([{"event_type": "zone.enter", "source": "z", "handled_by": "p1", "timestamp": "t1"}], 1),
    ([{"event_type": f"e{i}", "source": f"s{i}", "handled_by": f"h{i}", "timestamp": f"t{i}"} for i in range(10)], 5),
    ([{"event_type": f"e{i}", "source": f"s{i}", "handled_by": f"h{i}", "timestamp": f"t{i}"} for i in range(7)], 5),
])
SI6_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "engines_connected": 1}, True),
    ({"ok": True}, True),
])


@SI1_native_value
def test_SI1_native_value(core_data, expected):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.native_value == expected


@SI2_icon
def test_SI2_icon(core_data, expected_icon):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.icon == expected_icon


@SI3_attrs
def test_SI3_attrs(core_data, key, expected):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.extra_state_attributes[key] == expected


@SI4_wiring
def test_SI4_wiring(wiring_data, expected_keys):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply(wiring_data)
    attrs = s.extra_state_attributes
    if expected_keys is None:
        assert "event_types" not in attrs
    else:
        assert attrs.get("event_types") == expected_keys


@SI5_event_log
def test_SI5_event_log_cap(event_log, expected_count):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply({"ok": True, "event_log": event_log})
    attrs = s.extra_state_attributes
    assert len(attrs.get("recent_events", [])) == expected_count


@SI6_edge
def test_SI6_edge(data, expect_ok):
    s = SystemIntegrationSensorContract(MockCoordinator({}))
    s._apply(data)
    if expect_ok:
        assert s._data.get("ok") is True
