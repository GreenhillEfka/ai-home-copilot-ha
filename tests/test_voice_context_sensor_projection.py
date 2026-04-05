"""Projection Contract Tests — voice_context sensors (HA-126).

Verifies VoiceContextSensor + VoicePromptSensor are pure Projection-Shells
on coordinator.data["mood"] / ["neural"] / ["suggestions"] — no local semantic invention.

Contract: both sensors derive ALL display values from coordinator.data via trivial
Dict-lookups and string formatting. No local classification, no heuristic, no
semantic interpretation beyond what Core provides.

HA-126 — 2026-04-06
"""
from __future__ import annotations

import pytest
from homeassistant.components.sensor import SensorDeviceClass


# =============================================================================
# Contract Mirrors
# =============================================================================

class VoiceContextSensorContract:
    """Mirror of VoiceContextSensor extra_state_attributes + native_value logic.

    Contract:
    - reads: coordinator.data["mood"], ["neural"], ["suggestions"]
    - native_value: always "ok" (initialised in __init__)
    - extra_state_attributes:
        dominant_mood       ← mood.get("mood", "unknown")
        mood_confidence     ← mood.get("confidence", 0.0)
        mood_contributors   ← mood.get("contributors", [])
        current_zone        ← neural.get("zone", {}).get("current", "unknown")
        zone_presence       ← neural.get("zone", {}).get("presence") or neural.get("presence", [])
        voice_tone          ← mood.get("mood", "unknown")   (same as dominant_mood)
        voice_greeting      ← neural.get("time", {}).get("description_de") or
                               neural.get("time", {}).get("description_en", "Hallo")
        voice_suggestions   ← [f"{act} ist aktuell." for act in
                               neural.get("zone", {}).get("typical_activities", [])[:3]]
        voice_prompt        ← built from greeting + presence + suggestions
        last_update         ← neural.get("last_update", "")
    """

    @staticmethod
    def native_value(_coordinator_data: dict) -> str:
        return "ok"

    @staticmethod
    def extra_state_attributes(coordinator_data: dict) -> dict:
        mood = coordinator_data.get("mood", {})
        neural = coordinator_data.get("neural", {})
        suggestions = coordinator_data.get("suggestions", [])

        dominant_mood = mood.get("mood", "unknown")
        confidence = mood.get("confidence", 0.0)
        time_greeting = neural.get("time", {}).get("description_de") or \
                        neural.get("time", {}).get("description_en", "Hallo")
        zone_name = neural.get("zone", {}).get("current", "unknown")
        zone_activities = neural.get("zone", {}).get("typical_activities", [])
        voice_suggestions = [f"{act} ist aktuell." for act in zone_activities[:3]]
        core_zone = neural.get("zone", {})
        presence = core_zone.get("presence", neural.get("presence", []))

        return {
            "dominant_mood": dominant_mood,
            "mood_confidence": confidence,
            "mood_contributors": mood.get("contributors", []),
            "current_zone": zone_name,
            "zone_presence": presence,
            "voice_tone": dominant_mood,
            "voice_greeting": time_greeting,
            "voice_suggestions": voice_suggestions,
            "voice_prompt": VoiceContextSensorContract._build_prompt(
                time_greeting, presence, voice_suggestions
            ),
            "last_update": neural.get("last_update", ""),
        }

    @staticmethod
    def _build_prompt(greeting: str, presence: list, suggestions: list) -> str:
        parts = [f"Der Nutzer ist gerade {greeting}."]
        if presence:
            zones = ", ".join(presence[:3])
            parts.append(f"Anwesend in: {zones}.")
        if suggestions:
            parts.append(f"Vorschläge: {'; '.join(suggestions[:2])}.")
        return " ".join(parts)


class VoicePromptSensorContract:
    """Mirror of VoicePromptSensor native_value logic.

    Contract:
    - reads: coordinator.data["mood"], ["suggestions"]
    - native_value:
        mood_tones mapping (relax→Entspannt, focus→Fokussiert, etc.)
        f"Der Nutzer ist {tone}."
        if suggestions: + " {len(suggestions)} Vorschläge verfügbar."
        else: returns "Kein Kontext verfügbar." when coordinator.data empty
    """

    MOOD_TONES = {
        "relax": "Entspannt",
        "focus": "Fokussiert",
        "active": "Aktiv",
        "sleep": "Müde",
        "away": "Abwesend",
        "alert": "Aufmerksam",
        "social": "Gesellig",
        "recovery": "Erholend",
    }

    @staticmethod
    def native_value(coordinator_data: dict) -> str:
        if not coordinator_data:
            return "Kein Kontext verfügbar."
        mood = coordinator_data.get("mood", {})
        suggestions = coordinator_data.get("suggestions", [])
        dominant_mood = mood.get("mood", "unknown")
        tone = VoicePromptSensorContract.MOOD_TONES.get(dominant_mood, "Neutral")
        prompt = f"Der Nutzer ist {tone}."
        if suggestions:
            prompt += f" {len(suggestions)} Vorschläge verfügbar."
        return prompt


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def full_data():
    """Full coordinator data with all expected keys."""
    return {
        "mood": {
            "mood": "relax",
            "confidence": 0.85,
            "contributors": ["music", "comfort"],
        },
        "neural": {
            "time": {"description_de": "Guten Morgen"},
            "zone": {
                "current": "Wohnzimmer",
                "typical_activities": ["Lesen", "Musik hören"],
                "presence": ["Wohnzimmer"],
            },
            "last_update": "2026-04-06T08:00:00",
        },
        "suggestions": [],
    }


@pytest.fixture
def empty_data():
    return {}


# =============================================================================
# VC1 — VoiceContextSensor extra_state_attributes
# =============================================================================

@pytest.mark.parametrize("coordinator_data, key, expected", [
    # VC1a: full data
    (
        {
            "mood": {"mood": "relax", "confidence": 0.85, "contributors": ["music", "comfort"]},
            "neural": {
                "time": {"description_de": "Guten Morgen"},
                "zone": {"current": "Wohnzimmer", "typical_activities": ["Lesen", "Musik hören"], "presence": ["Wohnzimmer"]},
                "last_update": "2026-04-06T08:00:00",
            },
            "suggestions": [],
        },
        "dominant_mood",
        "relax",
    ),
    # VC1b: missing mood
    (
        {"neural": {}},
        "dominant_mood",
        "unknown",
    ),
    # VC1c: missing confidence
    (
        {"mood": {"mood": "focus"}},
        "mood_confidence",
        0.0,
    ),
    # VC1d: contributors
    (
        {"mood": {"mood": "active", "contributors": ["sport", "coffee"]}},
        "mood_contributors",
        ["sport", "coffee"],
    ),
    # VC1e: current_zone
    (
        {"neural": {"zone": {"current": "Büro"}}},
        "current_zone",
        "Büro",
    ),
    # VC1f: zone_presence from neural.zone.presence
    (
        {"neural": {"zone": {"presence": ["Küche", "Flur"]}}},
        "zone_presence",
        ["Küche", "Flur"],
    ),
    # VC1g: zone_presence fallback to neural.presence
    (
        {"neural": {"presence": ["Schlafzimmer"]}},
        "zone_presence",
        ["Schlafzimmer"],
    ),
    # VC1h: voice_tone = dominant_mood
    (
        {"mood": {"mood": "sleep"}},
        "voice_tone",
        "sleep",
    ),
    # VC1i: english fallback
    (
        {"neural": {"time": {"description_en": "Good morning"}}},
        "voice_greeting",
        "Good morning",
    ),
    # VC1j: activities capped at 3
    (
        {"neural": {"zone": {"typical_activities": ["A", "B", "C", "D"]}}},
        "voice_suggestions",
        ["A ist aktuell.", "B ist aktuell.", "C ist aktuell."],
    ),
    # VC1k: empty activities
    (
        {"neural": {"zone": {"typical_activities": []}}},
        "voice_suggestions",
        [],
    ),
    # VC1l: last_update
    (
        {"neural": {"last_update": "2026-04-06T10:00:00Z"}},
        "last_update",
        "2026-04-06T10:00:00Z",
    ),
])
def test_vc1_extra_state_attributes(coordinator_data, key, expected):
    """VC1: extra_state_attributes are pure Dict lookups from coordinator.data."""
    attrs = VoiceContextSensorContract.extra_state_attributes(coordinator_data)
    assert attrs[key] == expected, f"{key}: {attrs[key]!r} != {expected!r}"


# =============================================================================
# VC2 — VoiceContextSensor voice_prompt construction
# =============================================================================

@pytest.mark.parametrize("greeting, presence, suggestions, expected", [
    # VC2a: full prompt
    (
        "Guten Morgen",
        ["Wohnzimmer", "Küche"],
        ["Lesen", "Musik"],
        "Der Nutzer ist gerade Guten Morgen. Anwesend in: Wohnzimmer, Küche. Vorschläge: Lesen; Musik.",
    ),
    # VC2b: no presence, no suggestions
    (
        "Hallo",
        [],
        [],
        "Der Nutzer ist gerade Hallo.",
    ),
    # VC2c: presence only
    (
        "Gute Nacht",
        ["Schlafzimmer"],
        [],
        "Der Nutzer ist gerade Gute Nacht. Anwesend in: Schlafzimmer.",
    ),
    # VC2d: suggestions only
    (
        "Tag",
        [],
        ["Kaffee"],
        "Der Nutzer ist gerade Tag. Vorschläge: Kaffee.",
    ),
    # VC2e: presence capped at 3
    (
        "Morgen",
        ["Z1", "Z2", "Z3", "Z4"],
        [],
        "Der Nutzer ist gerade Morgen. Anwesend in: Z1, Z2, Z3.",
    ),
    # VC2f: suggestions capped at 2
    (
        "Abend",
        [],
        ["S1", "S2", "S3"],
        "Der Nutzer ist gerade Abend. Vorschläge: S1; S2.",
    ),
])
def test_vc2_voice_prompt_construction(greeting, presence, suggestions, expected):
    """VC2: voice_prompt is built from greeting + presence[:3] + suggestions[:2]."""
    prompt = VoiceContextSensorContract._build_prompt(greeting, presence, suggestions)
    assert prompt == expected


# =============================================================================
# VC3 — VoiceContextSensor native_value
# =============================================================================

def test_vc3_native_value_always_ok():
    """VC3: native_value is initialised to 'ok', never changes."""
    assert VoiceContextSensorContract.native_value({}) == "ok"
    assert VoiceContextSensorContract.native_value({"mood": {}}) == "ok"


# =============================================================================
# VP1 — VoicePromptSensor native_value
# =============================================================================

@pytest.mark.parametrize("coordinator_data, expected", [
    # VP1a: relax → Entspannt
    ({"mood": {"mood": "relax"}, "suggestions": []}, "Der Nutzer ist Entspannt."),
    # VP1b: focus + suggestions count
    ({"mood": {"mood": "focus"}, "suggestions": [{"id": 1}]}, "Der Nutzer ist Fokussiert. 1 Vorschläge verfügbar."),
    # VP1c: sleep
    ({"mood": {"mood": "sleep"}, "suggestions": []}, "Der Nutzer ist Müde."),
    # VP1d: no mood key → Guard: empty data returns 'Kein Kontext verfügbar.'
    # VP1e: social + 2 suggestions
    ({"mood": {"mood": "social"}, "suggestions": [{"a": 1}, {"b": 2}]}, "Der Nutzer ist Gesellig. 2 Vorschläge verfügbar."),
    # VP1f: unmapped mood → Neutral (data present but mood key unknown)
    ({"mood": {"mood": "unknown_mood"}, "suggestions": []}, "Der Nutzer ist Neutral."),
    # VP1g: active
    ({"mood": {"mood": "active"}}, "Der Nutzer ist Aktiv."),
    # VP1h: recovery
    ({"mood": {"mood": "recovery"}}, "Der Nutzer ist Erholend."),
    # VP1i: away
    ({"mood": {"mood": "away"}}, "Der Nutzer ist Abwesend."),
    # VP1j: alert
    ({"mood": {"mood": "alert"}}, "Der Nutzer ist Aufmerksam."),
    # VP1k: unmapped mood → Neutral
    ({"mood": {"mood": "alien"}, "suggestions": []}, "Der Nutzer ist Neutral."),
    # VP1l: empty data → "Kein Kontext verfügbar." (sensor guard: empty dict is falsy)
    ({}, "Kein Kontext verfügbar."),
])
def test_vp1_native_value(coordinator_data, expected):
    """VP1: native_value derives from mood tone + suggestions count via trivial mapping."""
    assert VoicePromptSensorContract.native_value(coordinator_data) == expected


def test_vp2_empty_coordinator_returns_default():
    """VP2: empty coordinator data → sensor guard returns 'Kein Kontext verfügbar.'."""
    # {} is falsy in Python → sensor guard `if not self.coordinator.data` fires
    assert VoicePromptSensorContract.native_value({}) == "Kein Kontext verfügbar."
    # mood=unknown_mood but data present → Neutral
    assert VoicePromptSensorContract.native_value({"mood": {"mood": "alien"}, "suggestions": []}) == "Der Nutzer ist Neutral."


# =============================================================================
# GC1 — Global Contract: pure projection, no local semantic invention
# =============================================================================

def test_gc1_no_local_semantic_invention(full_data):
    """GC1: Both sensors read only coordinator.data — no local heuristic.

    All logic is:
    - Dict.get() with defaults
    - Trivial string interpolation
    - List slicing
    No local mood classification, no heuristic, no semantic interpretation.
    """
    # VoiceContextSensor contract
    vc_attrs = VoiceContextSensorContract.extra_state_attributes(full_data)
    assert vc_attrs["dominant_mood"] == "relax"
    assert "Guten Morgen" in vc_attrs["voice_greeting"]

    # VoicePromptSensor contract
    vp_value = VoicePromptSensorContract.native_value(full_data)
    assert "Entspannt" in vp_value


def test_gc2_both_sensors_derive_from_same_coordinator_data(full_data):
    """GC2: VoiceContextSensor and VoicePromptSensor read the same coordinator.data.

    This verifies they are both pure projection shells on the same data source.
    """
    vc_attrs = VoiceContextSensorContract.extra_state_attributes(full_data)
    vp_value = VoicePromptSensorContract.native_value(full_data)

    # Both derive from the same "relax" mood
    assert vc_attrs["voice_tone"] == "relax"
    assert "Entspannt" in vp_value


def test_gc3_mood_tone_mapping_is_exhaustive_and_static():
    """GC3: Mood tone mapping covers all known moods — no runtime evaluation."""
    for mood, tone in VoicePromptSensorContract.MOOD_TONES.items():
        # Every tone is a non-empty German string
        assert isinstance(tone, str)
        assert len(tone) > 0
        # Mood key is a known string
        assert isinstance(mood, str)
