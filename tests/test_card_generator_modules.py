"""Tests for card_generator module-tab view functions (v6.0.0).

Tests the 5 new generate_*_view functions added for the Habitus module tabs:
- generate_licht_view
- generate_helligkeit_view
- generate_heiz_view
- generate_bewegung_view
- generate_praesenz_view

Each view must return a valid Lovelace tab dict with title, path, icon, cards keys.
Tests cover both with-zones and without-zones invocations.
"""

import pytest
import sys
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.copilot_ha.dashboard.card_generator import (
    generate_licht_view,
    generate_helligkeit_view,
    generate_heiz_view,
    generate_bewegung_view,
    generate_praesenz_view,
)


# ── Helpers ──────────────────────────────────────────────────────────────

REQUIRED_VIEW_KEYS = {"title", "path", "icon", "cards"}


def _sample_zones() -> list[dict[str, Any]]:
    """Return a realistic list of Habitus zones with entities for testing."""
    return [
        {
            "zone_id": "wohnbereich",
            "zone_name": "Wohnbereich",
            "entities": {
                "lights": ["light.wohnzimmer_decke", "light.wohnzimmer_stehlampe"],
                "brightness": ["sensor.wohnzimmer_lux"],
                "illuminance": [],
                "heating": ["climate.wohnzimmer"],
                "temperature": ["sensor.wohnzimmer_temp"],
                "humidity": ["sensor.wohnzimmer_humidity"],
                "motion": ["binary_sensor.wohnzimmer_motion"],
            },
        },
        {
            "zone_id": "schlafbereich",
            "zone_name": "Schlafbereich",
            "entities": {
                "lights": ["light.schlafzimmer_decke"],
                "brightness": [],
                "illuminance": ["sensor.schlafzimmer_illuminance"],
                "heating": ["climate.schlafzimmer"],
                "temperature": ["sensor.schlafzimmer_temp"],
                "humidity": [],
                "motion": ["binary_sensor.schlafzimmer_motion"],
            },
        },
    ]


def _assert_valid_view(view: dict[str, Any]) -> None:
    """Assert that a view dict has all required Lovelace tab keys."""
    for key in REQUIRED_VIEW_KEYS:
        assert key in view, f"Missing required key '{key}' in view"
    assert isinstance(view["title"], str) and len(view["title"]) > 0
    assert isinstance(view["path"], str) and len(view["path"]) > 0
    assert isinstance(view["icon"], str) and view["icon"].startswith("mdi:")
    assert isinstance(view["cards"], list) and len(view["cards"]) > 0


# ── generate_licht_view ─────────────────────────────────────────────────


class TestGenerateLichtViewNoZones:
    """Test generate_licht_view without zones."""

    def test_returns_valid_view(self):
        view = generate_licht_view()
        _assert_valid_view(view)

    def test_title_and_path(self):
        view = generate_licht_view()
        assert view["title"] == "Licht"
        assert view["path"] == "licht"

    def test_icon(self):
        view = generate_licht_view()
        assert view["icon"] == "mdi:lightbulb-group"

    def test_has_overview_card(self):
        view = generate_licht_view()
        overview = view["cards"][0]
        assert overview["type"] == "entities"
        assert overview["title"] == "Licht-Uebersicht"

    def test_no_zone_cards_without_zones(self):
        view = generate_licht_view()
        assert len(view["cards"]) == 1  # only the overview card

    def test_none_zones_same_as_no_arg(self):
        view = generate_licht_view(zones=None)
        _assert_valid_view(view)
        assert len(view["cards"]) == 1


class TestGenerateLichtViewWithZones:
    """Test generate_licht_view with zones parameter."""

    def test_returns_valid_view(self):
        view = generate_licht_view(zones=_sample_zones())
        _assert_valid_view(view)

    def test_adds_zone_cards(self):
        zones = _sample_zones()
        view = generate_licht_view(zones=zones)
        # 1 overview + 2 zone cards (both zones have lights)
        assert len(view["cards"]) == 3

    def test_zone_card_titles(self):
        zones = _sample_zones()
        view = generate_licht_view(zones=zones)
        titles = [c["title"] for c in view["cards"][1:]]
        assert "Wohnbereich" in titles
        assert "Schlafbereich" in titles

    def test_zone_card_has_light_entities(self):
        zones = _sample_zones()
        view = generate_licht_view(zones=zones)
        wohn_card = view["cards"][1]
        entity_ids = [e["entity"] for e in wohn_card["entities"]]
        assert "light.wohnzimmer_decke" in entity_ids

    def test_zone_without_lights_skipped(self):
        zones = [{"zone_id": "keller", "zone_name": "Keller", "entities": {"lights": []}}]
        view = generate_licht_view(zones=zones)
        assert len(view["cards"]) == 1  # only overview, no zone card

    def test_empty_zones_list(self):
        view = generate_licht_view(zones=[])
        _assert_valid_view(view)
        assert len(view["cards"]) == 1


# ── generate_helligkeit_view ─────────────────────────────────────────────


class TestGenerateHelligkeitViewNoZones:
    """Test generate_helligkeit_view without zones."""

    def test_returns_valid_view(self):
        view = generate_helligkeit_view()
        _assert_valid_view(view)

    def test_title_and_path(self):
        view = generate_helligkeit_view()
        assert view["title"] == "Helligkeit"
        assert view["path"] == "helligkeit"

    def test_icon(self):
        view = generate_helligkeit_view()
        assert view["icon"] == "mdi:brightness-6"

    def test_has_gauge_overview(self):
        view = generate_helligkeit_view()
        first_card = view["cards"][0]
        assert first_card["type"] == "horizontal-stack"

    def test_no_zone_cards_without_zones(self):
        view = generate_helligkeit_view()
        assert len(view["cards"]) == 1


class TestGenerateHelligkeitViewWithZones:
    """Test generate_helligkeit_view with zones parameter."""

    def test_returns_valid_view(self):
        view = generate_helligkeit_view(zones=_sample_zones())
        _assert_valid_view(view)

    def test_adds_zone_sensor_cards(self):
        zones = _sample_zones()
        view = generate_helligkeit_view(zones=zones)
        # 1 overview + 2 zones (wohnbereich has brightness, schlafbereich has illuminance)
        assert len(view["cards"]) == 3

    def test_zone_sensor_card_has_graph(self):
        zones = _sample_zones()
        view = generate_helligkeit_view(zones=zones)
        sensor_card = view["cards"][1]
        assert sensor_card["type"] == "sensor"
        assert sensor_card["graph"] == "line"

    def test_zone_without_brightness_skipped(self):
        zones = [{"zone_id": "keller", "zone_name": "Keller", "entities": {"brightness": [], "illuminance": []}}]
        view = generate_helligkeit_view(zones=zones)
        assert len(view["cards"]) == 1

    def test_empty_zones_list(self):
        view = generate_helligkeit_view(zones=[])
        _assert_valid_view(view)
        assert len(view["cards"]) == 1


# ── generate_heiz_view ──────────────────────────────────────────────────


class TestGenerateHeizViewNoZones:
    """Test generate_heiz_view without zones."""

    def test_returns_valid_view(self):
        view = generate_heiz_view()
        _assert_valid_view(view)

    def test_title_and_path(self):
        view = generate_heiz_view()
        assert view["title"] == "Heizung"
        assert view["path"] == "heizung"

    def test_icon(self):
        view = generate_heiz_view()
        assert view["icon"] == "mdi:thermostat"

    def test_has_gauge_overview(self):
        view = generate_heiz_view()
        first_card = view["cards"][0]
        assert first_card["type"] == "horizontal-stack"

    def test_no_zone_cards_without_zones(self):
        view = generate_heiz_view()
        assert len(view["cards"]) == 1


class TestGenerateHeizViewWithZones:
    """Test generate_heiz_view with zones parameter."""

    def test_returns_valid_view(self):
        view = generate_heiz_view(zones=_sample_zones())
        _assert_valid_view(view)

    def test_adds_zone_thermostat_cards(self):
        zones = _sample_zones()
        view = generate_heiz_view(zones=zones)
        # 1 overview + 2 zone stacks (both have heating entities)
        assert len(view["cards"]) == 3

    def test_zone_card_has_thermostat(self):
        zones = _sample_zones()
        view = generate_heiz_view(zones=zones)
        zone_stack = view["cards"][1]
        assert zone_stack["type"] == "vertical-stack"
        thermostat = zone_stack["cards"][0]
        assert thermostat["type"] == "thermostat"

    def test_zone_card_includes_temp_and_humidity(self):
        zones = _sample_zones()
        view = generate_heiz_view(zones=zones)
        # Wohnbereich has both temp and humidity
        wohn_stack = view["cards"][1]
        side_stack = wohn_stack["cards"][1]
        assert side_stack["type"] == "horizontal-stack"
        side_entities = [c["entity"] for c in side_stack["cards"]]
        assert "sensor.wohnzimmer_temp" in side_entities
        assert "sensor.wohnzimmer_humidity" in side_entities

    def test_zone_without_heating_skipped(self):
        zones = [{"zone_id": "garten", "zone_name": "Garten", "entities": {"heating": [], "temperature": [], "humidity": []}}]
        view = generate_heiz_view(zones=zones)
        assert len(view["cards"]) == 1

    def test_empty_zones_list(self):
        view = generate_heiz_view(zones=[])
        _assert_valid_view(view)
        assert len(view["cards"]) == 1


# ── generate_bewegung_view ───────────────────────────────────────────────


class TestGenerateBewegungViewNoZones:
    """Test generate_bewegung_view without zones."""

    def test_returns_valid_view(self):
        view = generate_bewegung_view()
        _assert_valid_view(view)

    def test_title_and_path(self):
        view = generate_bewegung_view()
        assert view["title"] == "Bewegung"
        assert view["path"] == "bewegung"

    def test_icon(self):
        view = generate_bewegung_view()
        assert view["icon"] == "mdi:motion-sensor"

    def test_has_overview_card(self):
        view = generate_bewegung_view()
        overview = view["cards"][0]
        assert overview["type"] == "entities"
        assert overview["title"] == "Bewegungs-Uebersicht"

    def test_no_zone_cards_without_zones(self):
        view = generate_bewegung_view()
        assert len(view["cards"]) == 1


class TestGenerateBewegungViewWithZones:
    """Test generate_bewegung_view with zones parameter."""

    def test_returns_valid_view(self):
        view = generate_bewegung_view(zones=_sample_zones())
        _assert_valid_view(view)

    def test_adds_zone_motion_cards(self):
        zones = _sample_zones()
        view = generate_bewegung_view(zones=zones)
        # 1 overview + 2 zone stacks (both have motion entities)
        assert len(view["cards"]) == 3

    def test_zone_card_is_vertical_stack(self):
        zones = _sample_zones()
        view = generate_bewegung_view(zones=zones)
        zone_card = view["cards"][1]
        assert zone_card["type"] == "vertical-stack"

    def test_zone_card_has_motion_entity_and_graph(self):
        zones = _sample_zones()
        view = generate_bewegung_view(zones=zones)
        zone_card = view["cards"][1]
        inner_cards = zone_card["cards"]
        assert len(inner_cards) == 2
        assert inner_cards[0]["type"] == "entity"
        assert inner_cards[1]["type"] == "sensor"
        assert inner_cards[1]["graph"] == "line"

    def test_zone_without_motion_skipped(self):
        zones = [{"zone_id": "keller", "zone_name": "Keller", "entities": {"motion": []}}]
        view = generate_bewegung_view(zones=zones)
        assert len(view["cards"]) == 1

    def test_empty_zones_list(self):
        view = generate_bewegung_view(zones=[])
        _assert_valid_view(view)
        assert len(view["cards"]) == 1


# ── generate_praesenz_view ───────────────────────────────────────────────


class TestGeneratePraesenzViewNoZones:
    """Test generate_praesenz_view without zones."""

    def test_returns_valid_view(self):
        view = generate_praesenz_view()
        _assert_valid_view(view)

    def test_title_and_path(self):
        view = generate_praesenz_view()
        assert view["title"] == "Praesenz"
        assert view["path"] == "praesenz-modul"

    def test_icon(self):
        view = generate_praesenz_view()
        assert view["icon"] == "mdi:account-group"

    def test_has_persons_overview_card(self):
        view = generate_praesenz_view()
        overview = view["cards"][0]
        assert overview["type"] == "entities"
        assert overview["title"] == "Personen zu Hause"

    def test_has_markdown_summary(self):
        view = generate_praesenz_view()
        # Without zones: overview card + markdown card
        last_card = view["cards"][-1]
        assert last_card["type"] == "markdown"
        assert last_card["title"] == "Praesenz-Uebersicht"

    def test_no_zone_grid_without_zones(self):
        view = generate_praesenz_view()
        # Should have exactly 2 cards: overview + markdown
        assert len(view["cards"]) == 2

    def test_none_zones_same_as_no_arg(self):
        view = generate_praesenz_view(zones=None)
        _assert_valid_view(view)
        assert len(view["cards"]) == 2


class TestGeneratePraesenzViewWithZones:
    """Test generate_praesenz_view with zones parameter."""

    def test_returns_valid_view(self):
        view = generate_praesenz_view(zones=_sample_zones())
        _assert_valid_view(view)

    def test_adds_zone_grid(self):
        zones = _sample_zones()
        view = generate_praesenz_view(zones=zones)
        # overview + zone grid + markdown = 3 cards
        assert len(view["cards"]) == 3

    def test_zone_grid_structure(self):
        zones = _sample_zones()
        view = generate_praesenz_view(zones=zones)
        grid = view["cards"][1]
        assert grid["type"] == "grid"
        assert grid["columns"] == 2
        assert len(grid["cards"]) == 2  # 2 zones

    def test_zone_grid_card_entities(self):
        zones = _sample_zones()
        view = generate_praesenz_view(zones=zones)
        grid = view["cards"][1]
        first_zone_card = grid["cards"][0]
        assert first_zone_card["title"] == "Wohnbereich"
        entity_ids = [e["entity"] for e in first_zone_card["entities"]]
        assert "binary_sensor.pilotsuite_zone_presence_wohnbereich" in entity_ids
        assert "sensor.pilotsuite_wohnbereich_person_count" in entity_ids

    def test_markdown_still_present_with_zones(self):
        zones = _sample_zones()
        view = generate_praesenz_view(zones=zones)
        last_card = view["cards"][-1]
        assert last_card["type"] == "markdown"

    def test_empty_zones_list(self):
        view = generate_praesenz_view(zones=[])
        _assert_valid_view(view)
        # Empty zones list: no grid added
        assert len(view["cards"]) == 2


# ── Cross-cutting view structure tests ───────────────────────────────────


class TestAllViewsCommonStructure:
    """Verify all 5 views share the expected Lovelace tab structure."""

    VIEW_FUNCTIONS = [
        generate_licht_view,
        generate_helligkeit_view,
        generate_heiz_view,
        generate_bewegung_view,
        generate_praesenz_view,
    ]

    @pytest.mark.parametrize("gen_fn", VIEW_FUNCTIONS)
    def test_has_required_keys(self, gen_fn):
        view = gen_fn()
        _assert_valid_view(view)

    @pytest.mark.parametrize("gen_fn", VIEW_FUNCTIONS)
    def test_has_badges_key(self, gen_fn):
        view = gen_fn()
        assert "badges" in view
        assert isinstance(view["badges"], list)

    @pytest.mark.parametrize("gen_fn", VIEW_FUNCTIONS)
    def test_with_zones_has_required_keys(self, gen_fn):
        view = gen_fn(zones=_sample_zones())
        _assert_valid_view(view)

    @pytest.mark.parametrize("gen_fn", VIEW_FUNCTIONS)
    def test_cards_are_dicts(self, gen_fn):
        view = gen_fn(zones=_sample_zones())
        for card in view["cards"]:
            assert isinstance(card, dict), f"Card is not a dict: {card}"

    @pytest.mark.parametrize("gen_fn", VIEW_FUNCTIONS)
    def test_all_cards_have_type(self, gen_fn):
        view = gen_fn(zones=_sample_zones())
        for card in view["cards"]:
            assert "type" in card, f"Card missing 'type' key: {card}"

    def test_all_paths_unique(self):
        """All 5 views must have unique paths to avoid Lovelace conflicts."""
        paths = set()
        for gen_fn in self.VIEW_FUNCTIONS:
            view = gen_fn()
            paths.add(view["path"])
        assert len(paths) == 5

    def test_all_titles_unique(self):
        """All 5 views must have unique titles."""
        titles = set()
        for gen_fn in self.VIEW_FUNCTIONS:
            view = gen_fn()
            titles.add(view["title"])
        assert len(titles) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
