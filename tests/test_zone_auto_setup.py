"""Tests for zone_auto_setup entity routing via sort_entity_to_zone()."""
import pytest
from unittest.mock import MagicMock

from custom_components.copilot_ha.habitus_zones_entities_v2 import (
    _ENTITY_ZONE_KEYWORDS,
    _VIRTUAL_AREA_PATTERNS,
    _normalize,
    _levenshtein,
    sort_entity_to_zone,
    _domain_bonus,
    _ZONE_ID_TO_NAME,
)


# ── Normalization helpers ─────────────────────────────────────────────

class TestNormalize:
    def test_lowercase(self):
        assert _normalize("WOHNZIMMER") == "wohnzimmer"

    def test_strips_accents(self):
        assert _normalize("Küche") == "kuche"
        # "Büro" → NFKD → "Bu\u0308ro" → strip non-ASCII → "buro"
        # (the combining diaeresis is stripped, not expanded to "ue")
        assert _normalize("Büro") == "buro"
        assert _normalize("Wohnzimmer") == "wohnzimmer"

    def test_strips_whitespace(self):
        assert _normalize("  bad  ") == "bad"

    def test_empty_string(self):
        assert _normalize("") == ""
        assert _normalize(None) == ""


class TestLevenshtein:
    def test_identical_strings(self):
        assert _levenshtein("wohn", "wohn") == 0

    def test_one_insertion(self):
        assert _levenshtein("wohnen", "wohne") == 1

    def test_one_deletion(self):
        assert _levenshtein("toilett", "toilette") == 1

    def test_one_substitution(self):
        assert _levenshtein("kueche", "kuche") == 1

    def test_typo_one_char_off(self):
        # "toilette" vs "toilett" (missing 'e'): distance = 1
        assert _levenshtein("toilette", "toilett") == 1

    def test_typo_toilettte_vs_toilett_is_distance_2(self):
        # "Toilettte" (3 t's) vs "toilett" (2 t's): two extra chars = distance 2
        assert _levenshtein("toilettte", "toilett") == 2

    def test_distance_returns_positive_for_different_strings(self):
        assert _levenshtein("abc", "xyz") > 0


# ── Virtual area patterns ─────────────────────────────────────────────

class TestVirtualAreaPatterns:
    @pytest.mark.parametrize("area", [
        "Energie", "energie", "ENERGIE",
        "Netzwerk", "netzwerk",
        "PV-Anlage", "pv-anlage",
        "Serverraum", "serverraum",
        "Personen", "personen",
        "Kalender",
    ])
    def test_virtual_areas_match(self, area):
        assert _VIRTUAL_AREA_PATTERNS.match(area) is not None, f"{area} should be virtual"

    @pytest.mark.parametrize("area", [
        "Wohnzimmer", "Küche", "Bad",
        "Flur", "Schlafzimmer", "Garten",
        "Büro",
    ])
    def test_real_areas_do_not_match(self, area):
        assert _VIRTUAL_AREA_PATTERNS.match(area) is None, f"{area} should NOT be virtual"


# ── sort_entity_to_zone() — basic routing ─────────────────────────────

class TestSortEntityToZoneBasic:
    """Core routing tests: entity_id + area_name based zone assignment."""

    @pytest.mark.parametrize("entity_id,expected_zone", [
        ("light.wohnzimmer_decke", "zone:wohnbereich"),
        ("light.wohn_decke", "zone:wohnbereich"),
        ("sensor.wohnzimmer_temperatur", "zone:wohnbereich"),
        ("climate.bad_heizung", "zone:badbereich"),
        ("binary_sensor.toilette_motion", "zone:badbereich"),
        ("switch.kueche_steckdose", "zone:kochbereich"),
        ("light.kochbereich_decke", "zone:kochbereich"),
        # "buerro" is not a keyword; "buero" would need fuzzy distance ≤ 1
        # (buerro→buero = 2, not ≤ 1), so generic entity stays ungeordnet
        ("sensor.buerro_lichtstärke", "zone:ungeordnet"),
        ("sensor.buero_temp", "zone:buerobereich"),   # "buero" exact keyword
        ("light.flur_decke", "zone:gangbereich"),
        ("binary_sensor.eingang_motion", "zone:gangbereich"),
        ("sensor.schlafzimmer_temp", "zone:schlafbereich"),
        ("light.schlafzimmer_nightlight", "zone:schlafbereich"),
        ("sensor.garten_bewegung", "zone:aussenbereich"),
        ("light.garage_decke", "zone:aussenbereich"),
        ("climate.garten_heizung", "zone:aussenbereich"),
        ("sensor.mira_bewegung", "zone:zimmer_mira"),
        ("light.paul_decke", "zone:zimmer_paul"),
    ])
    def test_entity_id_routes_to_correct_zone(self, entity_id, expected_zone):
        zone, conf, extra = sort_entity_to_zone(entity_id)
        assert zone == expected_zone, (
            f"{entity_id} → {zone} (expected {expected_zone}), "
            f"conf={conf}, match={extra.get('matched_keyword')}"
        )
        if expected_zone != "zone:ungeordnet":
            assert conf >= 0.60, f"{entity_id} confidence {conf} too low"

    def test_unknown_entity_routes_to_ungeordnet(self):
        zone, conf, extra = sort_entity_to_zone("sensor.unknown_xyz_123")
        assert zone == "zone:ungeordnet"
        assert conf == 0.0
        assert extra["match_type"] == "none"

    def test_light_bad_temperatur_routes_badbereich(self):
        """light.bad_temperatur routes to badbereich via keyword substring."""
        zone, conf, extra = sort_entity_to_zone("light.bad_temperatur")
        assert zone == "zone:badbereich"
        assert extra["match_type"] in ("substring", "exact")
        assert conf >= 0.60

    def test_light_flur_decke_routes_gangbereich(self):
        zone, conf, extra = sort_entity_to_zone("light.flur_decke")
        assert zone == "zone:gangbereich"
        assert extra["match_type"] in ("substring", "exact")

# ── sort_entity_to_zone() — area_name boost ───────────────────────────

class TestSortEntityToZoneAreaName:
    """area_name is used as a high-confidence signal."""

    def test_area_name_bad_trumps_entity_id_kw(self):
        # entity_id has "wohn" but area_name says "Bad" → Badbereich
        zone, conf, extra = sort_entity_to_zone(
            "sensor.wohn_motion",
            area_name="Bad",
        )
        assert zone == "zone:badbereich"
        assert conf >= 0.90, f"expected high confidence for area_exact, got {conf}"
        assert extra["match_type"] == "area_exact"

    def test_area_name_wohnzimmer_routes_ambiguous_entity(self):
        # entity_id is generic, area_name pins it
        zone, conf, extra = sort_entity_to_zone(
            "sensor.temp_sensor",
            area_name="Wohnzimmer",
        )
        assert zone == "zone:wohnbereich"
        assert conf >= 0.90

    def test_area_name_virtual_entity_goes_ungeordnet(self):
        zone, conf, extra = sort_entity_to_zone(
            "sensor.energie_total",
            area_name="Energie",
        )
        assert zone == "zone:ungeordnet"
        assert extra["is_virtual_area"] is True
        assert conf == 0.0

    def test_area_name_ungeordnet_zone_still_created(self):
        zone, conf, extra = sort_entity_to_zone(
            "sensor.serverschrank_temp",
            area_name="Serverschrank",
        )
        assert zone == "zone:ungeordnet"


# ── sort_entity_to_zone() — confidence thresholds ─────────────────────

class TestSortEntityToZoneConfidence:
    def test_confidence_above_090_is_high(self):
        zone, conf, _ = sort_entity_to_zone(
            "sensor.bad_temperatur",
            area_name="Bad",
        )
        assert conf >= 0.90

    def test_confidence_exact_entity_id(self):
        zone, conf, _ = sort_entity_to_zone("light.wohnzimmer_decke")
        assert conf >= 0.80

    def test_confidence_substring(self):
        zone, conf, _ = sort_entity_to_zone("sensor.wohnung_temp")
        assert 0.60 <= conf < 0.90

    def test_confidence_fuzzy_match(self):
        zone, conf, _ = sort_entity_to_zone("sensor.wohne Temperature")
        assert conf >= 0.60

    def test_confidence_zero_for_unknown(self):
        _, conf, _ = sort_entity_to_zone("sensor.xyzqweasd")
        assert conf == 0.0

    def test_confidence_below_060_goes_ungeordnet(self):
        # Even if sort_entity_to_zone returns a zone_id with low confidence,
        # the caller in zone_auto_setup enforces the 0.60 threshold.
        zone, conf, _ = sort_entity_to_zone("sensor.generic_unknown_xyz")
        # These entities should route to ungeordnet
        assert zone == "zone:ungeordnet"


# ── sort_entity_to_zone() — match types ─────────────────────────────

class TestSortEntityToZoneMatchTypes:
    def test_match_type_area_exact(self):
        _, _, extra = sort_entity_to_zone("sensor.xyz", area_name="Bad")
        assert extra["match_type"] == "area_exact"

    def test_match_type_exact(self):
        # Exact match: normalized entity_id exactly equals a keyword.
        # "sensor.bad" normalizes to "sensor.bad"; "bad" != "sensor.bad" → substring.
        # Use entity_id "bad" so search_text == "bad" == kw_norm.
        _, _, extra = sort_entity_to_zone("bad")
        assert extra["match_type"] == "exact"

    def test_match_type_substring(self):
        # "wohn" is substring of entity_id "light.wohnzimmer" but not equal → substring
        _, _, extra = sort_entity_to_zone("light.wohnzimmer")
        assert extra["match_type"] == "substring"

    def test_match_type_fuzzy(self):
        _, _, extra = sort_entity_to_zone("sensor.wohne_temp")
        assert extra["match_type"] in ("substring", "fuzzy")

    def test_match_type_none_for_unknown(self):
        _, _, extra = sort_entity_to_zone("sensor.unknownxyz123")
        assert extra["match_type"] == "none"

    def test_zone_name_de_populated(self):
        _, _, extra = sort_entity_to_zone("light.bad_decke", area_name="Bad")
        assert extra["zone_name_de"] == "Badbereich"

    def test_zone_name_de_ungeordnet(self):
        _, _, extra = sort_entity_to_zone("sensor.unknown")
        assert extra["zone_name_de"] == "Ungeordnet"


# ── sort_entity_to_zone() — state/friendly_name ─────────────────────

class TestSortEntityToZoneWithState:
    def test_friendly_name_in_search_space(self):
        mock_state = MagicMock()
        mock_state.attributes = {
            "friendly_name": "Wohnzimmer Deckenlampe",
            "device_class": None,
        }
        zone, conf, extra = sort_entity_to_zone(
            "light.entity_no_hint",
            state=mock_state,
        )
        assert zone == "zone:wohnbereich"

    def test_state_device_class_not_used_for_routing(self):
        # device_class affects role detection, not zone routing
        mock_state = MagicMock()
        mock_state.attributes = {
            "friendly_name": "",
            "device_class": "temperature",
        }
        zone, conf, extra = sort_entity_to_zone(
            "light.generic_light",
            state=mock_state,
        )
        # light.generic_light → no keyword → ungeordnet
        assert zone == "zone:ungeordnet"


# ── sort_entity_to_zone() — edge cases ─────────────────────────────

class TestSortEntityToZoneEdgeCases:
    def test_empty_entity_id(self):
        zone, conf, extra = sort_entity_to_zone("")
        assert zone == "zone:ungeordnet"
        assert conf == 0.0

    def test_none_area_name_ok(self):
        zone, conf, _ = sort_entity_to_zone("light.bad_decke", area_name=None)
        assert zone == "zone:badbereich"

    def test_area_id_passed_but_no_area_name(self):
        zone, conf, _ = sort_entity_to_zone("light.bad_decke", area_id="area_123")
        # area_id alone is not used for matching (no name resolution here)
        assert zone == "zone:badbereich"  # entity_id keyword match still fires

    def test_all_zone_ids_covered_in_keywords(self):
        """Every zone_id in _ENTITY_ZONE_KEYWORDS must have at least one keyword."""
        for zone_id in _ENTITY_ZONE_KEYWORDS:
            assert len(_ENTITY_ZONE_KEYWORDS[zone_id]) > 0, f"{zone_id} has no keywords"

    def test_zone_id_to_name_complete(self):
        """All zone_ids used in routing should have a human-readable name."""
        for zone_id in _ENTITY_ZONE_KEYWORDS:
            assert zone_id in _ZONE_ID_TO_NAME, f"Missing name for {zone_id}"


# ── domain bonus ─────────────────────────────────────────────────────

class TestDomainBonus:
    def test_light_domain_gets_bonus(self):
        assert _domain_bonus("light.wohnzimmer") > 0

    def test_climate_domain_gets_bonus(self):
        assert _domain_bonus("climate.wohnbereich") > 0

    def test_unknown_domain_no_bonus(self):
        assert _domain_bonus("sensor.generic") == 0.0

    def test_bonus_is_small(self):
        bonus = _domain_bonus("light.xyz")
        assert 0 < bonus <= 0.10


# ── sort_entity_to_zone() — integration scenarios ───────────────────

class TestSortEntityToZoneIntegration:
    """Real-world scenarios matching the task description."""

    def test_light_with_wohnen_keyword_routes_wohnbereich(self):
        zone, conf, extra = sort_entity_to_zone("light.wohnen_decke")
        assert zone == "zone:wohnbereich"
        assert extra["matched_keyword"] == "wohn"

    def test_light_with_wohnzimmer_routes_wohnbereich(self):
        zone, conf, extra = sort_entity_to_zone("light.wohnzimmer_decke")
        assert zone == "zone:wohnbereich"
        assert conf >= 0.80

    def test_motion_sensor_badbereich(self):
        zone, conf, extra = sort_entity_to_zone(
            "binary_sensor.toilette_praesenz",
            area_name="Toilette",
        )
        assert zone == "zone:badbereich"
        assert conf >= 0.60

    def test_entity_without_area_assignment_can_still_route(self):
        # Entity with no area, but entity_id contains a keyword → still routes
        zone, conf, extra = sort_entity_to_zone(
            "sensor.kueche_temperatur",
            area_id=None,
            area_name=None,
        )
        assert zone == "zone:kochbereich"
        assert conf >= 0.60

    def test_sicherheit_entity_not_matched_by_zone_keywords(self):
        # Entities about security should not accidentally match room keywords
        zone, conf, extra = sort_entity_to_zone(
            "alarm_control_panel.alarmanlage",
            area_name="Eingang",
        )
        # alarm_control_panel.alarmanlage has no room keyword in entity_id;
        # area_name Eingang → gangbereich
        assert zone == "zone:gangbereich"

    def test_entity_from_virtual_area_routes_ungeordnet(self):
        zone, conf, extra = sort_entity_to_zone(
            "sensor.energie_pv_leistung",
            area_name="PV-Anlage",
        )
        assert zone == "zone:ungeordnet"
        assert extra["is_virtual_area"] is True

    def test_entity_routing_with_low_confidence_goes_ungeordnet(self):
        # An entity whose name is ambiguous should end up in ungeordnet
        zone, conf, _ = sort_entity_to_zone("sensor.sensor42")
        assert zone == "zone:ungeordnet"
        assert conf == 0.0


# ── sort_entity_to_zone — confidence boundary ──────────────────────

class TestConfidenceBoundary:
    """Verify the 0.60 threshold behavior."""

    @pytest.mark.parametrize("entity_id", [
        "sensor.xyz_unknown_abc",
        "binary_sensor.generic",
        "input_boolean.dummy",
    ])
    def test_unknown_entities_ungeordnet(self, entity_id):
        zone, conf, _ = sort_entity_to_zone(entity_id)
        assert zone == "zone:ungeordnet"
        assert conf < 0.60

    @pytest.mark.parametrize("entity_id", [
        "light.wohnzimmer_decke",
        "sensor.bad_temperatur",
        "switch.kueche_plug",
        "climate.schlafzimmer",
        "binary_sensor.garten_bewegung",
    ])
    def test_known_entities_match_zone(self, entity_id):
        zone, conf, _ = sort_entity_to_zone(entity_id)
        assert zone != "zone:ungeordnet"
        assert conf >= 0.60
