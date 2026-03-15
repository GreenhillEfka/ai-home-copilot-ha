"""Tests for Neuron Feed Control, Entity-centric Zone & Tag Assignment.

Tests:
- NeuronFeedStore: per-tag feed state persistence
- NeuronFeedTagSwitch: switch entity on/off behavior
- NeuronFeedSummarySensor: included/excluded counts
- async_is_entity_neuron_fed: entity-level feed check
- zone_entity_select: assign/remove entity from zone
- tag_entity / untag_entity: entity-centric tag assignment
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass, field
from typing import Any


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_hass():
    """Create a lightweight mock HomeAssistant."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()
    hass.bus = MagicMock()
    hass.states = MagicMock()
    return hass


def _make_coordinator(hass=None):
    """Create a lightweight mock coordinator."""
    if hass is None:
        hass = _make_hass()
    coord = MagicMock()
    coord.hass = hass
    coord.data = {}
    coord._config = {"host": "localhost", "port": 8909}
    return coord


def _make_entry(entry_id="test_entry"):
    """Create a lightweight mock ConfigEntry."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.domain = "copilot_ha"
    entry.data = {}
    entry.options = {}
    return entry


# ── Neuron Feed Store Tests ──────────────────────────────────────────────


class TestNeuronFeedStore:
    """Test neuron_feed_store.py persistence functions."""

    @pytest.fixture
    def hass(self):
        return _make_hass()

    @pytest.fixture
    def store_data(self):
        """Shared mutable store data for simulating persistence."""
        return [{"feeds": {}}]

    @pytest.fixture(autouse=True)
    def patch_store(self, hass, store_data):
        """Patch HA Store to use in-memory dict."""
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(side_effect=lambda: store_data[0])

        async def _save(data):
            store_data[0] = data

        mock_store.async_save = AsyncMock(side_effect=_save)

        with patch(
            "copilot_ha.neuron_feed_store.Store",
            return_value=mock_store,
        ), patch(
            "copilot_ha.neuron_feed_store.async_dispatcher_send",
        ):
            # Reset global store cache
            hass.data.setdefault("copilot_ha", {}).setdefault("_global", {}).pop(
                "neuron_feed_store", None
            )
            yield mock_store

    @pytest.mark.asyncio
    async def test_get_empty_states(self, hass, store_data):
        """Empty store returns empty dict."""
        store_data[0] = {}
        from copilot_ha.neuron_feed_store import async_get_neuron_feed_states

        states = await async_get_neuron_feed_states(hass)
        assert states == {}

    @pytest.mark.asyncio
    async def test_set_and_get_state(self, hass, store_data):
        """Set a tag feed state and retrieve it."""
        from copilot_ha.neuron_feed_store import (
            async_set_neuron_feed_state,
            async_get_neuron_feed_state,
        )

        await async_set_neuron_feed_state(hass, "licht", False)
        assert store_data[0]["feeds"]["licht"] is False

        result = await async_get_neuron_feed_state(hass, "licht")
        assert result is False

    @pytest.mark.asyncio
    async def test_default_state_is_true(self, hass, store_data):
        """Unset tag defaults to True (enabled)."""
        from copilot_ha.neuron_feed_store import async_get_neuron_feed_state

        result = await async_get_neuron_feed_state(hass, "unknown_tag")
        assert result is True

    @pytest.mark.asyncio
    async def test_set_multiple_tags(self, hass, store_data):
        """Multiple tags can be independently controlled."""
        from copilot_ha.neuron_feed_store import (
            async_set_neuron_feed_state,
            async_get_neuron_feed_states,
        )

        await async_set_neuron_feed_state(hass, "licht", False)
        await async_set_neuron_feed_state(hass, "klima", True)
        await async_set_neuron_feed_state(hass, "sicherheit", False)

        states = await async_get_neuron_feed_states(hass)
        assert states == {"licht": False, "klima": True, "sicherheit": False}

    @pytest.mark.asyncio
    async def test_set_state_fires_signal(self, hass, store_data):
        """Setting neuron feed state fires SIGNAL_NEURON_FEED_CHANGED."""
        from copilot_ha.neuron_feed_store import (
            async_set_neuron_feed_state,
            SIGNAL_NEURON_FEED_CHANGED,
        )

        with patch(
            "copilot_ha.neuron_feed_store.async_dispatcher_send",
        ) as mock_signal:
            await async_set_neuron_feed_state(hass, "licht", False)
            mock_signal.assert_called_once_with(
                hass, SIGNAL_NEURON_FEED_CHANGED, "licht"
            )

    def test_signal_constant_exists(self):
        """SIGNAL_NEURON_FEED_CHANGED constant is defined."""
        from copilot_ha.neuron_feed_store import SIGNAL_NEURON_FEED_CHANGED
        assert "neuron_feed" in SIGNAL_NEURON_FEED_CHANGED


# ── Entity Neuron Fed Check ─────────────────────────────────────────────


class TestIsEntityNeuronFed:
    """Test async_is_entity_neuron_fed logic."""

    @pytest.fixture
    def hass(self):
        return _make_hass()

    @pytest.mark.asyncio
    async def test_entity_no_tags_always_fed(self, hass):
        """Entity with no tags is always forwarded."""
        from copilot_ha.neuron_feed_store import async_is_entity_neuron_fed

        with patch(
            "copilot_ha.entity_tags_store.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value={},
        ), patch(
            "copilot_ha.neuron_feed_store.async_get_neuron_feed_states",
            new_callable=AsyncMock,
            return_value={},
        ):
            result = await async_is_entity_neuron_fed(hass, "light.random")
            assert result is True

    @pytest.mark.asyncio
    async def test_entity_all_tags_disabled(self, hass):
        """Entity excluded when all its tags have feed disabled."""
        from copilot_ha.neuron_feed_store import async_is_entity_neuron_fed
        from copilot_ha.entity_tags_store import EntityTag

        tags = {
            "licht": EntityTag(
                tag_id="licht",
                name="Licht",
                entity_ids=["light.wohnzimmer"],
            ),
            "energie": EntityTag(
                tag_id="energie",
                name="Energie",
                entity_ids=["light.wohnzimmer", "sensor.power"],
            ),
        }
        feed_states = {"licht": False, "energie": False}

        with patch(
            "copilot_ha.entity_tags_store.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value=tags,
        ), patch(
            "copilot_ha.neuron_feed_store.async_get_neuron_feed_states",
            new_callable=AsyncMock,
            return_value=feed_states,
        ):
            result = await async_is_entity_neuron_fed(hass, "light.wohnzimmer")
            assert result is False

    @pytest.mark.asyncio
    async def test_entity_one_tag_enabled(self, hass):
        """Entity included if ANY tag has feed enabled."""
        from copilot_ha.neuron_feed_store import async_is_entity_neuron_fed
        from copilot_ha.entity_tags_store import EntityTag

        tags = {
            "licht": EntityTag(
                tag_id="licht",
                name="Licht",
                entity_ids=["light.wohnzimmer"],
            ),
            "energie": EntityTag(
                tag_id="energie",
                name="Energie",
                entity_ids=["light.wohnzimmer"],
            ),
        }
        feed_states = {"licht": False, "energie": True}

        with patch(
            "copilot_ha.entity_tags_store.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value=tags,
        ), patch(
            "copilot_ha.neuron_feed_store.async_get_neuron_feed_states",
            new_callable=AsyncMock,
            return_value=feed_states,
        ):
            result = await async_is_entity_neuron_fed(hass, "light.wohnzimmer")
            assert result is True


# ── NeuronFeedTagSwitch Tests ────────────────────────────────────────────


class TestNeuronFeedTagSwitch:
    """Test NeuronFeedTagSwitch entity behavior."""

    def test_switch_creation(self):
        """Switch can be instantiated with tag details."""
        from copilot_ha.neuron_feed_entities import NeuronFeedTagSwitch

        coord = _make_coordinator()
        sw = NeuronFeedTagSwitch(coord, "licht", "Licht")
        assert sw._tag_id == "licht"
        assert sw._attr_unique_id == "copilot_ha_neuron_feed_licht"
        assert "Licht" in sw._attr_name
        assert sw._attr_is_on is True  # default enabled

    def test_switch_extra_attributes(self):
        """Switch exposes tag info as attributes."""
        from copilot_ha.neuron_feed_entities import NeuronFeedTagSwitch

        coord = _make_coordinator()
        sw = NeuronFeedTagSwitch(coord, "klima", "Klima")
        attrs = sw.extra_state_attributes
        assert attrs["tag_id"] == "klima"
        assert attrs["tag_name"] == "Klima"

    @pytest.mark.asyncio
    async def test_switch_turn_off(self):
        """Turning off persists state."""
        from copilot_ha.neuron_feed_entities import NeuronFeedTagSwitch

        coord = _make_coordinator()
        sw = NeuronFeedTagSwitch(coord, "licht", "Licht")
        sw.hass = coord.hass

        with patch(
            "copilot_ha.neuron_feed_entities.async_set_neuron_feed_state",
            new_callable=AsyncMock,
        ) as mock_set:
            await sw.async_turn_off()
            mock_set.assert_called_once_with(coord.hass, "licht", False)
            assert sw._attr_is_on is False

    @pytest.mark.asyncio
    async def test_switch_turn_on(self):
        """Turning on persists state."""
        from copilot_ha.neuron_feed_entities import NeuronFeedTagSwitch

        coord = _make_coordinator()
        sw = NeuronFeedTagSwitch(coord, "licht", "Licht")
        sw.hass = coord.hass
        sw._attr_is_on = False

        with patch(
            "copilot_ha.neuron_feed_entities.async_set_neuron_feed_state",
            new_callable=AsyncMock,
        ) as mock_set:
            await sw.async_turn_on()
            mock_set.assert_called_once_with(coord.hass, "licht", True)
            assert sw._attr_is_on is True


# ── NeuronFeedSummarySensor Tests ────────────────────────────────────────


class TestNeuronFeedSummarySensor:
    """Test NeuronFeedSummarySensor entity."""

    def test_sensor_creation(self):
        """Sensor can be instantiated."""
        from copilot_ha.neuron_feed_entities import NeuronFeedSummarySensor

        coord = _make_coordinator()
        sensor = NeuronFeedSummarySensor(coord)
        assert sensor._attr_unique_id == "copilot_ha_neuron_feed_summary"
        assert "Neuron Feed" in sensor._attr_name

    def test_sensor_default_value(self):
        """Default value shows 0/0."""
        from copilot_ha.neuron_feed_entities import NeuronFeedSummarySensor

        coord = _make_coordinator()
        sensor = NeuronFeedSummarySensor(coord)
        assert "0" in sensor.native_value

    @pytest.mark.asyncio
    async def test_sensor_update(self):
        """Update computes correct included/excluded counts."""
        from copilot_ha.neuron_feed_entities import NeuronFeedSummarySensor
        from copilot_ha.entity_tags_store import EntityTag

        coord = _make_coordinator()
        sensor = NeuronFeedSummarySensor(coord)
        sensor.hass = coord.hass

        tags = {
            "licht": EntityTag(
                tag_id="licht",
                name="Licht",
                entity_ids=["light.a", "light.b"],
            ),
            "klima": EntityTag(
                tag_id="klima",
                name="Klima",
                entity_ids=["climate.c"],
            ),
        }
        feed_states = {"licht": False, "klima": True}

        with patch(
            "copilot_ha.neuron_feed_entities.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value=tags,
        ), patch(
            "copilot_ha.neuron_feed_entities.async_get_neuron_feed_states",
            new_callable=AsyncMock,
            return_value=feed_states,
        ):
            await sensor.async_update()

        # light.a, light.b only in "licht" (disabled) -> excluded
        # climate.c only in "klima" (enabled) -> included
        assert sensor._excluded == 2
        assert sensor._included == 1
        assert sensor._total_tags == 2
        assert sensor._enabled_tags == 1
        assert sensor.extra_state_attributes["included_entities"] == 1
        assert sensor.extra_state_attributes["excluded_entities"] == 2


# ── async_create_neuron_feed_entities Tests ──────────────────────────────


class TestCreateNeuronFeedEntities:
    """Test the factory function that creates switch + sensor entities."""

    @pytest.mark.asyncio
    async def test_creates_switches_per_tag(self):
        """One switch per tag + one summary sensor."""
        from copilot_ha.neuron_feed_entities import async_create_neuron_feed_entities
        from copilot_ha.entity_tags_store import EntityTag

        coord = _make_coordinator()
        tags = {
            "licht": EntityTag(tag_id="licht", name="Licht", entity_ids=["light.a"]),
            "klima": EntityTag(tag_id="klima", name="Klima", entity_ids=["climate.b"]),
        }

        with patch(
            "copilot_ha.neuron_feed_entities.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value=tags,
        ):
            result = await async_create_neuron_feed_entities(coord)

        assert len(result["switch"]) == 2
        assert len(result["sensor"]) == 1
        tag_ids = {sw._tag_id for sw in result["switch"]}
        assert tag_ids == {"licht", "klima"}

    @pytest.mark.asyncio
    async def test_no_tags_returns_empty_switches(self):
        """No tags -> no switches, still one summary sensor."""
        from copilot_ha.neuron_feed_entities import async_create_neuron_feed_entities

        coord = _make_coordinator()

        with patch(
            "copilot_ha.neuron_feed_entities.async_get_entity_tags",
            new_callable=AsyncMock,
            return_value={},
        ):
            result = await async_create_neuron_feed_entities(coord)

        assert len(result["switch"]) == 0
        assert len(result["sensor"]) == 1


# ── Zone Entity Select Tests ────────────────────────────────────────────


class TestZoneEntitySelect:
    """Test entity-centric zone assignment/removal."""

    @pytest.fixture
    def hass(self):
        hass = _make_hass()
        entry = _make_entry("test_entry")
        hass.config_entries.async_entries = MagicMock(return_value=[entry])
        return hass

    def _make_zones(self):
        """Create test zones."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2

        return [
            HabitusZoneV2(
                zone_id="zone:wohnzimmer",
                name="Wohnzimmer",
                entity_ids=("light.wohnzimmer", "sensor.temp_wz"),
            ),
            HabitusZoneV2(
                zone_id="zone:kueche",
                name="Kueche",
                entity_ids=("light.kueche",),
            ),
        ]

    @pytest.mark.asyncio
    async def test_assign_entity_to_zone(self, hass):
        """Assign an entity to a zone."""
        from copilot_ha.zone_entity_select import async_assign_entity_to_zone

        zones = self._make_zones()
        saved_zones = []

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ), patch(
            "copilot_ha.zone_entity_select.async_set_zones_v2",
            new_callable=AsyncMock,
            side_effect=lambda h, eid, z, **kw: saved_zones.extend(z),
        ):
            result = await async_assign_entity_to_zone(
                hass, "sensor.new_entity", "zone:kueche"
            )

        assert result is True
        # Find kueche in saved zones
        kueche = [z for z in saved_zones if z.zone_id == "zone:kueche"][0]
        assert "sensor.new_entity" in kueche.entity_ids

    @pytest.mark.asyncio
    async def test_assign_moves_between_zones(self, hass):
        """Moving entity from one zone to another."""
        from copilot_ha.zone_entity_select import async_assign_entity_to_zone

        zones = self._make_zones()
        saved_zones = []

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ), patch(
            "copilot_ha.zone_entity_select.async_set_zones_v2",
            new_callable=AsyncMock,
            side_effect=lambda h, eid, z, **kw: saved_zones.extend(z),
        ):
            # Move light.wohnzimmer from wohnzimmer to kueche
            result = await async_assign_entity_to_zone(
                hass, "light.wohnzimmer", "zone:kueche"
            )

        assert result is True
        wz = [z for z in saved_zones if z.zone_id == "zone:wohnzimmer"][0]
        ku = [z for z in saved_zones if z.zone_id == "zone:kueche"][0]
        assert "light.wohnzimmer" not in wz.entity_ids
        assert "light.wohnzimmer" in ku.entity_ids

    @pytest.mark.asyncio
    async def test_assign_to_nonexistent_zone(self, hass):
        """Assigning to a nonexistent zone returns False."""
        from copilot_ha.zone_entity_select import async_assign_entity_to_zone

        zones = self._make_zones()

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ):
            result = await async_assign_entity_to_zone(
                hass, "light.x", "zone:nonexistent"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_entity_from_zone(self, hass):
        """Remove an entity from all zones."""
        from copilot_ha.zone_entity_select import async_remove_entity_from_zone

        zones = self._make_zones()
        saved_zones = []

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ), patch(
            "copilot_ha.zone_entity_select.async_set_zones_v2",
            new_callable=AsyncMock,
            side_effect=lambda h, eid, z, **kw: saved_zones.extend(z),
        ):
            result = await async_remove_entity_from_zone(hass, "light.wohnzimmer")

        assert result is True
        wz = [z for z in saved_zones if z.zone_id == "zone:wohnzimmer"][0]
        assert "light.wohnzimmer" not in wz.entity_ids

    @pytest.mark.asyncio
    async def test_remove_nonexistent_entity(self, hass):
        """Removing an entity not in any zone returns False."""
        from copilot_ha.zone_entity_select import async_remove_entity_from_zone

        zones = self._make_zones()

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ):
            result = await async_remove_entity_from_zone(hass, "light.nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_entity_zone(self, hass):
        """Get current zone of an entity."""
        from copilot_ha.zone_entity_select import async_get_entity_zone

        zones = self._make_zones()

        with patch(
            "copilot_ha.zone_entity_select.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ):
            zone = await async_get_entity_zone(hass, "light.wohnzimmer")
            assert zone == "zone:wohnzimmer"

            zone = await async_get_entity_zone(hass, "light.nonexistent")
            assert zone is None


# ── Tag Entity Service Logic Tests ───────────────────────────────────────


class TestTagEntityLogic:
    """Test entity-centric tag assignment logic."""

    @pytest.mark.asyncio
    async def test_tag_entity_adds_to_existing_tag(self):
        """tag_entity adds entity to existing tag's entity_ids."""
        from copilot_ha.entity_tags_store import EntityTag

        tags = {
            "licht": EntityTag(
                tag_id="licht",
                name="Licht",
                entity_ids=["light.existing"],
            ),
        }
        saved = {}

        async def mock_save(hass, t):
            saved.update(t)

        async def mock_get(hass):
            return tags

        with patch(
            "copilot_ha.entity_tags_store.async_get_entity_tags",
            side_effect=mock_get,
        ), patch(
            "copilot_ha.entity_tags_store.async_save_entity_tags",
            side_effect=mock_save,
        ):
            # Simulate what the service handler does
            entity_id = "light.new_entity"
            tag_ids = ["licht"]

            loaded = await mock_get(None)
            changed = False
            for tid in tag_ids:
                if tid in loaded and entity_id not in loaded[tid].entity_ids:
                    loaded[tid].entity_ids.append(entity_id)
                    changed = True
            if changed:
                await mock_save(None, loaded)

        assert "light.new_entity" in tags["licht"].entity_ids

    @pytest.mark.asyncio
    async def test_untag_entity_removes_from_tag(self):
        """untag_entity removes entity from tag's entity_ids."""
        from copilot_ha.entity_tags_store import EntityTag

        tags = {
            "licht": EntityTag(
                tag_id="licht",
                name="Licht",
                entity_ids=["light.a", "light.b"],
            ),
        }
        saved = {}

        async def mock_save(hass, t):
            saved.update(t)

        async def mock_get(hass):
            return tags

        with patch(
            "copilot_ha.entity_tags_store.async_get_entity_tags",
            side_effect=mock_get,
        ), patch(
            "copilot_ha.entity_tags_store.async_save_entity_tags",
            side_effect=mock_save,
        ):
            entity_id = "light.a"
            tag_ids = ["licht"]

            loaded = await mock_get(None)
            changed = False
            for tid in tag_ids:
                if tid in loaded and entity_id in loaded[tid].entity_ids:
                    loaded[tid].entity_ids.remove(entity_id)
                    changed = True
            if changed:
                await mock_save(None, loaded)

        assert "light.a" not in tags["licht"].entity_ids
        assert "light.b" in tags["licht"].entity_ids


# ── Zone Rebuild Helper Tests ────────────────────────────────────────────


class TestZoneRebuildHelper:
    """Test _rebuild_zone_with_entity helper."""

    def test_add_entity(self):
        """Adding entity to zone."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
        from copilot_ha.zone_entity_select import _rebuild_zone_with_entity

        zone = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("light.a",),
        )
        updated = _rebuild_zone_with_entity(zone, "light.b", add=True)
        assert "light.b" in updated.entity_ids
        assert "light.a" in updated.entity_ids

    def test_remove_entity(self):
        """Removing entity from zone."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
        from copilot_ha.zone_entity_select import _rebuild_zone_with_entity

        zone = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("light.a", "light.b"),
        )
        updated = _rebuild_zone_with_entity(zone, "light.a", add=False)
        assert "light.a" not in updated.entity_ids
        assert "light.b" in updated.entity_ids

    def test_add_to_role_mapping(self):
        """Adding entity updates role mapping too."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
        from copilot_ha.zone_entity_select import _rebuild_zone_with_entity

        zone = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("light.a",),
            entities={"lights": ("light.a",)},
        )
        updated = _rebuild_zone_with_entity(zone, "sensor.temp", add=True)
        assert "sensor.temp" in updated.entity_ids
        assert updated.entities is not None
        assert "sensor.temp" in updated.entities.get("other", ())

    def test_remove_from_role_mapping(self):
        """Removing entity cleans up role mapping."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
        from copilot_ha.zone_entity_select import _rebuild_zone_with_entity

        zone = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("light.a", "sensor.temp"),
            entities={"lights": ("light.a",), "other": ("sensor.temp",)},
        )
        updated = _rebuild_zone_with_entity(zone, "sensor.temp", add=False)
        assert "sensor.temp" not in updated.entity_ids
        # "other" role should be cleaned up
        if updated.entities:
            assert "sensor.temp" not in updated.entities.get("other", ())

    def test_remove_only_entity_in_role(self):
        """Removing sole entity in a role removes the role key."""
        from copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
        from copilot_ha.zone_entity_select import _rebuild_zone_with_entity

        zone = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("sensor.temp",),
            entities={"other": ("sensor.temp",)},
        )
        updated = _rebuild_zone_with_entity(zone, "sensor.temp", add=False)
        # entities should be None because all roles are empty
        assert updated.entities is None
