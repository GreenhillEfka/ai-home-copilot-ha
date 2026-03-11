"""Tests for PilotSuite HA modules (Licht, Helligkeit, Heiz, Bewegung, Praesenz).

Tests instantiation, update_zone, get_zone, get_summary, and
PraesenzModule.get_persons_home() for all five Habitus tracking modules.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from dataclasses import dataclass
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.copilot_ha.core.modules.licht_module import LichtModule
from custom_components.copilot_ha.core.modules.helligkeit_module import HelligkeitModule
from custom_components.copilot_ha.core.modules.heiz_module import HeizModule
from custom_components.copilot_ha.core.modules.bewegung_module import BewegungModule
from custom_components.copilot_ha.core.modules.praesenz_module import PraesenzModule


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_ctx(entry_id: str = "test_entry_1"):
    """Create a lightweight mock ModuleContext."""
    hass = MagicMock()
    hass.data = {}

    entry = MagicMock()
    entry.entry_id = entry_id
    entry.domain = "copilot_ha"

    ctx = MagicMock()
    ctx.hass = hass
    ctx.entry = entry
    ctx.entry_id = entry_id
    return ctx


# ── LichtModule ──────────────────────────────────────────────────────────


class TestLichtModuleInstantiation:
    """Test LichtModule creation and basic properties."""

    def test_instantiation(self):
        mod = LichtModule()
        assert mod is not None

    def test_name(self):
        mod = LichtModule()
        assert mod.name == "licht_module"

    def test_initial_state_empty(self):
        mod = LichtModule()
        assert mod.get_zone("any") is None
        assert mod.get_summary() == {"total_zones": 0, "total_lights_on": 0}


class TestLichtModuleUpdateZone:
    """Test LichtModule.update_zone / get_zone / get_summary."""

    @pytest.fixture
    def mod(self):
        return LichtModule()

    def test_update_and_get_zone(self, mod):
        mod.update_zone("wohnzimmer", lights_on=3, lights_total=5, avg_brightness=78.5, auto_enabled=True)
        zone = mod.get_zone("wohnzimmer")
        assert zone is not None
        assert zone["lights_on"] == 3
        assert zone["lights_total"] == 5
        assert zone["avg_brightness"] == 78.5
        assert zone["auto_enabled"] is True

    def test_get_zone_unknown(self, mod):
        assert mod.get_zone("unknown") is None

    def test_update_overwrites(self, mod):
        mod.update_zone("kueche", lights_on=1, lights_total=4, avg_brightness=50.0, auto_enabled=False)
        mod.update_zone("kueche", lights_on=4, lights_total=4, avg_brightness=100.0, auto_enabled=True)
        zone = mod.get_zone("kueche")
        assert zone["lights_on"] == 4
        assert zone["avg_brightness"] == 100.0

    def test_summary_multiple_zones(self, mod):
        mod.update_zone("z1", lights_on=2, lights_total=3, avg_brightness=60.0, auto_enabled=True)
        mod.update_zone("z2", lights_on=0, lights_total=2, avg_brightness=0.0, auto_enabled=False)
        mod.update_zone("z3", lights_on=1, lights_total=1, avg_brightness=100.0, auto_enabled=True)
        summary = mod.get_summary()
        assert summary["total_zones"] == 3
        assert summary["total_lights_on"] == 3


class TestLichtModuleLifecycle:
    """Test async_setup_entry / async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_in_hass_data(self):
        mod = LichtModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)

        assert ctx.hass.data["copilot_ha"][ctx.entry_id]["licht_module"] is mod

    @pytest.mark.asyncio
    async def test_unload_removes_from_hass_data(self):
        mod = LichtModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)
        result = await mod.async_unload_entry(ctx)

        assert result is True
        assert "licht_module" not in ctx.hass.data["copilot_ha"][ctx.entry_id]


# ── HelligkeitModule ─────────────────────────────────────────────────────


class TestHelligkeitModuleInstantiation:
    """Test HelligkeitModule creation and basic properties."""

    def test_instantiation(self):
        mod = HelligkeitModule()
        assert mod is not None

    def test_name(self):
        mod = HelligkeitModule()
        assert mod.name == "helligkeit_module"

    def test_initial_state_empty(self):
        mod = HelligkeitModule()
        assert mod.get_zone("any") is None
        assert mod.get_summary() == {"total_zones": 0, "zones_needing_light": 0}


class TestHelligkeitModuleUpdateZone:
    """Test HelligkeitModule.update_zone / get_zone / get_summary."""

    @pytest.fixture
    def mod(self):
        return HelligkeitModule()

    def test_update_and_get_zone(self, mod):
        mod.update_zone("flur", avg_indoor_lux=120.0, avg_outdoor_lux=8000.0, needs_light=False, deficit_pct=0.0)
        zone = mod.get_zone("flur")
        assert zone is not None
        assert zone["avg_indoor_lux"] == 120.0
        assert zone["avg_outdoor_lux"] == 8000.0
        assert zone["needs_light"] is False
        assert zone["deficit_pct"] == 0.0

    def test_get_zone_unknown(self, mod):
        assert mod.get_zone("nope") is None

    def test_summary_zones_needing_light(self, mod):
        mod.update_zone("z1", avg_indoor_lux=50.0, avg_outdoor_lux=100.0, needs_light=True, deficit_pct=60.0)
        mod.update_zone("z2", avg_indoor_lux=300.0, avg_outdoor_lux=5000.0, needs_light=False, deficit_pct=0.0)
        mod.update_zone("z3", avg_indoor_lux=20.0, avg_outdoor_lux=80.0, needs_light=True, deficit_pct=80.0)
        summary = mod.get_summary()
        assert summary["total_zones"] == 3
        assert summary["zones_needing_light"] == 2


class TestHelligkeitModuleLifecycle:
    """Test async_setup_entry / async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_in_hass_data(self):
        mod = HelligkeitModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)

        assert ctx.hass.data["copilot_ha"][ctx.entry_id]["helligkeit_module"] is mod

    @pytest.mark.asyncio
    async def test_unload_removes_from_hass_data(self):
        mod = HelligkeitModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)
        result = await mod.async_unload_entry(ctx)

        assert result is True
        assert "helligkeit_module" not in ctx.hass.data["copilot_ha"][ctx.entry_id]


# ── HeizModule ───────────────────────────────────────────────────────────


class TestHeizModuleInstantiation:
    """Test HeizModule creation and basic properties."""

    def test_instantiation(self):
        mod = HeizModule()
        assert mod is not None

    def test_name(self):
        mod = HeizModule()
        assert mod.name == "heiz_module"

    def test_initial_state_empty(self):
        mod = HeizModule()
        assert mod.get_zone("any") is None
        assert mod.get_summary() == {"total_zones": 0, "zones_heating": 0, "zones_eco_mode": 0}


class TestHeizModuleUpdateZone:
    """Test HeizModule.update_zone / get_zone / get_summary."""

    @pytest.fixture
    def mod(self):
        return HeizModule()

    def test_update_and_get_zone(self, mod):
        mod.update_zone("bad", current_temp=22.5, target_temp=23.0, humidity=55, is_heating=True, eco_mode=False, comfort_index=0.85)
        zone = mod.get_zone("bad")
        assert zone is not None
        assert zone["current_temp"] == 22.5
        assert zone["target_temp"] == 23.0
        assert zone["humidity"] == 55
        assert zone["is_heating"] is True
        assert zone["eco_mode"] is False
        assert zone["comfort_index"] == 0.85

    def test_get_zone_unknown(self, mod):
        assert mod.get_zone("nowhere") is None

    def test_update_merges_kwargs(self, mod):
        """HeizModule.update_zone uses **kwargs and merges into existing data."""
        mod.update_zone("schlafzimmer", current_temp=20.0, is_heating=False)
        mod.update_zone("schlafzimmer", humidity=45, eco_mode=True)
        zone = mod.get_zone("schlafzimmer")
        assert zone["current_temp"] == 20.0
        assert zone["humidity"] == 45
        assert zone["eco_mode"] is True

    def test_summary_counts(self, mod):
        mod.update_zone("z1", is_heating=True, eco_mode=False)
        mod.update_zone("z2", is_heating=False, eco_mode=True)
        mod.update_zone("z3", is_heating=True, eco_mode=True)
        summary = mod.get_summary()
        assert summary["total_zones"] == 3
        assert summary["zones_heating"] == 2
        assert summary["zones_eco_mode"] == 2


class TestHeizModuleLifecycle:
    """Test async_setup_entry / async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_in_hass_data(self):
        mod = HeizModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)

        assert ctx.hass.data["copilot_ha"][ctx.entry_id]["heiz_module"] is mod

    @pytest.mark.asyncio
    async def test_unload_removes_from_hass_data(self):
        mod = HeizModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)
        result = await mod.async_unload_entry(ctx)

        assert result is True
        assert "heiz_module" not in ctx.hass.data["copilot_ha"][ctx.entry_id]


# ── BewegungModule ───────────────────────────────────────────────────────


class TestBewegungModuleInstantiation:
    """Test BewegungModule creation and basic properties."""

    def test_instantiation(self):
        mod = BewegungModule()
        assert mod is not None

    def test_name(self):
        mod = BewegungModule()
        assert mod.name == "bewegung_module"

    def test_initial_state_empty(self):
        mod = BewegungModule()
        assert mod.get_zone("any") is None
        assert mod.get_summary() == {"total_zones": 0, "zones_with_recent_motion": 0}


class TestBewegungModuleUpdateZone:
    """Test BewegungModule.update_zone / get_zone / get_summary."""

    @pytest.fixture
    def mod(self):
        return BewegungModule()

    def test_update_and_get_zone(self, mod):
        mod.update_zone("flur", sensors_active=2, sensors_total=3, last_motion="2026-03-11T10:00:00", has_recent_motion=True)
        zone = mod.get_zone("flur")
        assert zone is not None
        assert zone["sensors_active"] == 2
        assert zone["sensors_total"] == 3
        assert zone["has_recent_motion"] is True

    def test_get_zone_unknown(self, mod):
        assert mod.get_zone("nowhere") is None

    def test_update_merges_kwargs(self, mod):
        mod.update_zone("garage", sensors_active=0, sensors_total=1)
        mod.update_zone("garage", has_recent_motion=False)
        zone = mod.get_zone("garage")
        assert zone["sensors_active"] == 0
        assert zone["has_recent_motion"] is False

    def test_summary_counts_recent_motion(self, mod):
        mod.update_zone("z1", has_recent_motion=True)
        mod.update_zone("z2", has_recent_motion=False)
        mod.update_zone("z3", has_recent_motion=True)
        summary = mod.get_summary()
        assert summary["total_zones"] == 3
        assert summary["zones_with_recent_motion"] == 2


class TestBewegungModuleLifecycle:
    """Test async_setup_entry / async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_in_hass_data(self):
        mod = BewegungModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)

        assert ctx.hass.data["copilot_ha"][ctx.entry_id]["bewegung_module"] is mod

    @pytest.mark.asyncio
    async def test_unload_removes_from_hass_data(self):
        mod = BewegungModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)
        result = await mod.async_unload_entry(ctx)

        assert result is True
        assert "bewegung_module" not in ctx.hass.data["copilot_ha"][ctx.entry_id]


# ── PraesenzModule ───────────────────────────────────────────────────────


class TestPraesenzModuleInstantiation:
    """Test PraesenzModule creation and basic properties."""

    def test_instantiation(self):
        mod = PraesenzModule()
        assert mod is not None

    def test_name(self):
        mod = PraesenzModule()
        assert mod.name == "praesenz_module"

    def test_initial_state_empty(self):
        mod = PraesenzModule()
        assert mod.get_zone("any") is None
        summary = mod.get_summary()
        assert summary == {
            "total_zones": 0,
            "zones_occupied": 0,
            "total_persons": 0,
            "persons_home": [],
        }


class TestPraesenzModuleUpdateZone:
    """Test PraesenzModule.update_zone / get_zone / get_summary."""

    @pytest.fixture
    def mod(self):
        return PraesenzModule()

    def test_update_and_get_zone(self, mod):
        mod.update_zone("wohnzimmer", is_occupied=True, person_count=2, persons=["Alice", "Bob"], last_entered="2026-03-11T09:30:00")
        zone = mod.get_zone("wohnzimmer")
        assert zone is not None
        assert zone["is_occupied"] is True
        assert zone["person_count"] == 2
        assert zone["persons"] == ["Alice", "Bob"]

    def test_get_zone_unknown(self, mod):
        assert mod.get_zone("nirgends") is None

    def test_update_merges_kwargs(self, mod):
        mod.update_zone("kueche", is_occupied=True, person_count=1)
        mod.update_zone("kueche", persons=["Charlie"])
        zone = mod.get_zone("kueche")
        assert zone["is_occupied"] is True
        assert zone["persons"] == ["Charlie"]

    def test_summary_occupied_and_persons(self, mod):
        mod.update_zone("z1", is_occupied=True, person_count=2, persons=["Alice", "Bob"])
        mod.update_zone("z2", is_occupied=False, person_count=0, persons=[])
        mod.update_zone("z3", is_occupied=True, person_count=1, persons=["Charlie"])
        summary = mod.get_summary()
        assert summary["total_zones"] == 3
        assert summary["zones_occupied"] == 2
        assert summary["total_persons"] == 3
        assert sorted(summary["persons_home"]) == ["Alice", "Bob", "Charlie"]


class TestPraesenzModuleGetPersonsHome:
    """Test PraesenzModule.get_persons_home() specifically."""

    @pytest.fixture
    def mod(self):
        return PraesenzModule()

    def test_empty_returns_empty_list(self, mod):
        assert mod.get_persons_home() == []

    def test_single_zone_single_person(self, mod):
        mod.update_zone("z1", is_occupied=True, persons=["Alice"])
        assert mod.get_persons_home() == ["Alice"]

    def test_multiple_zones_deduplicated(self, mod):
        """Same person in multiple zones should appear only once."""
        mod.update_zone("z1", is_occupied=True, persons=["Alice", "Bob"])
        mod.update_zone("z2", is_occupied=True, persons=["Bob", "Charlie"])
        result = mod.get_persons_home()
        assert result == ["Alice", "Bob", "Charlie"]

    def test_unoccupied_zones_excluded(self, mod):
        """Persons in unoccupied zones should not be included."""
        mod.update_zone("z1", is_occupied=True, persons=["Alice"])
        mod.update_zone("z2", is_occupied=False, persons=["Ghost"])
        assert mod.get_persons_home() == ["Alice"]

    def test_zone_with_no_persons_key(self, mod):
        """Zone occupied but no persons list should not crash."""
        mod.update_zone("z1", is_occupied=True)
        assert mod.get_persons_home() == []

    def test_zone_with_empty_persons(self, mod):
        """Zone occupied with empty persons list."""
        mod.update_zone("z1", is_occupied=True, persons=[])
        assert mod.get_persons_home() == []

    def test_result_is_sorted(self, mod):
        mod.update_zone("z1", is_occupied=True, persons=["Zara", "Anna", "Mia"])
        assert mod.get_persons_home() == ["Anna", "Mia", "Zara"]


class TestPraesenzModuleLifecycle:
    """Test async_setup_entry / async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_in_hass_data(self):
        mod = PraesenzModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)

        assert ctx.hass.data["copilot_ha"][ctx.entry_id]["praesenz_module"] is mod

    @pytest.mark.asyncio
    async def test_unload_removes_from_hass_data(self):
        mod = PraesenzModule()
        ctx = _make_ctx()
        await mod.async_setup_entry(ctx)
        result = await mod.async_unload_entry(ctx)

        assert result is True
        assert "praesenz_module" not in ctx.hass.data["copilot_ha"][ctx.entry_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
