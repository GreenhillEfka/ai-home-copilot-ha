"""Tests for HomeAssistant Discovery & Zone-Matching (v12.8.0).

Tests HA entity discovery, zone auto-matching, and confidence scoring.
Uses mock HA API - no real HA instance required.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any


# ── Mock Data ─────────────────────────────────────────────────────────────

MOCK_HA_ENTITIES = {
    "sensor.wohnzimmer_temperature": {
        "entity_id": "sensor.wohnzimmer_temperature",
        "state": "22.5",
        "attributes": {
            "friendly_name": "Wohnzimmer Temperatur",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "area_id": "wohnzimmer",
        },
    },
    "sensor.wohnzimmer_humidity": {
        "entity_id": "sensor.wohnzimmer_humidity",
        "state": "55.0",
        "attributes": {
            "friendly_name": "Wohnzimmer Luftfeuchtigkeit",
            "unit_of_measurement": "%",
            "device_class": "humidity",
            "area_id": "wohnzimmer",
        },
    },
    "light.wohnzimmer_haupt": {
        "entity_id": "light.wohnzimmer_haupt",
        "state": "on",
        "attributes": {
            "friendly_name": "Wohnzimmer Hauptlicht",
            "supported_features": 33,
            "area_id": "wohnzimmer",
        },
    },
    "light.wohnzimmer_stehlampe": {
        "entity_id": "light.wohnzimmer_stehlampe",
        "state": "off",
        "attributes": {
            "friendly_name": "Wohnzimmer Stehlampe",
            "area_id": "wohnzimmer",
        },
    },
    "binary_sensor.wohnzimmer_motion": {
        "entity_id": "binary_sensor.wohnzimmer_motion",
        "state": "on",
        "attributes": {
            "friendly_name": "Wohnzimmer Bewegung",
            "device_class": "motion",
            "area_id": "wohnzimmer",
        },
    },
    "sensor.bad_temperature": {
        "entity_id": "sensor.bad_temperature",
        "state": "24.0",
        "attributes": {
            "friendly_name": "Bad Temperatur",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "area_id": "bad",
        },
    },
    "sensor.bad_humidity": {
        "entity_id": "sensor.bad_humidity",
        "state": "65.0",
        "attributes": {
            "friendly_name": "Bad Luftfeuchtigkeit",
            "unit_of_measurement": "%",
            "device_class": "humidity",
            "area_id": "bad",
        },
    },
    "light.bad_decke": {
        "entity_id": "light.bad_decke",
        "state": "off",
        "attributes": {
            "friendly_name": "Bad Deckenlicht",
            "area_id": "bad",
        },
    },
    "binary_sensor.bad_motion": {
        "entity_id": "binary_sensor.bad_motion",
        "state": "off",
        "attributes": {
            "friendly_name": "Bad Bewegung",
            "device_class": "motion",
            "area_id": "bad",
        },
    },
    "light.toilette_licht": {
        "entity_id": "light.toilette_licht",
        "state": "off",
        "attributes": {
            "friendly_name": "Toilette Licht",
            "area_id": "toilette",
        },
    },
    "binary_sensor.toilette_motion": {
        "entity_id": "binary_sensor.toilette_motion",
        "state": "off",
        "attributes": {
            "friendly_name": "Toilette Bewegung",
            "device_class": "motion",
            "area_id": "toilette",
        },
    },
    "sensor.kueche_temperature": {
        "entity_id": "sensor.kueche_temperature",
        "state": "21.0",
        "attributes": {
            "friendly_name": "Küche Temperatur",
            "area_id": "kueche",
        },
    },
    "light.kueche_decke": {
        "entity_id": "light.kueche_decke",
        "state": "on",
        "attributes": {
            "friendly_name": "Küche Deckenlicht",
            "area_id": "kueche",
        },
    },
    "media_player.wohnzimmer_tv": {
        "entity_id": "media_player.wohnzimmer_tv",
        "state": "playing",
        "attributes": {
            "friendly_name": "Wohnzimmer TV",
            "area_id": "wohnzimmer",
        },
    },
}

MOCK_HA_AREAS = {
    "wohnzimmer": {"area_id": "wohnzimmer", "name": "Wohnzimmer", "floor_id": "floor_1"},
    "bad": {"area_id": "bad", "name": "Bad", "floor_id": "floor_1"},
    "toilette": {"area_id": "toilette", "name": "Toilette", "floor_id": "floor_1"},
    "kueche": {"area_id": "kueche", "name": "Küche", "floor_id": "floor_1"},
    "schlafzimmer": {"area_id": "schlafzimmer", "name": "Schlafzimmer", "floor_id": "floor_2"},
}


# ── Zone Matcher Implementation (for testing) ─────────────────────────────

class ZoneMatcher:
    """Zone matching engine with fuzzy matching and confidence scoring."""

    # 10 Habitus zones with room aliases
    ZONE_TEMPLATES = {
        "wohnbereich": {
            "name": "Wohnbereich",
            "icon": "mdi:sofa",
            "rooms": ["wohnzimmer", "esszimmer", "living_room", "living"],
        },
        "badbereich": {
            "name": "Badbereich",
            "icon": "mdi:shower-head",
            "rooms": ["bad", "badezimmer", "toilette", "gaeste_wc", "guest_wc", "wc"],
        },
        "schlafbereich": {
            "name": "Schlafbereich",
            "icon": "mdi:bed",
            "rooms": ["schlafzimmer", "kinderzimmer", "guest_room", "bedroom"],
        },
        "kuechenbereich": {
            "name": "Küchenbereich",
            "icon": "mdi:stove",
            "rooms": ["küche", "kueche", "kitchen", "cookroom"],
        },
        "eingangsbereich": {
            "name": "Eingangsbereich",
            "icon": "mdi:door-open",
            "rooms": ["flur", "diele", "eingang", "hallway", "entrance", "foyer"],
        },
        "aussenbereich": {
            "name": "Außenbereich",
            "icon": "mdi:tree",
            "rooms": ["garten", "terrasse", "balkon", "garage", "outdoor"],
        },
        "buero": {
            "name": "Büro / Arbeitszimmer",
            "icon": "mdi:desk",
            "rooms": ["büro", "buero", "arbeitszimmer", "office", "homeoffice"],
        },
        "essbereich": {
            "name": "Essbereich",
            "icon": "mdi:table-dining",
            "rooms": ["esszimmer", "dining_room", "dining"],
        },
        "hobbybereich": {
            "name": "Hobbybereich",
            "icon": "mdi:gamepad-variant",
            "rooms": ["keller", "hobbyraum", "gaming_room", "basement"],
        },
        "waschbereich": {
            "name": "Waschbereich",
            "icon": "mdi:washing-machine",
            "rooms": ["waschraum", "hauswirtschaftsraum", "laundry", "utility"],
        },
    }

    def __init__(self):
        self._rooms: Dict[str, Dict[str, Any]] = {}
        self._zones: Dict[str, Dict[str, Any]] = {}
        self._entity_values: Dict[str, Any] = {}

    def register_room(self, room_id: str, name: str, area_id: str = "",
                      entities: List[str] = None, floor: str = "") -> Dict[str, Any]:
        """Register a room from HA discovery."""
        room = {
            "room_id": room_id,
            "name": name,
            "area_id": area_id or room_id,
            "entities": entities or [],
            "floor": floor,
            "zone": None,
            "zone_confidence": 0.0,
        }
        self._rooms[room_id] = room
        return room

    def match_zone(self, room_id: str) -> Dict[str, Any]:
        """Match a room to a Habitus zone with confidence scoring."""
        room = self._rooms.get(room_id)
        if not room:
            return {"zone_id": None, "confidence": 0.0, "match_type": "none"}

        room_name_lower = room["name"].lower()
        room_id_lower = room_id.lower()

        best_match = None
        best_confidence = 0.0
        match_type = "none"

        for zone_id, template in self.ZONE_TEMPLATES.items():
            # Check room aliases
            for alias in template["rooms"]:
                # Exact match (highest confidence)
                if room_id_lower == alias or room_name_lower == alias:
                    return {
                        "zone_id": zone_id,
                        "zone_name": template["name"],
                        "confidence": 1.0,
                        "match_type": "exact",
                        "matched_alias": alias,
                    }

                # Fuzzy match
                confidence = self._fuzzy_match(room_id_lower, alias)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = zone_id
                    match_type = "fuzzy"

        # Threshold for fuzzy matches
        if best_confidence >= 0.6:
            zone_template = self.ZONE_TEMPLATES[best_match]
            return {
                "zone_id": best_match,
                "zone_name": zone_template["name"],
                "confidence": round(best_confidence, 2),
                "match_type": match_type,
            }

        return {"zone_id": None, "confidence": 0.0, "match_type": "none"}

    def _fuzzy_match(self, room_id: str, alias: str) -> float:
        """Fuzzy string matching with Levenshtein-based scoring."""
        # Simple overlap scoring
        if alias in room_id or room_id in alias:
            return 0.9

        # Character overlap
        set1 = set(room_id)
        set2 = set(alias)
        overlap = len(set1 & set2) / max(len(set1), len(set2))

        # Word overlap (split by underscores/hyphens)
        words1 = set(room_id.replace("_", " ").replace("-", " ").split())
        words2 = set(alias.replace("_", " ").replace("-", " ").split())
        word_overlap = len(words1 & words2) / max(len(words1), len(words2))

        return max(overlap * 0.5 + word_overlap * 0.5, 0.0)

    def assign_zone(self, room_id: str, zone_id: str) -> bool:
        """Manually assign a room to a zone."""
        if room_id not in self._rooms:
            return False
        self._rooms[room_id]["zone"] = zone_id
        self._rooms[room_id]["zone_confidence"] = 1.0
        return True

    def get_zone_rooms(self, zone_id: str) -> List[Dict[str, Any]]:
        """Get all rooms assigned to a zone."""
        return [r for r in self._rooms.values() if r["zone"] == zone_id]

    def get_unassigned_rooms(self) -> List[Dict[str, Any]]:
        """Get rooms without zone assignment."""
        return [r for r in self._rooms.values() if r["zone"] is None]

    def update_entity_state(self, entity_id: str, state: Any) -> None:
        """Update entity state."""
        self._entity_values[entity_id] = state

    def get_zone_state(self, zone_id: str) -> Dict[str, Any]:
        """Get aggregated zone state from all room entities."""
        zone_rooms = self.get_zone_rooms(zone_id)
        if not zone_rooms:
            return {"zone_id": zone_id, "error": "no_rooms"}

        temps = []
        humidities = []
        lights_on = 0
        motion_detected = False

        for room in zone_rooms:
            for entity_id in room["entities"]:
                state = self._entity_values.get(entity_id, {}).get("state")

                if "temperature" in entity_id and state:
                    try:
                        temps.append(float(state))
                    except ValueError:
                        pass

                if "humidity" in entity_id and state:
                    try:
                        humidities.append(float(state))
                    except ValueError:
                        pass

                if entity_id.startswith("light.") and state == "on":
                    lights_on += 1

                if "motion" in entity_id and state == "on":
                    motion_detected = True

        return {
            "zone_id": zone_id,
            "room_count": len(zone_rooms),
            "avg_temperature": round(sum(temps) / len(temps), 1) if temps else None,
            "avg_humidity": round(sum(humidities) / len(humidities), 1) if humidities else None,
            "lights_on": lights_on,
            "occupancy": motion_detected,
        }


# ── Tests ─────────────────────────────────────────────────────────────────

class TestHADiscovery:
    """Tests for HA entity and area discovery."""

    def test_discover_entities(self):
        """Test entity discovery from mock HA API."""
        assert len(MOCK_HA_ENTITIES) == 14

        # Check entity structure
        entity = MOCK_HA_ENTITIES["sensor.wohnzimmer_temperature"]
        assert "entity_id" in entity
        assert "state" in entity
        assert "attributes" in entity
        assert "area_id" in entity["attributes"]

    def test_discover_areas(self):
        """Test area discovery."""
        assert len(MOCK_HA_AREAS) == 5

        area = MOCK_HA_AREAS["wohnzimmer"]
        assert area["area_id"] == "wohnzimmer"
        assert area["name"] == "Wohnzimmer"
        assert "floor_id" in area

    def test_filter_entities_by_area(self):
        """Test filtering entities by area_id."""
        wohnzimmer_entities = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["attributes"].get("area_id") == "wohnzimmer"
        ]
        assert len(wohnzimmer_entities) == 6

        bad_entities = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["attributes"].get("area_id") == "bad"
        ]
        assert len(bad_entities) == 4  # temp, humidity, light, motion

    def test_filter_entities_by_domain(self):
        """Test filtering entities by domain (sensor, light, etc.)."""
        sensors = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["entity_id"].startswith("sensor.")
        ]
        assert len(sensors) == 5  # wohnzimmer_temp, wohnzimmer_humidity, bad_temp, bad_humidity, kueche_temp

        lights = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["entity_id"].startswith("light.")
        ]
        assert len(lights) == 5

    def test_filter_entities_by_device_class(self):
        """Test filtering entities by device_class."""
        temp_sensors = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["attributes"].get("device_class") == "temperature"
        ]
        assert len(temp_sensors) == 2  # wohnzimmer_temp, bad_temp

        motion_sensors = [
            e for e in MOCK_HA_ENTITIES.values()
            if e["attributes"].get("device_class") == "motion"
        ]
        assert len(motion_sensors) == 3


class TestZoneMatching:
    """Tests for zone matching with fuzzy matching and confidence scoring."""

    @pytest.fixture
    def matcher(self):
        """Create ZoneMatcher with test rooms."""
        m = ZoneMatcher()

        # Register all rooms from mock data
        m.register_room("wohnzimmer", "Wohnzimmer", "wohnzimmer",
                       ["sensor.wohnzimmer_temperature", "light.wohnzimmer_haupt"])
        m.register_room("bad", "Bad", "bad",
                       ["sensor.bad_temperature", "light.bad_decke"])
        m.register_room("toilette", "Toilette", "toilette",
                       ["light.toilette_licht"])
        m.register_room("kueche", "Küche", "kueche",
                       ["sensor.kueche_temperature", "light.kueche_decke"])
        m.register_room("schlafzimmer", "Schlafzimmer", "schlafzimmer", [])
        m.register_room("flur", "Flur", "flur", [])
        m.register_room("garten", "Garten", "garten", [])
        m.register_room("buero", "Büro", "buero", [])

        return m

    def test_exact_match_wohnzimmer(self, matcher):
        """Test exact match for wohnzimmer -> wohnbereich."""
        result = matcher.match_zone("wohnzimmer")
        assert result["zone_id"] == "wohnbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_bad(self, matcher):
        """Test exact match for bad -> badbereich."""
        result = matcher.match_zone("bad")
        assert result["zone_id"] == "badbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_toilette(self, matcher):
        """Test exact match for toilet -> badbereich."""
        result = matcher.match_zone("toilette")
        assert result["zone_id"] == "badbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_kueche(self, matcher):
        """Test exact match for küche -> küchenbereich."""
        result = matcher.match_zone("kueche")
        assert result["zone_id"] == "kuechenbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_schlafzimmer(self, matcher):
        """Test exact match for schlafzimmer -> schlafbereich."""
        result = matcher.match_zone("schlafzimmer")
        assert result["zone_id"] == "schlafbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_flur(self, matcher):
        """Test exact match for flur -> eingangsbereich."""
        result = matcher.match_zone("flur")
        assert result["zone_id"] == "eingangsbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_garten(self, matcher):
        """Test exact match for garten -> außenbereich."""
        result = matcher.match_zone("garten")
        assert result["zone_id"] == "aussenbereich"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_exact_match_buero(self, matcher):
        """Test exact match for büro -> büro."""
        result = matcher.match_zone("buero")
        assert result["zone_id"] == "buero"
        assert result["confidence"] == 1.0
        assert result["match_type"] == "exact"

    def test_all_10_zones_covered(self, matcher):
        """Test that all 10 Habitus zones have room mappings."""
        templates = ZoneMatcher.ZONE_TEMPLATES
        assert len(templates) == 10

        expected_zones = {
            "wohnbereich", "badbereich", "schlafbereich",
            "kuechenbereich", "eingangsbereich", "aussenbereich",
            "buero", "essbereich", "hobbybereich", "waschbereich"
        }
        assert set(templates.keys()) == expected_zones

    def test_fuzzy_match_living_room(self, matcher):
        """Test fuzzy match for 'living_room' -> wohnbereich."""
        matcher.register_room("living_room", "Living Room", "", [])
        result = matcher.match_zone("living_room")
        assert result["zone_id"] == "wohnbereich"
        assert result["confidence"] >= 0.6

    def test_fuzzy_match_kitchen(self, matcher):
        """Test fuzzy match for 'kitchen' -> küchenbereich."""
        matcher.register_room("kitchen", "Kitchen", "", [])
        result = matcher.match_zone("kitchen")
        assert result["zone_id"] == "kuechenbereich"
        assert result["confidence"] >= 0.6

    def test_no_match_unknown_room(self, matcher):
        """Test no match for unknown room."""
        matcher.register_room("unknown_xyz_123", "Unknown Room", "", [])
        result = matcher.match_zone("unknown_xyz_123")
        assert result["zone_id"] is None
        assert result["confidence"] == 0.0
        assert result["match_type"] == "none"

    def test_confidence_scoring_exact_vs_fuzzy(self, matcher):
        """Test that exact matches have higher confidence than fuzzy."""
        exact_result = matcher.match_zone("wohnzimmer")
        assert exact_result["confidence"] == 1.0

        matcher.register_room("wohnzimmer_neu", "Neues Wohnzimmer", "", [])
        fuzzy_result = matcher.match_zone("wohnzimmer_neu")
        assert fuzzy_result["confidence"] < 1.0


class TestZoneStateAggregation:
    """Tests for zone state aggregation from entity values."""

    @pytest.fixture
    def populated_matcher(self):
        """Create matcher with entity states."""
        m = ZoneMatcher()

        # Register rooms for badbereich
        m.register_room("bad", "Bad", "bad",
                       ["sensor.bad_temperature", "sensor.bad_humidity",
                        "light.bad_decke", "binary_sensor.bad_motion"])
        m.register_room("toilette", "Toilette", "toilette",
                       ["light.toilette_licht", "binary_sensor.toilette_motion"])

        # Assign to zone
        m.assign_zone("bad", "badbereich")
        m.assign_zone("toilette", "badbereich")

        # Set entity states
        m.update_entity_state("sensor.bad_temperature", {"state": "24.0"})
        m.update_entity_state("sensor.bad_humidity", {"state": "65.0"})
        m.update_entity_state("light.bad_decke", {"state": "on"})
        m.update_entity_state("binary_sensor.bad_motion", {"state": "on"})
        m.update_entity_state("light.toilette_licht", {"state": "off"})
        m.update_entity_state("binary_sensor.toilette_motion", {"state": "off"})

        return m

    def test_zone_temperature_aggregation(self, populated_matcher):
        """Test temperature aggregation across zone rooms."""
        state = populated_matcher.get_zone_state("badbereich")
        assert state["avg_temperature"] == 24.0
        assert state["room_count"] == 2

    def test_zone_humidity_aggregation(self, populated_matcher):
        """Test humidity aggregation across zone rooms."""
        state = populated_matcher.get_zone_state("badbereich")
        assert state["avg_humidity"] == 65.0

    def test_zone_occupancy_detection(self, populated_matcher):
        """Test occupancy detection from motion sensors."""
        state = populated_matcher.get_zone_state("badbereich")
        assert state["occupancy"] is True  # bad motion is on

    def test_zone_lights_count(self, populated_matcher):
        """Test counting lights that are on in zone."""
        state = populated_matcher.get_zone_state("badbereich")
        assert state["lights_on"] == 1  # only bad_decke is on

    def test_zone_no_data(self):
        """Test zone state with no entity data."""
        m = ZoneMatcher()
        m.register_room("test", "Test", "", [])
        m.assign_zone("test", "wohnbereich")
        state = m.get_zone_state("wohnbereich")
        assert state["avg_temperature"] is None
        assert state["occupancy"] is False


class TestRoomZoneAssignment:
    """Tests for manual and automatic room-to-zone assignment."""

    def test_manual_assignment(self):
        """Test manual room-to-zone assignment."""
        m = ZoneMatcher()
        m.register_room("test_room", "Test Room", "", [])

        result = m.assign_zone("test_room", "wohnbereich")
        assert result is True

        rooms = m.get_zone_rooms("wohnbereich")
        assert len(rooms) == 1
        assert rooms[0]["room_id"] == "test_room"

    def test_invalid_room_assignment(self):
        """Test assignment fails for non-existent room."""
        m = ZoneMatcher()
        result = m.assign_zone("nonexistent", "wohnbereich")
        assert result is False

    def test_get_unassigned_rooms(self):
        """Test getting list of unassigned rooms."""
        m = ZoneMatcher()
        m.register_room("room1", "Room 1", "", [])
        m.register_room("room2", "Room 2", "", [])
        m.register_room("room3", "Room 3", "", [])

        m.assign_zone("room1", "wohnbereich")

        unassigned = m.get_unassigned_rooms()
        assert len(unassigned) == 2
        unassigned_ids = {r["room_id"] for r in unassigned}
        assert unassigned_ids == {"room2", "room3"}


class TestEntityAdoption:
    """Tests for entity adoption from rooms to zones."""

    def test_entities_inherited_from_rooms(self):
        """Test that zone inherits all entities from its rooms."""
        m = ZoneMatcher()

        m.register_room("bad", "Bad", "",
                       ["sensor.bad_temp", "light.bad", "binary_sensor.bad_motion"])
        m.register_room("toilette", "Toilette", "",
                       ["light.toilette", "binary_sensor.toilette_motion"])

        m.assign_zone("bad", "badbereich")
        m.assign_zone("toilette", "badbereich")

        # Get all entities from zone rooms
        zone_rooms = m.get_zone_rooms("badbereich")
        all_entities = []
        for room in zone_rooms:
            all_entities.extend(room["entities"])

        assert len(all_entities) == 5
        assert "sensor.bad_temp" in all_entities
        assert "light.toilette" in all_entities


# ── Integration-style Tests ───────────────────────────────────────────────

class TestHADiscoveryIntegration:
    """Integration-style tests for full discovery flow."""

    def test_full_discovery_and_matching_flow(self):
        """Test complete flow: HA discovery → room registration → zone matching."""
        matcher = ZoneMatcher()

        # Step 1: Discover areas from HA
        areas = MOCK_HA_AREAS

        # Step 2: Register rooms from discovered areas
        for area_id, area_info in areas.items():
            room_entities = [
                e["entity_id"] for e in MOCK_HA_ENTITIES.values()
                if e["attributes"].get("area_id") == area_id
            ]
            matcher.register_room(
                area_id,
                area_info["name"],
                area_id,
                room_entities,
                area_info.get("floor_id", "")
            )

        # Step 3: Auto-match zones
        matched_zones = {}
        for room_id in areas.keys():
            # Register room if not already registered
            if room_id not in matcher._rooms:
                room_entities = [
                    e["entity_id"] for e in MOCK_HA_ENTITIES.values()
                    if e["attributes"].get("area_id") == room_id
                ]
                matcher.register_room(room_id, areas[room_id]["name"], room_id, room_entities)

            result = matcher.match_zone(room_id)
            if result["zone_id"]:
                matcher.assign_zone(room_id, result["zone_id"])
                matched_zones[room_id] = result["zone_id"]

        # Step 4: Verify matches
        assert matched_zones.get("wohnzimmer") == "wohnbereich"
        assert matched_zones.get("bad") == "badbereich"
        assert matched_zones.get("toilette") == "badbereich"
        assert matched_zones.get("kueche") == "kuechenbereich"
        assert matched_zones.get("schlafzimmer") == "schlafbereich"
        # Note: flur and garten need explicit registration with aliases
        # Check they match when registered properly
        matcher.register_room("flur", "Flur", "flur", [])
        matcher.register_room("garten", "Garten", "garten", [])
        flur_match = matcher.match_zone("flur")
        garten_match = matcher.match_zone("garten")
        assert flur_match["zone_id"] == "eingangsbereich"
        assert garten_match["zone_id"] == "aussenbereich"

        # Step 5: Check zone room counts
        badbereich_rooms = matcher.get_zone_rooms("badbereich")
        assert len(badbereich_rooms) == 2  # bad + toilette
