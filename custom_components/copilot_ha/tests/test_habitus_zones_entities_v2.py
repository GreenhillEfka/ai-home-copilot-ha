"""Tests for Habitus Zones v2 entity classes.

Verifies that schema-driven entity generation produces the correct HA entities
for all module-per-zone types: Licht, Bewegung, Heiz/Klima, Cover, Energie, Szene.
"""

from __future__ import annotations

import asyncio
import inspect
from unittest.mock import MagicMock, AsyncMock

import pytest

# Import from existing conftest
from tests.conftest import ConfigEntry, MockHass


# ──────────────────────────────────────────────────────────────────────────────
# Import from the codebase under test (paths pre-configured by conftest)
# ──────────────────────────────────────────────────────────────────────────────

STORE = "custom_components.copilot_ha.habitus_zones_store_v2"
ENTITIES_V2 = "custom_components.copilot_ha.habitus_zones_entities_v2"


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Fake CopilotDataUpdateCoordinator."""
    coord = MagicMock()
    coord.data = {}
    coord._config = {
        "host": "192.168.1.10",
        "port": 8909,
        "token": "test_token",
    }
    coord.async_get_neurons = MagicMock(return_value={"context": {"presence": {}}})
    return coord


@pytest.fixture
def minimal_zone_dict() -> dict:
    """Minimal valid zone schema dict."""
    return {
        "id": "zone:wohnzimmer",
        "name": "Wohnzimmer",
        "zone_type": "room",
        "entity_ids": ["light.led_wohnzimmer", "binary_sensor.bewegung_wohnzimmer"],
    }


@pytest.fixture
def full_zone_dict() -> dict:
    """Full-featured zone schema dict with all role types."""
    return {
        "id": "zone:buero",
        "name": "Büro",
        "zone_type": "room",
        "entities": {
            "lights": ["light.decke", "light.schreibtischlampe"],
            "motion": ["binary_sensor.praesenz_buero"],
            "temperature": ["sensor.temperatur_buero"],
            "humidity": ["sensor.feuchtigkeit_buero"],
            "cover": ["cover.jalousie_buero"],
            "power": ["sensor.strom_buero"],
        },
        "floor": "OG",
        "priority": 7,
        "tags": ["arbeit", "fokus"],
        "metadata": {"ambience": "fokus", "optimization": "energie"},
    }


# ──────────────────────────────────────────────────────────────────────────────
# Test: Zone Schema Loading  (_normalize_zone_v2)
# ──────────────────────────────────────────────────────────────────────────────

class TestNormalizeZoneV2:
    """Schema loading: _normalize_zone_v2 converts dicts → HabitusZoneV2."""

    def test_minimal_schema(self, minimal_zone_dict: dict) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(minimal_zone_dict)

        assert zone is not None
        assert zone.zone_id == "zone:wohnzimmer"
        assert zone.name == "Wohnzimmer"
        assert zone.zone_type == "room"
        assert "light.led_wohnzimmer" in zone.entity_ids
        assert "binary_sensor.bewegung_wohnzimmer" in zone.entity_ids

    def test_all_zone_types(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        for ztype in ("room", "area", "floor", "outdoor"):
            zone = _normalize_zone_v2(
                {"id": f"zone:test_{ztype}", "name": "Test", "zone_type": ztype}
            )
            assert zone is not None, f"zone_type={ztype} failed"
            assert zone.zone_type == ztype

    def test_invalid_zone_type_falls_back_to_room(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {"id": "zone:test", "name": "Test", "zone_type": "invalid_type"}
        )
        assert zone is not None
        assert zone.zone_type == "room"  # fallback

    def test_role_based_entities_parsing(self, full_zone_dict: dict) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(full_zone_dict)

        assert zone.entities is not None
        assert "light.decke" in zone.entities["lights"]
        assert "sensor.temperatur_buero" in zone.entities["temperature"]
        assert "cover.jalousie_buero" in zone.entities["cover"]

    def test_role_alias_motion(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        # presence and occupancy both alias to 'motion'; last-write-wins
        zone = _normalize_zone_v2(
            {
                "id": "zone:test",
                "entities": {
                    "presence": ["binary_sensor.praesenz"],
                },
            }
        )
        assert zone is not None
        assert "motion" in (zone.entities or {})
        assert "binary_sensor.praesenz" in zone.entities["motion"]

    def test_auto_active_state_when_entities_assigned(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {"id": "zone:test", "current_state": "idle", "entity_ids": ["light.x"]}
        )
        assert zone is not None
        # Zone with entities but idle → auto-upgraded to active
        assert zone.current_state == "active"

    def test_disabled_state_preserved(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {"id": "zone:test", "current_state": "disabled", "entity_ids": ["light.x"]}
        )
        assert zone is not None
        assert zone.current_state == "disabled"  # explicit state preserved

    def test_missing_id_returns_none(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2({"name": "No ID Zone"})
        assert zone is None

    def test_priority_normalization(self, full_zone_dict: dict) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(full_zone_dict)
        assert zone is not None
        assert zone.priority == 7

    def test_hierarchy_parent_child(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        parent = _normalize_zone_v2(
            {"id": "zone:living_area", "name": "Living Area", "zone_type": "area"}
        )
        child = _normalize_zone_v2(
            {
                "id": "zone:wohnzimmer",
                "name": "Wohnzimmer",
                "zone_type": "room",
                "parent": "zone:living_area",
            }
        )
        assert parent is not None
        assert child is not None
        assert child.parent_zone_id == "zone:living_area"


# ──────────────────────────────────────────────────────────────────────────────
# Test: Role Alias Resolution  (_parse_entities_mapping)
# ──────────────────────────────────────────────────────────────────────────────

class TestRoleAliases:
    """Role aliases resolve correctly (presence→motion, larm→noise, etc.)."""

    def test_presence_alias(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _parse_entities_mapping,
        )

        result = _parse_entities_mapping({"presence": ["binary_sensor.x"]})
        assert result is not None
        assert "motion" in result
        assert "binary_sensor.x" in result["motion"]

    def test_lights_alias(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _parse_entities_mapping,
        )

        result = _parse_entities_mapping({"lights": ["light.y"]})
        assert result is not None
        assert "lights" in result

    def test_heating_alias(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _parse_entities_mapping,
        )

        result = _parse_entities_mapping({"heating": ["climate.thermostat"]})
        assert result is not None
        assert "heating" in result

    def test_unknown_role_preserved(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _parse_entities_mapping,
        )

        result = _parse_entities_mapping({"my_custom_role": ["sensor.x"]})
        assert result is not None
        assert "my_custom_role" in result


# ──────────────────────────────────────────────────────────────────────────────
# Test: Entity Validation  (_validate_zone_v2)
# ──────────────────────────────────────────────────────────────────────────────

class TestZoneValidation:
    """Invalid schemas raise ValueError with actionable messages."""

    def test_orphan_zone_no_entities_raises_validation_error(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
            _validate_zone_v2,
        )

        # Orphan zones (no entities) are accepted by the store (no ValueError
        # in __post_init__) but validation at write-time raises ValueError.
        zone = _normalize_zone_v2({"id": "zone:orphan", "entity_ids": []})
        assert zone is not None
        # Must raise — zone without any valid entity_id is rejected
        with pytest.raises(ValueError, match="must include at least 1 valid entity_id"):
            _validate_zone_v2(MagicMock(), zone)

    def test_invalid_entity_id_format_still_passes_store(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        # No dot = invalid format; store accepts it, validation could reject
        zone = _normalize_zone_v2(
            {"id": "zone:test", "entity_ids": ["no_domain_entity"]}
        )
        assert zone is not None
        # Store-level normalization does NOT block; entity_ids can be any string
        assert "no_domain_entity" in zone.entity_ids

    def test_zone_id_required(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2({"name": "Nameless Zone"})
        assert zone is None  # No zone_id → None

    def test_graph_node_id_auto_set(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {"id": "zone:wohnzimmer", "name": "Wohnzimmer"}
        )
        assert zone is not None
        assert zone.graph_node_id == "zone:wohnzimmer"


# ──────────────────────────────────────────────────────────────────────────────
# Test: Module-per-Zone Entity Generation
# ──────────────────────────────────────────────────────────────────────────────

class TestBewegungModuleEntityGeneration:
    """BewegungModule tracks per-zone motion state for Habitus zones."""

    def test_bewegung_module_tracks_zone(self) -> None:
        from custom_components.copilot_ha.core.modules.bewegung_module import (
            BewegungModule,
        )

        mod = BewegungModule()
        mod.update_zone(
            "zone:wohnzimmer",
            sensors_active=2,
            sensors_total=3,
            last_motion=1234567890,
            has_recent_motion=True,
        )

        state = mod.get_zone("zone:wohnzimmer")
        assert state is not None
        assert state["sensors_active"] == 2
        assert state["sensors_total"] == 3
        assert state["has_recent_motion"] is True

    def test_bewegung_module_get_summary(self) -> None:
        from custom_components.copilot_ha.core.modules.bewegung_module import (
            BewegungModule,
        )

        mod = BewegungModule()
        mod.update_zone("zone:a", has_recent_motion=True)
        mod.update_zone("zone:b", has_recent_motion=False)

        summary = mod.get_summary()
        assert summary["total_zones"] == 2
        assert summary["zones_with_recent_motion"] == 1


class TestLichtModuleEntityGeneration:
    """LichtModule tracks per-zone light state for Habitus zones."""

    def test_licht_module_update_zone(self) -> None:
        from custom_components.copilot_ha.core.modules.licht_module import (
            LichtModule,
        )

        mod = LichtModule()
        mod.update_zone(
            "zone:wohnzimmer",
            lights_on=3,
            lights_total=5,
            avg_brightness=75.0,
            auto_enabled=True,
        )

        state = mod.get_zone("zone:wohnzimmer")
        assert state is not None
        assert state["lights_on"] == 3
        assert state["lights_total"] == 5
        assert state["avg_brightness"] == 75.0
        assert state["auto_enabled"] is True

    def test_licht_module_name(self) -> None:
        from custom_components.copilot_ha.core.modules.licht_module import (
            LichtModule,
        )

        mod = LichtModule()
        assert mod.name == "licht_module"


class TestHeizModuleEntityGeneration:
    """HeizModule tracks per-zone climate state for Habitus zones."""

    def test_heiz_module_update_zone(self) -> None:
        from custom_components.copilot_ha.core.modules.heiz_module import (
            HeizModule,
        )

        mod = HeizModule()
        mod.update_zone(
            "zone:schlafzimmer",
            current_temp=19.5,
            target_temp=21.0,
            humidity=55.0,
            is_heating=True,
            eco_mode=False,
            comfort_index=0.8,
        )

        state = mod.get_zone("zone:schlafzimmer")
        assert state is not None
        assert state["current_temp"] == 19.5
        assert state["target_temp"] == 21.0
        assert state["is_heating"] is True


class TestSceneModuleEntityGeneration:
    """SceneModule manages zone scenes (Licht/Cover/Klima/Szene)."""

    def test_scene_module_name(self) -> None:
        from custom_components.copilot_ha.core.modules.scene_module import (
            SceneModule,
        )

        mod = SceneModule()
        assert mod.name == "scene_module"
        assert mod.version == "0.1.0"

    def test_scene_module_capturable_domains(self) -> None:
        from custom_components.copilot_ha.core.modules.scene_module import (
            CAPTURABLE_DOMAINS,
        )

        assert "light" in CAPTURABLE_DOMAINS
        assert "cover" in CAPTURABLE_DOMAINS
        assert "climate" in CAPTURABLE_DOMAINS
        assert "media_player" in CAPTURABLE_DOMAINS

    def test_scene_module_domain_capture_attrs(self) -> None:
        from custom_components.copilot_ha.core.modules.scene_module import (
            DOMAIN_CAPTURE_ATTRS,
        )

        assert "light" in DOMAIN_CAPTURE_ATTRS
        assert "brightness" in DOMAIN_CAPTURE_ATTRS["light"]
        assert "color_temp_kelvin" in DOMAIN_CAPTURE_ATTRS["light"]


class TestModuleProtocolCompliance:
    """All CopilotModules satisfy the CopilotModule protocol."""

    @pytest.mark.parametrize(
        "module_class",
        [
            "custom_components.copilot_ha.core.modules.bewegung_module.BewegungModule",
            "custom_components.copilot_ha.core.modules.licht_module.LichtModule",
            "custom_components.copilot_ha.core.modules.heiz_module.HeizModule",
            "custom_components.copilot_ha.core.modules.scene_module.SceneModule",
        ],
    )
    def test_module_has_name_property(self, module_class: str) -> None:
        import importlib
        module_path, class_name = module_class.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        instance = cls()
        assert hasattr(instance, "name")
        assert isinstance(instance.name, str)

    @pytest.mark.parametrize(
        "module_class",
        [
            "custom_components.copilot_ha.core.modules.bewegung_module.BewegungModule",
            "custom_components.copilot_ha.core.modules.licht_module.LichtModule",
            "custom_components.copilot_ha.core.modules.heiz_module.HeizModule",
            "custom_components.copilot_ha.core.modules.scene_module.SceneModule",
        ],
    )
    def test_module_has_async_setup_entry(self, module_class: str) -> None:
        import importlib
        module_path, class_name = module_class.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        instance = cls()
        assert hasattr(instance, "async_setup_entry")
        assert inspect.iscoroutinefunction(instance.async_setup_entry)

    @pytest.mark.parametrize(
        "module_class",
        [
            "custom_components.copilot_ha.core.modules.bewegung_module.BewegungModule",
            "custom_components.copilot_ha.core.modules.licht_module.LichtModule",
            "custom_components.copilot_ha.core.modules.heiz_module.HeizModule",
            "custom_components.copilot_ha.core.modules.scene_module.SceneModule",
        ],
    )
    def test_module_has_async_unload_entry(self, module_class: str) -> None:
        import importlib
        module_path, class_name = module_class.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        instance = cls()
        assert hasattr(instance, "async_unload_entry")
        assert inspect.iscoroutinefunction(instance.async_unload_entry)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Zone Conflict Resolution
# ──────────────────────────────────────────────────────────────────────────────

class TestZoneConflictResolver:
    """ZoneConflictResolver detects and resolves entity overlaps between zones."""

    def test_overlapping_entities_detected(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            HabitusZoneV2,
            ZoneConflictResolver,
            ConflictResolutionStrategy,
        )

        zones = [
            HabitusZoneV2(
                zone_id="zone:wohnzimmer",
                name="Wohnzimmer",
                zone_type="room",
                entity_ids=("light.shared", "light.wohnzimmer"),
            ),
            HabitusZoneV2(
                zone_id="zone:living_area",
                name="Living Area",
                zone_type="area",
                entity_ids=("light.shared", "light.area"),
            ),
        ]

        resolver = ZoneConflictResolver(
            hass=MagicMock(),
            zones=zones,
            default_strategy=ConflictResolutionStrategy.HIERARCHY,
        )

        overlaps = resolver.find_overlapping_zones()
        assert len(overlaps) == 1
        assert "zone:wohnzimmer" in overlaps[0]
        assert "zone:living_area" in overlaps[0]
        assert "light.shared" in overlaps[0][2]

    @pytest.mark.asyncio
    async def test_hierarchy_resolution_child_wins(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            HabitusZoneV2,
            ZoneConflictResolver,
            ConflictResolutionStrategy,
        )

        zones = [
            HabitusZoneV2(
                zone_id="zone:wohnzimmer",
                name="Wohnzimmer",
                zone_type="room",  # hierarchy_level=2
                entity_ids=("light.shared",),
            ),
            HabitusZoneV2(
                zone_id="zone:living_area",
                name="Living Area",
                zone_type="area",  # hierarchy_level=1
                entity_ids=("light.shared",),
            ),
        ]

        resolver = ZoneConflictResolver(
            hass=MagicMock(),
            zones=zones,
            default_strategy=ConflictResolutionStrategy.HIERARCHY,
        )

        resolved, conflicts = await resolver.resolve_conflicts(
            ["zone:wohnzimmer", "zone:living_area"]
        )

        # Child zone (room) wins over parent zone (area)
        assert "zone:wohnzimmer" in resolved
        assert "zone:living_area" not in resolved

    @pytest.mark.asyncio
    async def test_priority_resolution_higher_wins(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            HabitusZoneV2,
            ZoneConflictResolver,
            ConflictResolutionStrategy,
        )

        zones = [
            HabitusZoneV2(
                zone_id="zone:low_prio",
                name="Low Priority",
                zone_type="room",
                priority=3,
                entity_ids=("light.shared",),
            ),
            HabitusZoneV2(
                zone_id="zone:high_prio",
                name="High Priority",
                zone_type="room",
                priority=9,
                entity_ids=("light.shared",),
            ),
        ]

        resolver = ZoneConflictResolver(
            hass=MagicMock(),
            zones=zones,
            default_strategy=ConflictResolutionStrategy.PRIORITY,
        )

        resolved, _ = await resolver.resolve_conflicts(
            ["zone:low_prio", "zone:high_prio"]
        )

        assert "zone:high_prio" in resolved
        assert "zone:low_prio" not in resolved

    @pytest.mark.asyncio
    async def test_no_conflict_single_zone(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            HabitusZoneV2,
            ZoneConflictResolver,
            ConflictResolutionStrategy,
        )

        zones = [
            HabitusZoneV2(
                zone_id="zone:solo",
                name="Solo Zone",
                zone_type="room",
                entity_ids=("light.only",),
            ),
        ]

        resolver = ZoneConflictResolver(
            hass=MagicMock(),
            zones=zones,
            default_strategy=ConflictResolutionStrategy.HIERARCHY,
        )

        resolved, conflicts = await resolver.resolve_conflicts(["zone:solo"])
        assert resolved == ["zone:solo"]
        assert conflicts == []


# ──────────────────────────────────────────────────────────────────────────────
# Test: Zone State Machine
# ──────────────────────────────────────────────────────────────────────────────

class TestZoneStateMachine:
    """HabitusZoneV2 state transitions."""

    def test_valid_states(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        for state in ("idle", "active", "transitioning", "disabled", "error"):
            zone = _normalize_zone_v2(
                {"id": f"zone:state_{state}", "current_state": state}
            )
            assert zone is not None, f"state={state} failed"
            assert zone.current_state == state

    def test_invalid_state_falls_back_to_idle(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {"id": "zone:bad_state", "current_state": "super_state"}
        )
        assert zone is not None
        assert zone.current_state == "idle"  # fallback

    def test_hierarchy_level_computed(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        floor_zone = _normalize_zone_v2({"id": "zone:eg", "zone_type": "floor"})
        area_zone = _normalize_zone_v2({"id": "zone:wohnbereich", "zone_type": "area"})
        room_zone = _normalize_zone_v2({"id": "zone:wohnzimmer", "zone_type": "room"})

        assert floor_zone is not None
        assert area_zone is not None
        assert room_zone is not None

        assert floor_zone.hierarchy_level == 0
        assert area_zone.hierarchy_level == 1
        assert room_zone.hierarchy_level == 2

    def test_get_role_entities(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {
                "id": "zone:test",
                "entities": {
                    "lights": ["light.a", "light.b"],
                    "motion": ["binary_sensor.x"],
                },
            }
        )
        assert zone is not None
        lights = zone.get_role_entities("lights")
        assert len(lights) == 2
        assert "light.a" in lights

    def test_get_all_entities(self) -> None:
        from custom_components.copilot_ha.habitus_zones_store_v2 import (
            _normalize_zone_v2,
        )

        zone = _normalize_zone_v2(
            {
                "id": "zone:test",
                "entity_ids": ["sensor.temp"],
                "entities": {"lights": ["light.x"]},
            }
        )
        assert zone is not None
        all_entities = zone.get_all_entities()
        assert "sensor.temp" in all_entities
        assert "light.x" in all_entities


# ──────────────────────────────────────────────────────────────────────────────
# Test: Zone Schema → Entity Registry Mapping  (ENTITIES_V2 list)
# ──────────────────────────────────────────────────────────────────────────────

class TestEntitiesV2Registry:
    """All expected entity classes are registered in ENTITIES_V2."""

    def test_entities_v2_contains_expected_count(self) -> None:
        from custom_components.copilot_ha.habitus_zones_entities_v2 import (
            ENTITIES_V2,
        )

        # 9 entity types currently exposed for Habitus Zones v2
        assert len(ENTITIES_V2) == 9

    def test_entities_v2_all_are_classes(self) -> None:
        from custom_components.copilot_ha.habitus_zones_entities_v2 import (
            ENTITIES_V2,
        )

        for entity_cls in ENTITIES_V2:
            assert isinstance(entity_cls, type), (
                f"{entity_cls} is not a class"
            )

    def test_entities_v2_unique_ids(self) -> None:
        from custom_components.copilot_ha.habitus_zones_entities_v2 import (
            ENTITIES_V2,
        )

        unique_ids = [e._attr_unique_id for e in ENTITIES_V2]
        assert len(unique_ids) == len(set(unique_ids)), (
            "Duplicate unique_ids in ENTITIES_V2"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Py-compile Verify
# ──────────────────────────────────────────────────────────────────────────────

class TestPyCompile:
    """Syntax verification for all tested modules."""

    @pytest.mark.parametrize(
        "module_path",
        [
            "custom_components.copilot_ha.habitus_zones_store_v2",
            "custom_components.copilot_ha.habitus_zones_entities_v2",
            "custom_components.copilot_ha.core.modules.bewegung_module",
            "custom_components.copilot_ha.core.modules.licht_module",
            "custom_components.copilot_ha.core.modules.heiz_module",
            "custom_components.copilot_ha.core.modules.scene_module",
            "custom_components.copilot_ha.core.modules.frigate_bridge",
        ],
    )
    def test_module_compiles(self, module_path: str) -> None:
        import importlib
        import py_compile

        spec = importlib.util.find_spec(module_path)
        assert spec is not None, f"Module {module_path!r} not found"
        filepath = spec.origin
        assert filepath is not None

        # py_compile raises SyntaxError on failure
        py_compile.compile(filepath, doraise=True)
