"""NotificationIntelligenceSensor Projection Contract Tests (HA-144 / HA-343).

Verifies: NotificationIntelligenceSensor ist reine Projection-Shell auf /api/v1/hub/notifications.
"""

import pytest
from unittest.mock import MagicMock


class NotificationIntelligenceSensorContract:
    """Contract-Mirror für NotificationIntelligenceSensor."""

    ENDPOINT = "/api/v1/hub/notifications"
    SENSOR_MODULE = "custom_components.pilotsuite.sensors.notification_intelligence_sensor"
    SENSOR_CLASS = "NotificationIntelligenceSensor"

    @staticmethod
    def _as_mapping(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value):
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_int(value, default=0):
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value
        return default

    @staticmethod
    def _as_bool(value, default=False):
        if isinstance(value, bool):
            return value
        return default

    @staticmethod
    def _as_string(value, default=""):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return default

    @staticmethod
    def native_value_ok(data: dict) -> str:
        """native_value bei ok=True."""
        safe = NotificationIntelligenceSensorContract._as_mapping(data)
        total = NotificationIntelligenceSensorContract._as_int(safe.get("total_notifications"), 0)
        unread = NotificationIntelligenceSensorContract._as_int(safe.get("unread_count"), 0)
        if total == 0:
            return "Keine Benachrichtigungen"
        if unread == 0:
            return "Alle gelesen"
        return f"{unread} ungelesen"

    @staticmethod
    def icon_for(data: dict) -> str:
        """icon basierend auf dnd_active/unread_count."""
        safe = NotificationIntelligenceSensorContract._as_mapping(data)
        if NotificationIntelligenceSensorContract._as_bool(safe.get("dnd_active"), False):
            return "mdi:bell-off"
        if NotificationIntelligenceSensorContract._as_int(safe.get("unread_count"), 0) > 0:
            return "mdi:bell-badge"
        return "mdi:bell-check"

    @staticmethod
    def attrs_minimal(data: dict) -> dict:
        """Minimale Attribute."""
        safe = NotificationIntelligenceSensorContract._as_mapping(data)
        return {
            "total_notifications": NotificationIntelligenceSensorContract._as_int(safe.get("total_notifications"), 0),
            "unread_count": NotificationIntelligenceSensorContract._as_int(safe.get("unread_count"), 0),
            "dnd_active": NotificationIntelligenceSensorContract._as_bool(safe.get("dnd_active"), False),
            "batch_pending": NotificationIntelligenceSensorContract._as_int(safe.get("batch_pending"), 0),
            "rules_count": NotificationIntelligenceSensorContract._as_int(safe.get("rules_count"), 0),
            "channels_active": [
                channel
                for channel in (
                    NotificationIntelligenceSensorContract._as_string(item)
                    for item in NotificationIntelligenceSensorContract._as_list(safe.get("channels_active"))
                )
                if channel
            ],
        }

    @staticmethod
    def attrs_full(data: dict) -> dict:
        """Volle Attribute inkl. stats/recent."""
        safe = NotificationIntelligenceSensorContract._as_mapping(data)
        attrs = NotificationIntelligenceSensorContract.attrs_minimal(safe)
        stats = NotificationIntelligenceSensorContract._as_mapping(safe.get("stats"))
        if stats:
            attrs["total_sent"] = NotificationIntelligenceSensorContract._as_int(stats.get("total_sent"), 0)
            attrs["total_suppressed"] = NotificationIntelligenceSensorContract._as_int(stats.get("total_suppressed"), 0)
            attrs["by_priority"] = NotificationIntelligenceSensorContract._as_mapping(stats.get("by_priority"))
        recent = []
        for notification in NotificationIntelligenceSensorContract._as_list(safe.get("recent"))[:5]:
            item = NotificationIntelligenceSensorContract._as_mapping(notification)
            if not item:
                continue
            recent.append(
                {
                    "title": NotificationIntelligenceSensorContract._as_string(item.get("title")),
                    "priority": NotificationIntelligenceSensorContract._as_string(item.get("priority")),
                    "channel": NotificationIntelligenceSensorContract._as_string(item.get("channel")),
                    "read": NotificationIntelligenceSensorContract._as_bool(item.get("read"), False),
                }
            )
        if recent:
            attrs["recent"] = recent
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
    from custom_components.pilotsuite.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
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
    assert sensor.native_value == "Keine Benachrichtigungen"
    assert sensor.icon == "mdi:bell-check"
    attrs = sensor.extra_state_attributes
    assert attrs["channels_active"] == []


def test_NI4_edge_ok_false(coordinator, hass):
    data = {"ok": False, "total_notifications": 100, "unread_count": 50}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    assert sensor.native_value == "50 ungelesen"


def test_NI4_edge_recent_not_list(coordinator, hass):
    data = {"ok": True, "recent": "not-a-list"}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert "recent" not in attrs


def test_NI4_edge_stats_not_dict(coordinator, hass):
    data = {"ok": True, "stats": "not-a-dict"}
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    attrs = sensor.extra_state_attributes
    assert "total_sent" not in attrs
    assert "total_suppressed" not in attrs
    assert "by_priority" not in attrs


# ─────────────────────────────────────────────────────────────────────────────
# NI5: malformed payload guards — 8 Cases
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "data,expected",
    [
        ({"ok": True, "total_notifications": "10", "unread_count": 3}, "Keine Benachrichtigungen"),
        ({"ok": True, "total_notifications": 10, "unread_count": "3"}, "Alle gelesen"),
        ({"ok": True, "total_notifications": True, "unread_count": 2}, "Keine Benachrichtigungen"),
        ({"ok": True, "dnd_active": "yes", "unread_count": 3}, "mdi:bell-badge"),
    ],
)
def test_NI5_malformed_scalar_projection(coordinator, hass, data, expected):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = data
    if expected.startswith("mdi:"):
        assert sensor.icon == expected
    else:
        assert sensor.native_value == expected


def test_NI5_channels_active_non_list_guard(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {"ok": True, "channels_active": "telegram"}
    assert sensor.extra_state_attributes["channels_active"] == []


def test_NI5_channels_active_mixed_list_guard(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {"ok": True, "channels_active": ["telegram", None, 3, " sms ", ""]}
    assert sensor.extra_state_attributes["channels_active"] == ["telegram", "sms"]


def test_NI5_recent_mixed_entries_guard(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {
        "ok": True,
        "recent": [
            {"title": "A", "priority": "high", "channel": "telegram", "read": True},
            "bad-entry",
            {"title": 7, "priority": None, "channel": " sms ", "read": "no"},
        ],
    }
    assert sensor.extra_state_attributes["recent"] == [
        {"title": "A", "priority": "high", "channel": "telegram", "read": True},
        {"title": "", "priority": "", "channel": "sms", "read": False},
    ]


def test_NI5_stats_malformed_fields_guard(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {
        "ok": True,
        "stats": {"total_sent": "100", "total_suppressed": True, "by_priority": ["high"]},
    }
    attrs = sensor.extra_state_attributes
    assert attrs["total_sent"] == 0
    assert attrs["total_suppressed"] == 0
    assert attrs["by_priority"] == {}


@pytest.mark.asyncio
async def test_NI5_async_update_top_level_non_dict_guard(coordinator, hass):
    sensor = _make_sensor(coordinator, hass)
    sensor._data = {"ok": True, "total_notifications": 9}

    async def fake_fetch():
        return ["not", "a", "dict"]

    sensor._fetch = fake_fetch
    await sensor.async_update()
    assert sensor._data == {"ok": True, "total_notifications": 9}


# ─────────────────────────────────────────────────────────────────────────────
# GC1–GC3: Global Contract
# ─────────────────────────────────────────────────────────────────────────────
def test_GC1_no_local_semantic_invention():
    """NotificationIntelligenceSensor erfindet keine lokale Semantik."""
    import inspect
    from custom_components.pilotsuite.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor

    source = inspect.getsource(NotificationIntelligenceSensor)
    # Keine ML/Heuristik/Classification im Code
    forbidden = ["model", "predict", "classify", "heuristic", "ml", "neural", "inference"]
    for word in forbidden:
        assert word.lower() not in source.lower(), f"Found forbidden word '{word}' in source"


def test_GC2_hits_core_api_endpoint():
    """NotificationIntelligenceSensor nutzt /api/v1/hub/notifications."""
    import inspect
    from custom_components.pilotsuite.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor

    source = inspect.getsource(NotificationIntelligenceSensor)
    assert "/api/v1/hub/notifications" in source


def test_GC3_source_guard_helpers_present():
    """Source verankert Guard-Helper und Top-Level-Dict-Guard."""
    import inspect
    from custom_components.pilotsuite.sensors import notification_intelligence_sensor as module

    source = inspect.getsource(module)
    for helper in ["_as_mapping", "_as_list", "_as_int", "_as_bool", "_as_string"]:
        assert helper in source
    assert "isinstance(data, dict)" in source
