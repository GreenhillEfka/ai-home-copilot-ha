"""Projection Contract Tests — voice_context sensors (HA-126).

Verifies VoiceContextSensor + VoicePromptSensor are pure Projection-Shells
on coordinator.data["mood"] / ["neural"] / ["suggestions"] — no local semantic invention.

Contract: both sensors derive ALL display values from coordinator.data via trivial
Dict-lookups and string formatting. No local classification, no heuristic, no
semantic interpretation beyond what Core provides.

HA-126 — 2026-04-06
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest


# =============================================================================
# Contract Mirrors
# =============================================================================

class VoiceContextSensorContract:
    """Mirror of VoiceContextSensor extra_state_attributes + native_value logic.

    Contract:
    - reads: coordinator.data["mood"], ["neural"]
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
                               (NOT from coordinator.data["suggestions"])
        voice_prompt        ← built from greeting + presence + suggestions
        last_update         ← neural.get("last_update", "")

    Note: coordinator.data["suggestions"] is intentionally not consumed.  Voice suggestions
    are derived solely from neural.zone.typical_activities to keep the HA Assist prompt
    grounded in factual zone activity rather than raw Core suggestion payloads.
    """

    @staticmethod
    def native_value(_coordinator_data: dict) -> str:
        return "ok"

    @staticmethod
    def _as_mapping(value) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return " ".join(value.split())

    @staticmethod
    def _as_string_list(value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [
            normalized
            for item in value
            if isinstance(item, str)
            if (normalized := VoiceContextSensorContract._normalize_whitespace(item))
        ]

    @staticmethod
    def _as_string(value, default: str) -> str:
        if not isinstance(value, str):
            return default
        normalized = VoiceContextSensorContract._normalize_whitespace(value)
        return normalized if normalized else default

    @staticmethod
    def _as_float(value, default: float) -> float:
        if isinstance(value, bool):
            return default
        if not isinstance(value, (int, float)):
            return default
        numeric_value = float(value)
        return numeric_value if math.isfinite(numeric_value) else default

    @staticmethod
    def extra_state_attributes(coordinator_data: dict) -> dict:
        coordinator_data = VoiceContextSensorContract._as_mapping(coordinator_data)
        if not coordinator_data:
            return {}

        mood = VoiceContextSensorContract._as_mapping(coordinator_data.get("mood", {}))
        neural = VoiceContextSensorContract._as_mapping(coordinator_data.get("neural", {}))

        dominant_mood = VoiceContextSensorContract._as_string(mood.get("mood"), "unknown")
        confidence = VoiceContextSensorContract._as_float(mood.get("confidence"), 0.0)
        core_time = VoiceContextSensorContract._as_mapping(neural.get("time", {}))
        time_greeting = (
            VoiceContextSensorContract._as_string(core_time.get("description_de"), "")
            or VoiceContextSensorContract._as_string(core_time.get("description_en"), "")
            or "Hallo"
        )
        core_zone = VoiceContextSensorContract._as_mapping(neural.get("zone", {}))
        zone_name = VoiceContextSensorContract._as_string(core_zone.get("current"), "unknown")
        zone_activities = VoiceContextSensorContract._as_string_list(
            core_zone.get("typical_activities", [])
        )
        voice_suggestions = [f"{act} ist aktuell." for act in zone_activities[:3]]
        presence = VoiceContextSensorContract._as_string_list(core_zone.get("presence"))
        if not presence:
            presence = VoiceContextSensorContract._as_string_list(neural.get("presence", []))

        return {
            "dominant_mood": dominant_mood,
            "mood_confidence": confidence,
            "mood_contributors": VoiceContextSensorContract._as_string_list(mood.get("contributors", [])),
            "current_zone": zone_name,
            "zone_presence": presence,
            "voice_tone": dominant_mood,
            "voice_greeting": time_greeting,
            "voice_suggestions": voice_suggestions,
            "voice_prompt": VoiceContextSensorContract._build_prompt(
                time_greeting, presence, voice_suggestions
            ),
            "last_update": VoiceContextSensorContract._as_string(neural.get("last_update", ""), ""),
        }

    @staticmethod
    def _build_prompt(greeting: str, presence: list, suggestions: list) -> str:
        greeting = VoiceContextSensorContract._as_string(greeting, "") or "Neutral"
        parts = [f"Der Nutzer ist gerade {greeting}."]
        presence = VoiceContextSensorContract._as_string_list(presence)
        if presence:
            zones = ", ".join(presence[:3])
            parts.append(f"Anwesend in: {zones}.")
        suggestions = VoiceContextSensorContract._as_string_list(suggestions)
        if suggestions:
            parts.append(f"Vorschläge: {'; '.join(suggestions[:2])}.")
        return " ".join(parts)


class VoicePromptSensorContract:
    """Mirror of VoicePromptSensor native_value logic.

    Contract:
    - reads: coordinator.data["mood"], ["neural"]
    - native_value:
        returns "Kein Kontext verfügbar." when coordinator.data empty
        otherwise projects the same greeting/presence/activity fields as
        VoiceContextSensor and returns the identical HA Assist prompt
    """

    @staticmethod
    def native_value(coordinator_data: dict) -> str:
        coordinator_data = VoiceContextSensorContract._as_mapping(coordinator_data)
        if not coordinator_data:
            return "Kein Kontext verfügbar."
        attrs = VoiceContextSensorContract.extra_state_attributes(coordinator_data)
        return attrs["voice_prompt"]


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
    # VC1m: malformed zone.typical_activities string must not be split char-wise
    (
        {"neural": {"zone": {"typical_activities": "Lesen"}}},
        "voice_suggestions",
        [],
    ),
    # VC1n: malformed zone.presence falls back to neural.presence list
    (
        {"neural": {"zone": {"presence": "Wohnzimmer"}, "presence": ["Küche"]}},
        "zone_presence",
        ["Küche"],
    ),
    # VC1o: non-dict mood/neural payloads stay on safe projection defaults
    (
        {"mood": ["relax"], "neural": "bad-payload"},
        "dominant_mood",
        "unknown",
    ),
    # VC1p: malformed scalar mood string payload falls back safely
    (
        {"mood": {"mood": ["relax"]}},
        "dominant_mood",
        "unknown",
    ),
    # VC1q: malformed confidence payload falls back to 0.0
    (
        {"mood": {"confidence": {"bad": 1}}},
        "mood_confidence",
        0.0,
    ),
    # VC1r: malformed contributors payload is filtered to safe empty list
    (
        {"mood": {"contributors": "music"}},
        "mood_contributors",
        [],
    ),
    # VC1r2: bool confidence payload must not leak Python bool-as-int semantics
    (
        {"mood": {"confidence": True}},
        "mood_confidence",
        0.0,
    ),
    # VC1r3: non-finite confidence payload falls back to documented safe default
    (
        {"mood": {"confidence": float("inf")}},
        "mood_confidence",
        0.0,
    ),
    # VC1s: malformed zone/time scalar payloads stay on safe defaults
    (
        {"neural": {"time": {"description_de": ["Hallo"]}, "zone": {"current": {"name": "Wohnzimmer"}}}},
        "voice_greeting",
        "Hallo",
    ),
    # VC1t: malformed last_update payload falls back to empty string
    (
        {"neural": {"last_update": ["2026-04-06T10:00:00Z"]}},
        "last_update",
        "",
    ),
    # VC1u: blank time descriptions fall back to Hallo at projection source
    (
        {"neural": {"time": {"description_de": "", "description_en": ""}}},
        "voice_greeting",
        "Hallo",
    ),
    # VC1u2: blank presence entries are filtered instead of leaking empty labels into HA attrs/prompt
    (
        {"neural": {"zone": {"presence": ["", "Küche", "   "]}}},
        "zone_presence",
        ["Küche"],
    ),
    # VC1u3: blank activities are filtered before voice suggestion projection
    (
        {"neural": {"zone": {"typical_activities": ["", "Lesen", "   "]}}},
        "voice_suggestions",
        ["Lesen ist aktuell."],
    ),
    # VC1u4: padded scalar/list payloads are normalized before projection into HA attrs
    (
        {
            "mood": {"mood": "  relax  ", "contributors": ["  music  ", " comfort "]},
            "neural": {
                "time": {"description_de": "  Guten Morgen  "},
                "zone": {
                    "current": "  Wohnzimmer  ",
                    "presence": ["  Wohnzimmer  ", " Küche "],
                    "typical_activities": ["  Lesen  ", " Musik hören "],
                },
                "last_update": " 2026-04-06T10:00:00Z ",
            },
        },
        None,
        {
            "dominant_mood": "relax",
            "mood_confidence": 0.0,
            "mood_contributors": ["music", "comfort"],
            "current_zone": "Wohnzimmer",
            "zone_presence": ["Wohnzimmer", "Küche"],
            "voice_tone": "relax",
            "voice_greeting": "Guten Morgen",
            "voice_suggestions": ["Lesen ist aktuell.", "Musik hören ist aktuell."],
            "voice_prompt": "Der Nutzer ist gerade Guten Morgen. Anwesend in: Wohnzimmer, Küche. Vorschläge: Lesen ist aktuell.; Musik hören ist aktuell..",
            "last_update": "2026-04-06T10:00:00Z",
        },
    ),
    # VC1u5: blank mood scalar falls back to documented default instead of leaking empty attrs
    (
        {"mood": {"mood": "   "}, "neural": {"zone": {"current": "   "}}},
        "dominant_mood",
        "unknown",
    ),
    # VC1u6: blank zone current scalar also falls back to documented default
    (
        {"neural": {"zone": {"current": "   "}}},
        "current_zone",
        "unknown",
    ),
    # VC1u7: embedded newlines/tabs collapse to stable single-space HA attrs and prompt fields
    (
        {
            "mood": {"mood": "\tdeep   focus\n", "contributors": ["  music\n", "\tlate   night\t"]},
            "neural": {
                "time": {"description_de": "  Guten\n\tMorgen  "},
                "zone": {
                    "current": "  Wohnzimmer\nNord  ",
                    "presence": ["  Wohnzimmer\nNord  ", "\tKüche\t"],
                    "typical_activities": ["  Lesen\n", "Musik\t hören  "],
                },
                "last_update": " 2026-04-06T10:00:00Z\n",
            },
        },
        None,
        {
            "dominant_mood": "deep focus",
            "mood_confidence": 0.0,
            "mood_contributors": ["music", "late night"],
            "current_zone": "Wohnzimmer Nord",
            "zone_presence": ["Wohnzimmer Nord", "Küche"],
            "voice_tone": "deep focus",
            "voice_greeting": "Guten Morgen",
            "voice_suggestions": ["Lesen ist aktuell.", "Musik hören ist aktuell."],
            "voice_prompt": "Der Nutzer ist gerade Guten Morgen. Anwesend in: Wohnzimmer Nord, Küche. Vorschläge: Lesen ist aktuell.; Musik hören ist aktuell..",
            "last_update": "2026-04-06T10:00:00Z",
        },
    ),
    # VC1v: truthy non-dict coordinator payload is rejected at the top-level guard
    (
        ["bad-payload"],
        None,
        {},
    ),
])
def test_vc1_extra_state_attributes(coordinator_data, key, expected):
    """VC1: extra_state_attributes are pure Dict lookups from coordinator.data."""
    attrs = VoiceContextSensorContract.extra_state_attributes(coordinator_data)
    if key is None:
        assert attrs == expected
        return
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
    # VC2g: malformed presence/suggestions strings are ignored instead of split char-wise
    (
        "Hallo",
        "Wohnzimmer",
        "Lesen",
        "Der Nutzer ist gerade Hallo.",
    ),
    # VC2h: malformed greeting payload falls back to Neutral instead of leaking reprs
    (
        ["Hallo"],
        [],
        [],
        "Der Nutzer ist gerade Neutral.",
    ),
    # VC2i: empty greeting payload also falls back to Neutral
    (
        "",
        [],
        [],
        "Der Nutzer ist gerade Neutral.",
    ),
    # VC2j: padded presence/suggestions are normalized before prompt construction
    (
        "  Hallo  ",
        ["  Wohnzimmer  ", " Küche "],
        ["  Lesen ist aktuell.  ", " Musik hören ist aktuell. "],
        "Der Nutzer ist gerade Hallo. Anwesend in: Wohnzimmer, Küche. Vorschläge: Lesen ist aktuell.; Musik hören ist aktuell..",
    ),
    # VC2k: embedded newlines/tabs collapse to stable single-line prompt text
    (
        "  Guten\n\tMorgen  ",
        ["  Wohnzimmer\nNord  ", "\tKüche\t"],
        ["  Lesen\n ist aktuell.  ", " Musik\t hören ist aktuell. "],
        "Der Nutzer ist gerade Guten Morgen. Anwesend in: Wohnzimmer Nord, Küche. Vorschläge: Lesen ist aktuell.; Musik hören ist aktuell..",
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
    # VP1a: german greeting from neural.time.description_de
    ({"mood": {"mood": "relax"}, "neural": {"time": {"description_de": "Guten Morgen"}}}, "Der Nutzer ist gerade Guten Morgen."),
    # VP1b: english fallback from neural.time.description_en
    ({"mood": {"mood": "focus"}, "neural": {"time": {"description_en": "Good morning"}}}, "Der Nutzer ist gerade Good morning."),
    # VP1c: presence is projected into the prompt
    ({"neural": {"time": {"description_de": "Abend"}, "zone": {"presence": ["Wohnzimmer", "Küche"]}}}, "Der Nutzer ist gerade Abend. Anwesend in: Wohnzimmer, Küche."),
    # VP1d: typical activities become projected suggestions in the prompt
    ({"neural": {"time": {"description_de": "Tag"}, "zone": {"typical_activities": ["Lesen", "Musik hören", "Kaffee"]}}}, "Der Nutzer ist gerade Tag. Vorschläge: Lesen ist aktuell.; Musik hören ist aktuell.."),
    # VP1e: blank time descriptions fall back to Hallo via shared projection
    ({"neural": {"time": {"description_de": "", "description_en": ""}}}, "Der Nutzer ist gerade Hallo."),
    # VP1f: empty data → sensor guard default
    ({}, "Kein Kontext verfügbar."),
    # VP1g: truthy non-dict coordinator payload also returns guard default
    (["bad-payload"], "Kein Kontext verfügbar."),
    # VP1h: padded scalar/list payloads are normalized before prompt projection
    ({"neural": {"time": {"description_de": "  Abend  "}, "zone": {"presence": ["  Wohnzimmer  "], "typical_activities": ["  Lesen  "]}}}, "Der Nutzer ist gerade Abend. Anwesend in: Wohnzimmer. Vorschläge: Lesen ist aktuell.."),
    # VP1i: embedded newlines/tabs are collapsed before prompt projection
    ({"neural": {"time": {"description_de": "  Guten\n\tMorgen  "}, "zone": {"presence": ["  Wohnzimmer\nNord  "], "typical_activities": ["  Musik\t hören  "]}}}, "Der Nutzer ist gerade Guten Morgen. Anwesend in: Wohnzimmer Nord. Vorschläge: Musik hören ist aktuell.."),
])
def test_vp1_native_value(coordinator_data, expected):
    """VP1: native_value is the projected HA Assist prompt, not a local tone mapping."""
    assert VoicePromptSensorContract.native_value(coordinator_data) == expected


def test_vp2_empty_coordinator_returns_default():
    """VP2: empty coordinator data → sensor guard returns 'Kein Kontext verfügbar.'."""
    assert VoicePromptSensorContract.native_value({}) == "Kein Kontext verfügbar."


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
    vc_attrs = VoiceContextSensorContract.extra_state_attributes(full_data)
    assert vc_attrs["dominant_mood"] == "relax"
    assert "Guten Morgen" in vc_attrs["voice_greeting"]

    vp_value = VoicePromptSensorContract.native_value(full_data)
    assert vp_value == vc_attrs["voice_prompt"]


def test_gc2_both_sensors_derive_from_same_coordinator_data(full_data):
    """GC2: VoiceContextSensor and VoicePromptSensor read the same coordinator.data.

    This verifies they are both pure projection shells on the same data source.
    """
    vc_attrs = VoiceContextSensorContract.extra_state_attributes(full_data)
    vp_value = VoicePromptSensorContract.native_value(full_data)

    assert vc_attrs["voice_tone"] == "relax"
    assert vp_value == vc_attrs["voice_prompt"]


def test_gc3_source_projects_core_voice_fields_directly():
    """GC3: voice_context.py projects Core fields directly for the HA-126 contract."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'description_de' in source
    assert 'description_en' in source
    assert 'typical_activities' in source
    assert 'zone_presence = _as_string_list(core_zone.get("presence"))' in source
    assert 'zone_presence = _as_string_list(neural_data.get("presence"))' in source
    assert 'f"{act} ist aktuell." for act in zone_activities[:3]' in source


def test_gc4_source_does_not_reintroduce_local_voice_semantics():
    """GC4: voice_context.py does not translate actions or invent local voice heuristics."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert '_action_to_voice' not in source
    assert 'suggestion_conf' not in source
    assert 'Licht einschalten' not in source
    assert 'Temperatur anpassen' not in source
    assert 'Medien steuern' not in source
    assert 'mood_tones' not in source
    assert 'Entspannt' not in source
    assert 'Fokussiert' not in source


def test_gc5_source_uses_shared_projection_backbone_for_both_sensors():
    """GC5: both sensors must share the same projection backbone and prompt builder."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'def _project_voice_context(' in source
    assert 'def _build_voice_prompt(context: Dict[str, Any]) -> str:' in source
    assert 'return _project_voice_context(mood_data, neural_data)' in source
    assert 'context = _project_voice_context(mood_data, neural_data)' in source
    assert 'return _build_voice_prompt(context)' in source


def test_gc6_source_blocks_split_prompt_paths_and_counting_semantics():
    """GC6: no split greeting keys, local tone field, or suggestion-count prompts."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'mood_data.get("tone", "neutral")' not in source
    assert 'greeting_de' not in source
    assert 'greeting_en' not in source
    assert 'Standort:' not in source
    assert 'Aktivitäten:' not in source
    assert 'Vorschläge verfügbar' not in source


def test_gc7_source_hardens_projection_against_malformed_list_payloads():
    """GC7: malformed strings/dicts must not be treated as presence/activity lists."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'def _as_string_list(value: Any) -> list[str]:' in source
    assert 'if not isinstance(value, list):' in source
    assert 'normalized := _normalize_whitespace(item)' in source


def test_gc8_source_hardens_projection_against_malformed_scalar_payloads():
    """GC8: malformed scalar payloads must not leak dict/list types into HA attrs/prompt."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'def _as_string(value: Any, default: str) -> str:' in source
    assert 'def _as_float(value: Any, default: float) -> float:' in source
    assert 'dominant_mood = _as_string(mood_data.get("mood"), "unknown")' in source
    assert 'if not isinstance(value, str):' in source
    assert 'normalized = _normalize_whitespace(value)' in source
    assert 'return normalized if normalized else default' in source
    assert 'if isinstance(value, bool):' in source
    assert 'math.isfinite' in source
    assert 'confidence = _as_float(mood_data.get("confidence"), 0.0)' in source
    assert 'zone_name = _as_string(core_zone.get("current"), "unknown")' in source
    assert 'or _as_string(core_time.get("description_en"), "")' in source
    assert 'or "Hallo"' in source
    assert 'greeting = _as_string(voice.get("greeting"), "") or "Neutral"' in source
    assert 'coordinator_data = _as_mapping(self.coordinator.data)' in source
    assert 'if not coordinator_data:' in source
    assert '"contributors": _as_string_list(mood_data.get("contributors"))' in source
    assert '"last_update": _as_string(neural_data.get("last_update"), "")' in source


def test_gc9_source_collapses_embedded_whitespace_in_projection_scalars_and_lists():
    """GC9: embedded newlines/tabs are normalized before HA attrs/prompt projection."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'def _normalize_whitespace(value: str) -> str:' in source
    assert 'return " ".join(value.split())' in source



def test_gc10_source_canonicalizes_voice_sensor_identity_and_migrates_legacy_ids():
    """GC10: voice_context sensors use pilotsuite IDs and migrate legacy ai_copilot IDs."""
    sensor_source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()
    init_source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "__init__.py"
    ).read_text()

    assert "sensor.pilotsuite_voice_context" in sensor_source
    assert '_attr_unique_id = "pilotsuite_voice_context"' in sensor_source
    assert '_attr_unique_id = "pilotsuite_voice_prompt"' in sensor_source
    assert "sensor.ai_copilot_voice_context" not in sensor_source
    assert '"ai_copilot_voice_context": "pilotsuite_voice_context"' in init_source
    assert '"ai_copilot_voice_prompt": "pilotsuite_voice_prompt"' in init_source



def test_gc11_source_never_consumes_raw_suggestions_payload():
    """GC11: voice_context projection must stay grounded in zone activities, not raw suggestions."""
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "voice_context.py"
    ).read_text()

    assert 'Note: coordinator.data["suggestions"] is intentionally not consumed here.' in source
    assert 'Voice suggestions are derived solely from neural.zone.typical_activities' in source
    assert 'coordinator_data.get("suggestions")' not in source
    assert 'self.coordinator.data.get("suggestions")' not in source
    assert 'neural_data.get("suggestions")' not in source
    assert 'mood_data.get("suggestions")' not in source
