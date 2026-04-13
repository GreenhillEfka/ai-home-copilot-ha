"""Projection contract tests for habitus_zones_entities_v2 unique_ids."""
import ast
import sys
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/habitus_zones_entities_v2.py")
assert SRC.exists(), f"Source not found: {SRC}"


def _get_unique_ids() -> list[str]:
    """Extract all _attr_unique_id assignments from the source."""
    source = SRC.read_text()
    tree = ast.parse(source)
    unique_ids = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_attr_unique_id":
                    if isinstance(node.value, ast.Constant):
                        unique_ids.append(node.value.value)
    return unique_ids


def _get_notification_ids() -> list[str]:
    """Extract all notification_id= keyword argument strings from the source."""
    source = SRC.read_text()
    found = []
    for line in source.splitlines():
        if 'notification_id=' in line:
            # Extract the string value after notification_id=
            idx = line.index('notification_id=')
            rest = line[idx + len('notification_id='):].lstrip()
            if rest.startswith('"') or rest.startswith("'"):
                quote = rest[0]
                end = rest.index(quote, 1)
                found.append(rest[1:end])
    return found


class TestHabitusZonesV2NotificationIds:
    """Contract: all notification_id values use pilotsuite_ prefix."""

    def test_no_stale_copilot_ha_notification_ids(self):
        nids = _get_notification_ids()
        stale = [n for n in nids if "copilot_ha" in n]
        assert not stale, f"Found stale copilot_ha notification_ids: {stale}"

    def test_ast_scan_no_copilot_ha_literal_in_notification_id(self):
        source = SRC.read_text()
        tree = ast.parse(source)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "notification_id":
                if isinstance(node.value, ast.Constant) and "copilot_ha" in node.value.value:
                    found.append(node.value.value)
        assert not found, f"AST found copilot_ha literal in notification_id kwarg: {found}"


class TestHabitusZonesV2UniqueIds:
    """Contract: all _attr_unique_id values use pilotsuite_ prefix."""

    def test_habitus_zones_v2_json_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_json" in uids, (
            "HabitusZonesV2JsonInputTextAttr unique_id must be "
            "pilotsuite_habitus_zones_v2_json"
        )

    def test_habitus_zones_count_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_count" in uids, (
            "HabitusZonesV2CountSensor unique_id must be "
            "pilotsuite_habitus_zones_count"
        )

    def test_habitus_zones_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones" in uids, (
            "HabitusZonesV2Sensor unique_id must be pilotsuite_habitus_zones"
        )

    def test_validate_habitus_zones_v2_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_validate_habitus_zones_v2" in uids, (
            "HabitusZonesV2ValidateButton unique_id must be "
            "pilotsuite_validate_habitus_zones_v2"
        )

    def test_habitus_zones_v2_states_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_states" in uids, (
            "HabitusZonesV2StatesSensor unique_id must be "
            "pilotsuite_habitus_zones_v2_states"
        )

    def test_habitus_zones_v2_health_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_health" in uids, (
            "HabitusZonesV2HealthSensor unique_id must be "
            "pilotsuite_habitus_zones_v2_health"
        )

    def test_habitus_zones_v2_global_state_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_global_state" in uids, (
            "HabitusZonesV2GlobalStateSelect unique_id must be "
            "pilotsuite_habitus_zones_v2_global_state"
        )

    def test_habitus_zones_v2_sync_graph_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_sync_graph" in uids, (
            "HabitusZonesV2SyncGraphButton unique_id must be "
            "pilotsuite_habitus_zones_v2_sync_graph"
        )

    def test_habitus_zones_v2_reload_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_habitus_zones_v2_reload" in uids, (
            "HabitusZonesV2ReloadButton unique_id must be "
            "pilotsuite_habitus_zones_v2_reload"
        )

    def test_no_stale_copilot_ha_unique_ids(self):
        uids = _get_unique_ids()
        stale = [u for u in uids if "copilot_ha" in u]
        assert not stale, f"Found stale copilot_ha unique_ids: {stale}"

    def test_ast_scan_no_copilot_ha_literal_in_unique_id_assignments(self):
        source = SRC.read_text()
        tree = ast.parse(source)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_attr_unique_id":
                        if isinstance(node.value, ast.Constant) and "copilot_ha" in node.value.value:
                            found.append(node.value.value)
        assert not found, f"AST found copilot_ha literal in _attr_unique_id: {found}"
