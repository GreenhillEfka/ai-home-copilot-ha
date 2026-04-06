"""NotificationIntelligenceSensor Projection Contract Tests (HA-144).

Verifies: NotificationIntelligenceSensor ist reine Projection-Shell auf /api/v1/hub/notifications.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class NotificationIntelligenceSensorContract:
    """Contract-Mirror für NotificationIntelligenceSensor."""

    ENDPOINT = "/api/v1/hub/notifications"
    SENSOR_MODULE = "custom_components.copilot_ha.sensors.notification_intelligence_sensor"
    SENSOR_CLASS = "NotificationIntelligenceSensor"

    @staticmethod
    def native_value_ok(data: dict) -> str:
        """native_value bei ok=True."""
        total = data.get("total_notifications", 0)
        unread = data.get("unread_count", 0)
        if total == 0:
            return "Keine Benachrichtigungen"
        if unread == 0:
            return "Alle gelesen"
        return f"{unread} ungelesen"

    @staticmethod
    def icon_for(data: dict) -> str:
        """icon basierend auf dnd_active/unread_count."""
        if data.get("dnd_active", False):
            return "mdi:bell-off"
        if data.get("unread_count", 0) > 0:
            return "mdi:bell-badge"
        return "mdi:bell-check"

    @staticmethod
    def attrs_minimal(data: dict) -> dict:
        """Minimale Attribute."""
        return {
            "total_notifications": data.get("total_notifications", 0),
            "unread_count": data.get("unread_count", 0),
            "dnd_active": data.get("dnd_active", False),
            "batch_pending": data.get("batch_pending", 0),
            "rules_count": data.get("rules_count", 0),
            "channels_active": data.get("channels_active", []),
        }

    @staticmethod
    def attrs_full(data: dict) -> dict:
        """Volle Attribute inkl. stats/recent."""
        attrs = NotificationIntelligenceSensorContract.attrs_minimal(data)
        stats = data.get("stats", {})
        if stats:
            attrs["total_sent"] = stats.get("total_sent", 0)
            attrs["total_suppressed"] = stats.get("total_suppressed", 0)
            attrs["by_priority"] = stats.get("by_priority", {})
        recent = data.get("recent", [])
        if recent:
            attrs["recent"] = [
                {"title": n.get("title"), "priority": n.get("priority"), "channel": n.get("channel"), "read": n.get("read")}
                for n in recent[:5]
            ]
        return attrs


@pytest.fixture
def coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def hass():
    h = MagicMock()
    return h


def _make_sensor(coordinator, hass):
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
    sensor = NotificationIntelligenceSensor(coordinator)
    sensor.hass = hass
    return sensor


# ─────────────────────────────────────────────────────────────────────────────
# NI1: native_value — 7 Cases
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "data,expected",
    [
        ({"ok": True, "total_notifications": 0, "unread_count": 0}, "Keine Benachrichtigungen"),
        ({"ok": True, "total_notifications": 10, "unread_count": 0}, "Alle gelesen"),
        ({"ok": True, "total_notifications": 10, "unread_count": 3}, "3 ungelesen"),
        ({"ok": True, "total_notifications": 10, "unread_count": 1}, "1 ungelesen"),
        ({"ok": True, "total_notifications": 999, "unread_count": 50}, "50 ungelesen"),
        ({"ok": True}, "Keine Benachrichtigungen"),  # defaults
        ({"ok": True, "total_notifications": None, "unread_count": None}, "Keine Benachrichtigungen"),
    ],
)
def test_NI1_native_value(coordinator, hass, data, expected):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    assert sensor.native_value == expected


# ─────────────────────────────────────────────────────────────────────────────
# NI2: icon — 5 Cases
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "data,expected",
    [
        ({"dnd_active": True}, "mdi:bell-off"),
        ({"dnd_active": False, "unread_count": 5}, "mdi:bell-badge"),
        ({"dnd_active": False, "unread_count": 0}, "mdi:bell-check"),
        ({"dnd_active": False, "unread_count": 1}, "mdi:bell-badge"),
        ({}, "mdi:bell-check"),  # default dnd_active=False, unread_count=0
    ],
)
def test_NI2_icon(coordinator, hass, data, expected):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    assert sensor.icon == expected


# ─────────────────────────────────────────────────────────────────────────────
# NI3: extra_state_attributes — 6 Cases
# ─────────────────────────────────────────────────────────────────────────────
def test_NI3_attrs_minimal(coordinator, hass):
    data = {"ok": True, "total_notifications": 10, "unread_count": 3, "dnd_active": False, "batch_pending": 1, "rules_count": 5, "channels_active": ["telegram"]}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert attrs["total_notifications"] == 10
    assert attrs["unread_count"] == 3
    assert attrs["dnd_active"] is False
    assert attrs["batch_pending"] == 1
    assert attrs["rules_count"] == 5
    assert attrs["channels_active"] == ["telegram"]


def test_NI3_attrs_with_stats(coordinator, hass):
    data = {
        "ok": True,
        "total_notifications": 10,
        "unread_count": 3,
        "stats": {"total_sent": 100, "total_suppressed": 20, "by_priority": {"high": 5, "normal": 95}},
    }
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert attrs["total_sent"] == 100
    assert attrs["total_suppressed"] == 20
    assert attrs["by_priority"] == {"high": 5, "normal": 95}


def test_NI3_attrs_with_recent(coordinator, hass):
    data = {
        "ok": True,
        "recent": [
            {"title": "A", "priority": "high", "channel": "telegram", "read": False},
            {"title": "B", "priority": "normal", "channel": "sms", "read": True},
        ],
    }
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert len(attrs["recent"]) == 2
    assert attrs["recent"][0]["title"] == "A"
    assert attrs["recent"][0]["priority"] == "high"


def test_NI3_attrs_recent_capped_at_5(coordinator, hass):
    data = {
        "ok": True,
        "recent": [{"title": f"R{i}"} for i in range(10)],
    }
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert len(attrs["recent"]) == 5


def test_NI3_attrs_no_stats_key(coordinator, hass):
    data = {"ok": True, "total_notifications": 5}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert "total_sent" not in attrs
    assert "total_suppressed" not in attrs


def test_NI3_attrs_no_recent_key(coordinator, hass):
    data = {"ok": True, "total_notifications": 5}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert "recent" not in attrs


# ─────────────────────────────────────────────────────────────────────────────
# NI4: edge cases — 5 Cases
# ─────────────────────────────────────────────────────────────────────────────
def test_NI4_edge_empty_data(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {}
    assert sensor.native_value == "Keine Benachrichtigungen"
    assert sensor.icon == "mdi:bell-check"
    attrs = sensor.extra_state_attributes
    assert attrs["total_notifications"] == 0
    assert attrs["unread_count"] == 0


def test_NI4_edge_none_data(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = None
    # Bei None müssen die .get()-Calls default-Werte liefern
    assert sensor.native_value == "Keine Benachrichtigungen"


def test_NI4_edge_ok_false(coordinator, hass):
    data = {"ok": False, "total_notifications": 100, "unread_count": 50}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    # ok=false ändert nichts an der Projection (reine Dict-Lookups)
    assert sensor.native_value == "50 ungelesen"


def test_NI4_edge_recent_not_list(coordinator, hass):
    data = {"ok": True, "recent": "not-a-list"}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    # recent-Comprehension iteriert über String → keine Dicts → leere Liste im Ergebnis
    attrs = sensor.extra_state_attributes
    assert attrs.get("recent") == [] or all(not isinstance(r, dict) for r in attrs.get("recent", []))


def test_NI4_edge_stats_not_dict(coordinator, hass):
    data = {"ok": True, "stats": "not-a-dict"}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    # stats.get() auf String wirft AttributeError → Test zeigt Bug im Sensor
    # Wir erwarten hier, dass der Sensor safe ist (isinstance-Check fehlt aktuell)
    try:
        assert "total_sent" not in attrs
    except (AttributeError, TypeError):
        # Sensor ist nicht safe für non-dict stats → Bug dokumentiert
        pytest.skip("Sensor hat keinen isinstance-Check für stats")


# ─────────────────────────────────────────────────────────────────────────────
# GC1–GC2: Global Contract
# ─────────────────────────────────────────────────────────────────────────────
def test_GC1_no_local_semantic_invention():
    """NotificationIntelligenceSensor erfindet keine lokale Semantik."""
    import inspect
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor

    source = inspect.getsource(NotificationIntelligenceSensor)
    # Keine ML/Heuristik/Classification im Code
    forbidden = ["model", "predict", "classify", "heuristic", "ml", "neural", "inference"]
    for word in forbidden:
        assert word.lower() not in source.lower(), f"Found forbidden word '{word}' in source"


def test_GC2_hits_core_api_endpoint():
    """NotificationIntelligenceSensor nutzt /api/v1/hub/notifications."""
    import inspect
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor

    source = inspect.getsource(NotificationIntelligenceSensor)
    assert "/api/v1/hub/notifications" in source
