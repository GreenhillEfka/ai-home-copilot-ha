"""Tests for the FrontendModule and frontend entities."""
import pytest
from unittest.mock import MagicMock

from custom_components.copilot_ha.frontend_entities import (
    DASHBOARD_VIEWS,
    DashboardRefreshButton,
    DashboardViewToggleSwitch,
    create_frontend_entities,
)
from custom_components.copilot_ha.core.modules.frontend_module import (
    DASHBOARD_VIEW_PATHS,
    FrontendModule,
)
from custom_components.copilot_ha.dashboard_wiring import (
    _build_storage_dashboard_config,
)


class TestDashboardViewPaths:
    """Verify view path constants are consistent."""

    def test_view_paths_match_entity_definitions(self):
        entity_paths = {v[0] for v in DASHBOARD_VIEWS}
        module_paths = set(DASHBOARD_VIEW_PATHS)
        assert entity_paths == module_paths

    def test_eight_views_defined(self):
        assert len(DASHBOARD_VIEW_PATHS) == 8
        assert len(DASHBOARD_VIEWS) == 8

    def test_all_expected_paths_present(self):
        expected = {"styx", "haushalt", "zonen", "automation",
                    "energie", "musik", "ki", "chat"}
        assert set(DASHBOARD_VIEW_PATHS) == expected


class TestFrontendModule:
    """Test FrontendModule instance behavior (no HA runtime)."""

    def test_module_name(self):
        mod = FrontendModule()
        assert mod.name == "frontend_module"


class TestDashboardViewDefinitions:
    """Test DASHBOARD_VIEWS constant structure."""

    def test_each_view_has_three_elements(self):
        for view in DASHBOARD_VIEWS:
            assert len(view) == 3, f"View {view} should have (path, label, icon)"

    def test_all_icons_are_mdi(self):
        for path, label, icon in DASHBOARD_VIEWS:
            assert icon.startswith("mdi:"), f"Icon for {path} should be mdi:*"

    def test_unique_paths(self):
        paths = [v[0] for v in DASHBOARD_VIEWS]
        assert len(paths) == len(set(paths))

    def test_unique_labels(self):
        labels = [v[1] for v in DASHBOARD_VIEWS]
        assert len(labels) == len(set(labels))


class TestCreateFrontendEntities:
    """Test entity factory function (with mock coordinator)."""

    @pytest.fixture
    def mock_coordinator(self):
        coord = MagicMock()
        coord._config = {"host": "localhost", "port": "8909"}
        return coord

    @pytest.fixture
    def mock_entry(self):
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.domain = "copilot_ha"
        return entry

    def test_returns_switches_and_buttons(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        assert "switch" in result
        assert "button" in result
        assert len(result["switch"]) == 8
        assert len(result["button"]) == 1

    def test_switch_unique_ids_are_unique(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        ids = [s._attr_unique_id for s in result["switch"]]
        assert len(ids) == len(set(ids))

    def test_switch_names_contain_view_label(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        for switch, (path, label, icon) in zip(result["switch"], DASHBOARD_VIEWS):
            assert label in switch._attr_name
            assert switch._attr_icon == icon

    def test_button_has_correct_attrs(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        btn = result["button"][0]
        assert btn._attr_icon == "mdi:view-dashboard-edit"
        assert "Rebuild" in btn._attr_name

    def test_switch_unique_id_format(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        for switch in result["switch"]:
            assert "dashboard_view_" in switch._attr_unique_id

    def test_button_unique_id(self, mock_coordinator, mock_entry):
        result = create_frontend_entities(mock_coordinator, mock_entry)
        btn = result["button"][0]
        assert "dashboard_rebuild" in btn._attr_unique_id


class TestBuildStorageDashboardConfigFiltering:
    """Test enabled_views parameter in dashboard config builder."""

    def test_all_views_when_none(self):
        config = _build_storage_dashboard_config([])
        assert len(config["views"]) == 8

    def test_filter_to_two_views(self):
        config = _build_storage_dashboard_config(
            [], enabled_views={"chat", "ki"}
        )
        paths = {v["path"] for v in config["views"]}
        assert paths == {"chat", "ki"}
        assert len(config["views"]) == 2

    def test_filter_to_empty(self):
        config = _build_storage_dashboard_config(
            [], enabled_views=set()
        )
        assert len(config["views"]) == 0

    def test_filter_preserves_view_content(self):
        entities = ["sensor.pilotsuite_mood_score"]
        config = _build_storage_dashboard_config(
            entities, enabled_views={"haushalt"}
        )
        assert len(config["views"]) == 1
        assert config["views"][0]["path"] == "haushalt"
        assert config["views"][0]["title"] == "Haushalt"

    def test_all_views_when_all_enabled(self):
        all_paths = set(DASHBOARD_VIEW_PATHS)
        config = _build_storage_dashboard_config([], enabled_views=all_paths)
        assert len(config["views"]) == 8

    def test_single_view_chat(self):
        config = _build_storage_dashboard_config([], enabled_views={"chat"})
        assert len(config["views"]) == 1
        assert config["views"][0]["path"] == "chat"
        assert config["views"][0]["icon"] == "mdi:chat-outline"

    def test_view_order_preserved(self):
        """Views should maintain their original order even when filtered."""
        config = _build_storage_dashboard_config(
            [], enabled_views={"chat", "styx", "energie"}
        )
        paths = [v["path"] for v in config["views"]]
        assert paths == ["styx", "energie", "chat"]
