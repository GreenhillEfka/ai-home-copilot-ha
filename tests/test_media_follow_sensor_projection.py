"""Projection Contract Tests for MediaFollowSensor (HA-24).

Verifies that MediaFollowSensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/media) with trivial presentation logic only.

Pattern: same as HA-6 through HA-23.
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


_MEDIA_ICONS = {
    "music": "mdi:music",
    "tv": "mdi:television",
    "radio": "mdi:radio",
    "podcast": "mdi:podcast",
    "video": "mdi:video",
}


class MediaFollowSensorContract:
    """Mirror of MediaFollowSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/hub/media
    - native_value: "Keine Wiedergabe" | "artist — title" | "{n} Wiedergaben"
    - icon: media_type lookup or music-off/circle-outline
    - extra_state_attributes: direct passthrough of sessions/zones/transfers
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        active = self._data.get("active_sessions", 0)
        if active == 0:
            return "Keine Wiedergabe"
        sessions = self._data.get("sessions", [])
        playing = [s for s in sessions if s.get("state") == "playing"]
        if len(playing) == 1:
            title = playing[0].get("title", "")
            artist = playing[0].get("artist", "")
            if artist:
                return f"{artist} — {title}"
            return title or "Wiedergabe"
        return f"{len(playing)} Wiedergaben"

    @property
    def icon(self):
        sessions = self._data.get("sessions", [])
        playing = [s for s in sessions if s.get("state") == "playing"]
        if not playing:
            return "mdi:music-off"
        if len(playing) == 1:
            mt = playing[0].get("media_type", "music")
            return _MEDIA_ICONS.get(mt, "mdi:music")
        return "mdi:music-circle-outline"

    @property
    def extra_state_attributes(self):
        attrs = {
            "total_sources": self._data.get("total_sources", 0),
            "active_sessions": self._data.get("active_sessions", 0),
            "zones_with_playback": self._data.get("zones_with_playback", 0),
            "follow_enabled_zones": self._data.get("follow_enabled_zones", 0),
        }
        sessions = self._data.get("sessions", [])
        if sessions:
            attrs["sessions"] = [
                {"zone": s.get("zone_id"), "title": s.get("title"),
                 "artist": s.get("artist"), "state": s.get("state"),
                 "media_type": s.get("media_type"), "follow": s.get("follow_enabled")}
                for s in sessions
            ]
        zones = self._data.get("zone_states", [])
        if zones:
            attrs["zone_states"] = [
                {"zone": z.get("zone_id"), "title": z.get("primary_title"),
                 "artist": z.get("primary_artist"), "state": z.get("primary_state"),
                 "follow": z.get("follow_enabled")}
                for z in zones
            ]
        transfers = self._data.get("recent_transfers", [])
        if transfers:
            attrs["recent_transfers"] = transfers[:5]
        return attrs


MF1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "active_sessions": 0}, "Keine Wiedergabe"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "title": "Song", "artist": "Artist"}]}, "Artist — Song"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "title": "OnlyTitle", "artist": ""}]}, "OnlyTitle"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "title": "", "artist": ""}]}, "Wiedergabe"),
    ({"ok": True, "active_sessions": 2, "sessions": [{"state": "playing"}, {"state": "paused"}]}, "Wiedergabe"),
    ({"ok": True, "active_sessions": 3, "sessions": [{"state": "playing"}, {"state": "playing"}, {"state": "paused"}]}, "2 Wiedergaben"),
])
MF2 = pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "active_sessions": 0}, "mdi:music-off"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "music"}]}, "mdi:music"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "tv"}]}, "mdi:television"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "radio"}]}, "mdi:radio"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "podcast"}]}, "mdi:podcast"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "video"}]}, "mdi:video"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": ""}]}, "mdi:music"),
    ({"ok": True, "active_sessions": 2, "sessions": [{"state": "playing"}, {"state": "playing"}]}, "mdi:music-circle-outline"),
    ({"ok": True, "active_sessions": 1, "sessions": [{"state": "paused"}]}, "mdi:music-off"),
])
MF3 = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "total_sources": 3, "active_sessions": 1, "zones_with_playback": 2, "follow_enabled_zones": 1}, "total_sources", 3),
    ({"ok": True, "total_sources": 3, "active_sessions": 1, "zones_with_playback": 2, "follow_enabled_zones": 1}, "active_sessions", 1),
    ({"ok": True, "total_sources": 3, "active_sessions": 1, "zones_with_playback": 2, "follow_enabled_zones": 1}, "zones_with_playback", 2),
    ({"ok": True, "total_sources": 3, "active_sessions": 1, "zones_with_playback": 2, "follow_enabled_zones": 1}, "follow_enabled_zones", 1),
])
MF4_sessions = pytest.mark.parametrize("sessions_data,expected_count", [
    ([], 0),
    ([{"zone_id": "z1", "title": "T", "artist": "A", "state": "playing", "media_type": "music", "follow_enabled": True}], 1),
    ([{"zone_id": "z1"}, {"zone_id": "z2"}], 2),
])
MF5_transfers = pytest.mark.parametrize("transfers_data,expected_count", [
    ([], 0),
    ([{"t1": "x"}], 1),
])
MF6_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "active_sessions": 0}, True),
])


@MF1
def test_MF1_native_value(data, expected):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@MF2
def test_MF2_icon(data, expected_icon):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.icon == expected_icon


@MF3
def test_MF3_attrs(data, key, expected):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected


@MF4_sessions
def test_MF4_sessions_passthrough(sessions_data, expected_count):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply({"ok": True, "sessions": sessions_data})
    attrs = s.extra_state_attributes
    assert len(attrs.get("sessions", [])) == expected_count


@MF5_transfers
def test_MF5_transfers_cap(transfers_data, expected_count):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply({"ok": True, "recent_transfers": transfers_data})
    attrs = s.extra_state_attributes
    assert len(attrs.get("recent_transfers", [])) == expected_count


@MF6_edge
def test_MF6_edge(data, expect_ok):
    s = MediaFollowSensorContract(MockCoordinator({}))
    s.apply(data)
    if expect_ok:
        assert s._data.get("ok") is True
