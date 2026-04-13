"""Projection contract tests for media_context_v2_entities unique_ids."""
import ast
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/media_context_v2_entities.py")
assert SRC.exists(), f"Source not found: {SRC}"


def _get_unique_ids() -> list[str]:
    """Extract all unique_id= keyword argument strings from the source."""
    source = SRC.read_text()
    found = []
    for line in source.splitlines():
        if "unique_id=" in line:
            idx = line.index("unique_id=")
            rest = line[idx + len("unique_id="):].lstrip()
            if rest.startswith('"') or rest.startswith("'"):
                quote = rest[0]
                end = rest.index(quote, 1)
                found.append(rest[1:end])
    return found


class TestMediaContextV2UniqueIds:
    """Contract: all unique_id values use pilotsuite_ prefix."""

    def test_active_mode_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_active_mode" in uids, (
            "ActiveModeSensor unique_id must be pilotsuite_media_active_mode"
        )

    def test_active_target_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_active_target" in uids, (
            "ActiveTargetSensor unique_id must be pilotsuite_media_active_target"
        )

    def test_active_zone_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_active_zone" in uids, (
            "ActiveZoneSensor unique_id must be pilotsuite_media_active_zone"
        )

    def test_volume_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_volume" in uids, (
            "VolumeControlNumber unique_id must be pilotsuite_media_volume"
        )

    def test_volume_up_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_volume_up" in uids, (
            "VolumeUpButton unique_id must be pilotsuite_media_volume_up"
        )

    def test_volume_down_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_volume_down" in uids, (
            "VolumeDownButton unique_id must be pilotsuite_media_volume_down"
        )

    def test_volume_mute_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_volume_mute" in uids, (
            "VolumeMuteButton unique_id must be pilotsuite_media_volume_mute"
        )

    def test_zone_select_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_zone_select" in uids, (
            "ZoneSelectEntity unique_id must be pilotsuite_media_zone_select"
        )

    def test_manual_target_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_manual_target" in uids, (
            "ManualTargetSelectEntity unique_id must be pilotsuite_media_manual_target"
        )

    def test_clear_overrides_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_clear_overrides" in uids, (
            "ClearOverridesButton unique_id must be pilotsuite_media_clear_overrides"
        )

    def test_config_validation_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_config_validation" in uids, (
            "ConfigValidationSensor unique_id must be pilotsuite_media_config_validation"
        )

    def test_debug_info_unique_id(self):
        uids = _get_unique_ids()
        assert "pilotsuite_media_debug_info" in uids, (
            "DebugInfoSensor unique_id must be pilotsuite_media_debug_info"
        )

    def test_no_stale_copilot_ha_unique_ids(self):
        uids = _get_unique_ids()
        stale = [u for u in uids if "copilot_ha" in u]
        assert not stale, f"Found stale copilot_ha unique_ids: {stale}"

    def test_ast_scan_no_copilot_ha_literal(self):
        source = SRC.read_text()
        tree = ast.parse(source)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "unique_id":
                if isinstance(node.value, ast.Constant) and "copilot_ha" in node.value.value:
                    found.append(node.value.value)
        assert not found, f"AST found copilot_ha literal in unique_id kwarg: {found}"
