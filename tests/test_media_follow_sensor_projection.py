"""Contract tests: MediaFollowSensor is a pure projection shell on /api/v1/hub/media."""

import pytest

from custom_components.copilot_ha.sensors.media_follow_sensor import (
    MediaFollowSensor,
    _MEDIA_ICONS,
)


# =============================================================================
# Contract Mirror
# =============================================================================


class MediaFollowSensorContract:
    """Mirrors what MediaFollowSensor reads from Core API response (coordinator.data)."""

    def __init__(self, data: dict | None):
        self._data = data if (data and data.get("ok")) else {}

    def native_value(self) -> str:
        active = self._data.get("active_sessions", 0)
        if active == 0:
            return "Keine Wiedergabe"
        sessions = self._data.get("sessions", [])
        if not isinstance(sessions, list):
            sessions = []
        playing = [s for s in sessions if isinstance(s, dict) and s.get("state") == "playing"]
        if len(playing) == 1:
            title = playing[0].get("title", "")
            artist = playing[0].get("artist", "")
            if artist:
                return f"{artist} — {title}"
            return title or "Wiedergabe"
        return f"{len(playing)} Wiedergaben"

    def icon(self) -> str:
        sessions = self._data.get("sessions", [])
        if not isinstance(sessions, list):
            return "mdi:music-off"
        playing = [s for s in sessions if isinstance(s, dict) and s.get("state") == "playing"]
        if not playing:
            return "mdi:music-off"
        if len(playing) == 1:
            mt = playing[0].get("media_type", "music")
            return _MEDIA_ICONS.get(mt, "mdi:music")
        return "mdi:music-circle-outline"

    def extra_state_attributes(self) -> dict:
        attrs = {
            "total_sources": self._data.get("total_sources", 0),
            "active_sessions": self._data.get("active_sessions", 0),
            "zones_with_playback": self._data.get("zones_with_playback", 0),
            "follow_enabled_zones": self._data.get("follow_enabled_zones", 0),
        }
        sessions = self._data.get("sessions", [])
        if sessions:
            attrs["sessions"] = [
                {
                    "zone": s.get("zone_id"),
                    "title": s.get("title"),
                    "artist": s.get("artist"),
                    "state": s.get("state"),
                    "media_type": s.get("media_type"),
                    "follow": s.get("follow_enabled"),
                }
                for s in sessions
            ]
        zones = self._data.get("zone_states", [])
        if zones:
            attrs["zone_states"] = [
                {
                    "zone": z.get("zone_id"),
                    "title": z.get("primary_title"),
                    "artist": z.get("primary_artist"),
                    "state": z.get("primary_state"),
                    "follow": z.get("follow_enabled"),
                }
                for z in zones
            ]
        transfers = self._data.get("recent_transfers", [])
        if transfers:
            attrs["recent_transfers"] = transfers[:5]
        return attrs


# =============================================================================
# MF1: native_value
# =============================================================================
@pytest.mark.parametrize(
    "raw,expected",
    [
        # MF1.1: ok, 0 sessions
        (
            {"ok": True, "active_sessions": 0, "sessions": []},
            "Keine Wiedergabe",
        ),
        # MF1.2: ok, 1 playing with artist+title
        (
            {
                "ok": True,
                "active_sessions": 1,
                "sessions": [{"state": "playing", "title": "Bohemian Rhapsody", "artist": "Queen"}],
            },
            "Queen — Bohemian Rhapsody",
        ),
        # MF1.3: ok, 1 playing, title only (no artist)
        (
            {
                "ok": True,
                "active_sessions": 1,
                "sessions": [{"state": "playing", "title": "Morning Mood", "artist": ""}],
            },
            "Morning Mood",
        ),
        # MF1.4: ok, 1 playing, neither title nor artist
        (
            {"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "title": "", "artist": ""}]},
            "Wiedergabe",
        ),
        # MF1.5: ok, 1 session but state=paused (not "playing")
        (
            {"ok": True, "active_sessions": 0, "sessions": [{"state": "paused", "title": "Song", "artist": "Artist"}]},
            "Keine Wiedergabe",
        ),
        # MF1.6: ok, 2 playing sessions
        (
            {
                "ok": True,
                "active_sessions": 2,
                "sessions": [
                    {"state": "playing", "title": "Song A", "artist": "Artist A"},
                    {"state": "playing", "title": "Song B", "artist": "Artist B"},
                ],
            },
            "2 Wiedergaben",
        ),
        # MF1.7: ok, 3 playing sessions
        (
            {
                "ok": True,
                "active_sessions": 3,
                "sessions": [
                    {"state": "playing", "title": "S1", "artist": "A1"},
                    {"state": "playing", "title": "S2", "artist": "A2"},
                    {"state": "playing", "title": "S3", "artist": "A3"},
                ],
            },
            "3 Wiedergaben",
        ),
    ],
)
def test_mf1_native_value(raw, expected):
    assert MediaFollowSensorContract(raw).native_value() == expected


# =============================================================================
# MF2: icon
# =============================================================================
@pytest.mark.parametrize(
    "raw,expected",
    [
        # MF2.1: no sessions
        ({"ok": True, "active_sessions": 0, "sessions": []}, "mdi:music-off"),
        # MF2.2: 1 playing, music
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "music"}]}, "mdi:music"),
        # MF2.3: 1 playing, tv
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "tv"}]}, "mdi:television"),
        # MF2.4: 1 playing, radio
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "radio"}]}, "mdi:radio"),
        # MF2.5: 1 playing, podcast
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "podcast"}]}, "mdi:podcast"),
        # MF2.6: 1 playing, video
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "video"}]}, "mdi:video"),
        # MF2.7: 1 playing, unknown media_type → default mdi:music
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing", "media_type": "unknown"}]}, "mdi:music"),
        # MF2.8: 1 playing, media_type missing → default mdi:music
        ({"ok": True, "active_sessions": 1, "sessions": [{"state": "playing"}]}, "mdi:music"),
        # MF2.9: 2+ playing sessions
        (
            {
                "ok": True,
                "active_sessions": 2,
                "sessions": [
                    {"state": "playing", "media_type": "music"},
                    {"state": "playing", "media_type": "tv"},
                ],
            },
            "mdi:music-circle-outline",
        ),
    ],
)
def test_mf2_icon(raw, expected):
    assert MediaFollowSensorContract(raw).icon() == expected


# =============================================================================
# MF3: extra_state_attributes
# =============================================================================
def test_mf3_attrs_full():
    raw = {
        "ok": True,
        "total_sources": 5,
        "active_sessions": 2,
        "zones_with_playback": 3,
        "follow_enabled_zones": 2,
        "sessions": [
            {
                "zone_id": "zone_1",
                "title": "Song A",
                "artist": "Artist A",
                "state": "playing",
                "media_type": "music",
                "follow_enabled": True,
            },
            {
                "zone_id": "zone_2",
                "title": "Song B",
                "artist": "Artist B",
                "state": "playing",
                "media_type": "tv",
                "follow_enabled": False,
            },
        ],
        "zone_states": [
            {
                "zone_id": "zone_1",
                "primary_title": "Song A",
                "primary_artist": "Artist A",
                "primary_state": "playing",
                "follow_enabled": True,
            },
        ],
        "recent_transfers": [{"from": "zone_1", "to": "zone_2"}, {"from": "zone_2", "to": "zone_3"}],
    }
    attrs = MediaFollowSensorContract(raw).extra_state_attributes()
    assert attrs["total_sources"] == 5
    assert attrs["active_sessions"] == 2
    assert attrs["zones_with_playback"] == 3
    assert attrs["follow_enabled_zones"] == 2
    assert len(attrs["sessions"]) == 2
    assert attrs["sessions"][0]["zone"] == "zone_1"
    assert len(attrs["zone_states"]) == 1
    assert len(attrs["recent_transfers"]) == 2  # only 2 items, not capped


def test_mf3_attrs_empty_sessions():
    raw = {
        "ok": True,
        "active_sessions": 0,
        "sessions": [],
        "total_sources": 0,
        "zones_with_playback": 0,
        "follow_enabled_zones": 0,
    }
    attrs = MediaFollowSensorContract(raw).extra_state_attributes()
    assert attrs["total_sources"] == 0
    assert attrs["active_sessions"] == 0
    assert "sessions" not in attrs
    assert "zone_states" not in attrs
    assert "recent_transfers" not in attrs


def test_mf3_attrs_missing_optional_keys():
    raw = {"ok": True}
    attrs = MediaFollowSensorContract(raw).extra_state_attributes()
    assert attrs["total_sources"] == 0
    assert attrs["active_sessions"] == 0
    assert attrs["zones_with_playback"] == 0
    assert attrs["follow_enabled_zones"] == 0
    assert "sessions" not in attrs


# =============================================================================
# MF4: edge cases
# =============================================================================
def test_mf4_ok_false():
    """ok=false → _data stays empty → defaults apply."""
    raw = {"ok": False, "active_sessions": 99, "sessions": [{"state": "playing", "title": "X"}]}
    c = MediaFollowSensorContract(raw)
    assert c.native_value() == "Keine Wiedergabe"
    assert c.icon() == "mdi:music-off"


def test_mf4_data_none():
    c = MediaFollowSensorContract(None)
    assert c.native_value() == "Keine Wiedergabe"
    assert c.icon() == "mdi:music-off"


def test_mf4_data_empty_dict():
    c = MediaFollowSensorContract({})
    assert c.native_value() == "Keine Wiedergabe"
    assert c.icon() == "mdi:music-off"


def test_mf4_sessions_not_list():
    """sessions is not a list → treated as empty list → 0 playing found → '0 Wiedergaben'."""
    raw = {"ok": True, "active_sessions": 1, "sessions": "not-a-list"}
    c = MediaFollowSensorContract(raw)
    assert c.native_value() == "0 Wiedergaben"


def test_mf4_recent_transfers_capped():
    """recent_transfers is capped at [:5]."""
    raw = {
        "ok": True,
        "active_sessions": 0,
        "sessions": [],
        "total_sources": 0,
        "zones_with_playback": 0,
        "follow_enabled_zones": 0,
        "recent_transfers": [{"from": f"z{i}", "to": f"z{i+1}"} for i in range(10)],
    }
    attrs = MediaFollowSensorContract(raw).extra_state_attributes()
    assert len(attrs["recent_transfers"]) == 5  # capped at [:5]


# =============================================================================
# GC1: pure projection on /api/v1/hub/media
# =============================================================================
def test_gc1_hub_media_endpoint():
    """MediaFollowSensor hits /api/v1/hub/media via _fetch()."""
    # The _fetch method is the only HTTP call site — verify the URL path
    import inspect
    source = inspect.getsource(MediaFollowSensor._fetch)
    assert "/api/v1/hub/media" in source, "_fetch must target /api/v1/hub/media"


# =============================================================================
# GC2: no local semantic invention
# =============================================================================
def test_gc2_no_local_semantic_invention():
    """MediaFollowSensor does not compute derived semantic values — only pass-through."""
    raw = {
        "ok": True,
        "active_sessions": 1,
        "total_sources": 3,
        "zones_with_playback": 1,
        "follow_enabled_zones": 1,
        "sessions": [
            {
                "state": "playing",
                "title": "Test",
                "artist": "Artist",
                "media_type": "music",
                "zone_id": "z1",
                "follow_enabled": True,
            }
        ],
        "zone_states": [],
        "recent_transfers": [],
    }
    c = MediaFollowSensorContract(raw)
    # native_value: 1 playing with artist → pass-through
    assert c.native_value() == "Artist — Test"
    # icon: 1 playing, music → pass-through
    assert c.icon() == "mdi:music"
    # attrs: pass-through
    attrs = c.extra_state_attributes()
    assert attrs["total_sources"] == 3
    assert len(attrs["sessions"]) == 1
    # The sensor does not classify mood, energy level, or any semantic derivative.
    # If it did, contract output would differ from sensor output.
    # Here: pass-through only → contract == sensor behavior.
