"""Tests for smart zone auto-setup (area aggregation + entity role detection)."""
import pytest

from custom_components.copilot_ha.zone_auto_setup import (
    HABITUS_ZONE_TEMPLATES,
    ROLE_NEURON_TYPE_MAP,
    NEURON_TAG_META,
    aggregate_areas_to_habitus_zones,
    async_create_neuron_tags_from_zones,
    detect_entity_role,
    detect_entity_tags,
    _is_virtual_area,
    _match_area_to_template,
)


class TestAreaToTemplateMatching:
    """Test keyword-based area → template matching."""

    def test_wohnzimmer_matches_wohnbereich(self):
        template, conf = _match_area_to_template("Wohnzimmer")
        assert template is not None
        assert template["zone_id"] == "wohnbereich"
        assert conf >= 0.8

    def test_bad_matches_badbereich(self):
        template, conf = _match_area_to_template("Bad")
        assert template is not None
        assert template["zone_id"] == "badbereich"

    def test_toilette_matches_badbereich(self):
        template, conf = _match_area_to_template("Toilette")
        assert template is not None
        assert template["zone_id"] == "badbereich"

    def test_kueche_matches_kochbereich(self):
        template, conf = _match_area_to_template("Küche")
        assert template is not None
        assert template["zone_id"] == "kochbereich"

    def test_flur_matches_gangbereich(self):
        template, conf = _match_area_to_template("Flur")
        assert template is not None
        assert template["zone_id"] == "gangbereich"

    def test_gang_matches_gangbereich(self):
        template, conf = _match_area_to_template("Gang")
        assert template is not None
        assert template["zone_id"] == "gangbereich"

    def test_schlafzimmer_matches_schlafbereich(self):
        template, conf = _match_area_to_template("Schlafzimmer")
        assert template is not None
        assert template["zone_id"] == "schlafbereich"

    def test_buero_matches_buerobereich(self):
        template, conf = _match_area_to_template("Büro")
        assert template is not None
        assert template["zone_id"] == "buerobereich"

    def test_garten_matches_aussenbereich(self):
        template, conf = _match_area_to_template("Garten")
        assert template is not None
        assert template["zone_id"] == "aussenbereich"

    def test_keller_matches_kellerbereich(self):
        template, conf = _match_area_to_template("Keller")
        assert template is not None
        assert template["zone_id"] == "kellerbereich"

    def test_kinderzimmer_matches(self):
        template, conf = _match_area_to_template("Kinderzimmer")
        assert template is not None
        assert template["zone_id"] == "kinderzimmer"

    def test_terrasse_matches(self):
        template, conf = _match_area_to_template("Terrasse")
        assert template is not None
        assert template["zone_id"] == "aussenbereich"

    def test_unknown_area_no_match(self):
        template, conf = _match_area_to_template("Serverschrank")
        assert template is None
        assert conf == 0.0

    def test_esszimmer_matches_wohnbereich(self):
        template, conf = _match_area_to_template("Esszimmer")
        assert template is not None
        assert template["zone_id"] == "wohnbereich"

    def test_dusche_matches_badbereich(self):
        template, conf = _match_area_to_template("Dusche")
        assert template is not None
        assert template["zone_id"] == "badbereich"

    def test_eingang_matches_gangbereich(self):
        template, conf = _match_area_to_template("Eingang")
        assert template is not None
        assert template["zone_id"] == "gangbereich"

    def test_loft_matches_wohnbereich(self):
        template, conf = _match_area_to_template("Loft")
        assert template is not None
        assert template["zone_id"] == "wohnbereich"

    def test_fuzzy_toilettte_typo_matches_badbereich(self):
        """Typo tolerance: 'Toilettte' (triple t) should still match badbereich."""
        template, conf = _match_area_to_template("Toilettte")
        assert template is not None
        assert template["zone_id"] == "badbereich"
        assert conf >= 0.6


class TestVirtualAreaFilter:
    """Test virtual/organizational area detection."""

    def test_energie_is_virtual(self):
        assert _is_virtual_area("Energie") is True

    def test_netzwerk_is_virtual(self):
        assert _is_virtual_area("Netzwerk") is True

    def test_kontrollraum_is_virtual(self):
        assert _is_virtual_area("Kontrollraum") is True

    def test_personen_is_virtual(self):
        assert _is_virtual_area("Personen") is True

    def test_pv_anlage_is_virtual(self):
        assert _is_virtual_area("PV-Anlage") is True

    def test_wohnzimmer_is_not_virtual(self):
        assert _is_virtual_area("Wohnzimmer") is False

    def test_kueche_is_not_virtual(self):
        assert _is_virtual_area("Küche") is False

    def test_virtual_areas_excluded_from_aggregation(self):
        areas = [
            {"area_id": "wz", "name": "Wohnzimmer"},
            {"area_id": "en", "name": "Energie"},
            {"area_id": "nw", "name": "Netzwerk"},
        ]
        zones = aggregate_areas_to_habitus_zones(areas)
        zone_ids = {z["zone_id"] for z in zones}
        assert "zone:wohnbereich" in zone_ids
        # Virtual areas should not appear
        assert not any("energie" in zid for zid in zone_ids)
        assert not any("netzwerk" in zid for zid in zone_ids)


class TestAggregation:
    """Test smart area aggregation into Habitus Zones."""

    def test_toilet_and_bad_aggregate_to_badbereich(self):
        areas = [
            {"area_id": "a1", "name": "Bad"},
            {"area_id": "a2", "name": "Toilette"},
        ]
        zones = aggregate_areas_to_habitus_zones(areas)
        bad_zones = [z for z in zones if z["zone_id"] == "zone:badbereich"]
        assert len(bad_zones) == 1
        assert set(bad_zones[0]["area_ids"]) == {"a1", "a2"}
        assert bad_zones[0]["aggregated"] is True

    def test_flur_and_gang_aggregate_to_gangbereich(self):
        areas = [
            {"area_id": "a1", "name": "Flur"},
            {"area_id": "a2", "name": "Gang"},
        ]
        zones = aggregate_areas_to_habitus_zones(areas)
        gang_zones = [z for z in zones if z["zone_id"] == "zone:gangbereich"]
        assert len(gang_zones) == 1
        assert set(gang_zones[0]["area_ids"]) == {"a1", "a2"}

    def test_mixed_areas_produce_correct_zones(self):
        areas = [
            {"area_id": "wz", "name": "Wohnzimmer"},
            {"area_id": "bad", "name": "Badezimmer"},
            {"area_id": "wc", "name": "WC"},
            {"area_id": "ku", "name": "Küche"},
            {"area_id": "fl", "name": "Flur"},
            {"area_id": "ga", "name": "Gang"},
            {"area_id": "sz", "name": "Schlafzimmer"},
            {"area_id": "ga2", "name": "Garten"},
            {"area_id": "srv", "name": "Serverschrank"},
        ]
        zones = aggregate_areas_to_habitus_zones(areas)
        zone_ids = {z["zone_id"] for z in zones}

        # Check expected aggregations
        assert "zone:badbereich" in zone_ids     # Bad + WC
        assert "zone:gangbereich" in zone_ids    # Flur + Gang
        assert "zone:wohnbereich" in zone_ids    # Wohnzimmer
        assert "zone:kochbereich" in zone_ids    # Küche
        assert "zone:schlafbereich" in zone_ids  # Schlafzimmer
        assert "zone:aussenbereich" in zone_ids  # Garten

        # Serverschrank is unmatched → standalone zone
        srv_zones = [z for z in zones if "serverschrank" in z["zone_id"]]
        assert len(srv_zones) == 1
        assert srv_zones[0]["aggregated"] is False

        # Badbereich should have 2 areas
        bad = next(z for z in zones if z["zone_id"] == "zone:badbereich")
        assert len(bad["area_ids"]) == 2

    def test_empty_areas_returns_empty(self):
        assert aggregate_areas_to_habitus_zones([]) == []

    def test_single_area(self):
        zones = aggregate_areas_to_habitus_zones([{"area_id": "x", "name": "Küche"}])
        assert len(zones) == 1
        assert zones[0]["zone_id"] == "zone:kochbereich"
        assert zones[0]["aggregated"] is False


class TestEntityRoleDetection:
    """Test automatic entity role detection."""

    def test_light_entity(self):
        assert detect_entity_role("light.wohnzimmer_decke") == "lights"

    def test_motion_binary_sensor(self):
        assert detect_entity_role(
            "binary_sensor.flur_motion", device_class="motion"
        ) == "motion"

    def test_motion_by_name(self):
        assert detect_entity_role("binary_sensor.praesenz_wohnzimmer") == "motion"

    def test_temperature_sensor(self):
        assert detect_entity_role(
            "sensor.bad_temperatur", device_class="temperature"
        ) == "temperature"

    def test_humidity_sensor(self):
        assert detect_entity_role(
            "sensor.bad_humidity", device_class="humidity"
        ) == "humidity"

    def test_media_player(self):
        assert detect_entity_role("media_player.sonos_wohnzimmer") == "media"

    def test_climate(self):
        assert detect_entity_role("climate.bad_heizung") == "heating"

    def test_cover(self):
        assert detect_entity_role("cover.wohnzimmer_rollladen") == "cover"

    def test_lock(self):
        assert detect_entity_role("lock.haustuer") == "lock"

    def test_energy_sensor(self):
        assert detect_entity_role("sensor.strom_verbrauch") == "power"

    def test_illuminance_sensor(self):
        assert detect_entity_role("sensor.helligkeit_flur") == "brightness"

    def test_window_binary_sensor(self):
        assert detect_entity_role(
            "binary_sensor.fenster_bad", device_class="window"
        ) == "window"

    def test_door_binary_sensor(self):
        assert detect_entity_role(
            "binary_sensor.haustuer", device_class="door"
        ) == "door"


class TestEntityTagDetection:
    """Test automatic entity tag detection."""

    def test_light_tag(self):
        tags = detect_entity_tags("light.decke", "lights")
        assert "licht" in tags

    def test_motion_tag(self):
        tags = detect_entity_tags("binary_sensor.motion", "motion")
        assert "praesenz" in tags

    def test_climate_tag(self):
        tags = detect_entity_tags("climate.heizung", "heating")
        assert "klima" in tags

    def test_cover_tag(self):
        tags = detect_entity_tags("cover.rollladen", "cover")
        assert "rollladen" in tags

    def test_styx_entity_gets_styx_tag(self):
        tags = detect_entity_tags("sensor.pilotsuite_mood", "other")
        assert "styx" in tags

    def test_no_duplicate_tags(self):
        tags = detect_entity_tags("sensor.licht_energie", "energy")
        assert len(tags) == len(set(tags))


class TestTemplateCompleteness:
    """Verify template system covers common German room names."""

    @pytest.mark.parametrize("room_name,expected_zone", [
        ("Wohnzimmer", "wohnbereich"),
        ("Esszimmer", "wohnbereich"),
        ("Loft", "wohnbereich"),
        ("Badezimmer", "badbereich"),
        ("Toilette", "badbereich"),
        ("WC", "badbereich"),
        ("Küche", "kochbereich"),
        ("Büro", "buerobereich"),
        ("Homeoffice", "buerobereich"),
        ("Flur", "gangbereich"),
        ("Diele", "gangbereich"),
        ("Eingang", "gangbereich"),
        ("Schlafzimmer", "schlafbereich"),
        ("Kinderzimmer", "kinderzimmer"),
        ("Terrasse", "aussenbereich"),
        ("Balkon", "aussenbereich"),
        ("Loggia", "aussenbereich"),
        ("Garten", "aussenbereich"),
        ("Garage", "aussenbereich"),
        ("Keller", "kellerbereich"),
    ])
    def test_room_matches_expected_zone(self, room_name, expected_zone):
        template, conf = _match_area_to_template(room_name)
        assert template is not None, f"{room_name} should match {expected_zone}"
        assert template["zone_id"] == expected_zone, (
            f"{room_name} matched {template['zone_id']} instead of {expected_zone}"
        )
        assert conf >= 0.6, f"{room_name} confidence {conf} too low"


class TestNeuronTypeMapping:
    """Test role → neuron type classification."""

    def test_temperature_is_context(self):
        assert ROLE_NEURON_TYPE_MAP["temperature"] == "context"

    def test_humidity_is_context(self):
        assert ROLE_NEURON_TYPE_MAP["humidity"] == "context"

    def test_energy_is_context(self):
        assert ROLE_NEURON_TYPE_MAP["energy"] == "context"

    def test_motion_is_state(self):
        assert ROLE_NEURON_TYPE_MAP["motion"] == "state"

    def test_door_is_state(self):
        assert ROLE_NEURON_TYPE_MAP["door"] == "state"

    def test_lock_is_state(self):
        assert ROLE_NEURON_TYPE_MAP["lock"] == "state"

    def test_lights_is_mood(self):
        assert ROLE_NEURON_TYPE_MAP["lights"] == "mood"

    def test_media_is_mood(self):
        assert ROLE_NEURON_TYPE_MAP["media"] == "mood"

    def test_all_three_types_covered(self):
        types = set(ROLE_NEURON_TYPE_MAP.values())
        assert types == {"context", "state", "mood"}

    def test_neuron_tag_meta_has_all_types(self):
        assert set(NEURON_TAG_META.keys()) == {"context", "state", "mood"}

    def test_each_meta_has_color_and_icon(self):
        for ntype, meta in NEURON_TAG_META.items():
            assert "color" in meta, f"{ntype} missing color"
            assert "icon" in meta, f"{ntype} missing icon"

    def test_context_roles_are_environmental(self):
        context_roles = {r for r, t in ROLE_NEURON_TYPE_MAP.items() if t == "context"}
        assert context_roles == {"temperature", "humidity", "co2", "pressure", "energy", "power"}

    def test_state_roles_are_physical(self):
        state_roles = {r for r, t in ROLE_NEURON_TYPE_MAP.items() if t == "state"}
        assert state_roles == {"motion", "door", "window", "lock", "cover", "heating"}

    def test_mood_roles_are_comfort(self):
        mood_roles = {r for r, t in ROLE_NEURON_TYPE_MAP.items() if t == "mood"}
        assert mood_roles == {"lights", "brightness", "media", "noise"}
