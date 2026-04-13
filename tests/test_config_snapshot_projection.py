"""Projection test for config_snapshot LEGACY path constants."""
import ast
import sys
from pathlib import Path

ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite")
SRC = ROOT / "config_snapshot.py"


class TestConfigSnapshotLEGACY:
    """Contract tests for LEGACY_* path constants in config_snapshot.py."""

    def test_legacy_export_dir_uses_pilotsuite(self):
        """LEGACY_EXPORT_DIR must reference pilotsuite, not copilot_ha."""
        src_text = SRC.read_text()
        assert 'LEGACY_EXPORT_DIR = "/config/pilotsuite' in src_text, (
            f"LEGACY_EXPORT_DIR must use /config/pilotsuite, found:\n"
            f"{[l for l in src_text.splitlines() if 'LEGACY_EXPORT_DIR' in l]}"
        )
        assert 'LEGACY_EXPORT_DIR = "/config/copilot_ha' not in src_text

    def test_legacy_publish_dir_uses_pilotsuite(self):
        """LEGACY_PUBLISH_DIR must reference pilotsuite, not copilot_ha."""
        src_text = SRC.read_text()
        assert 'LEGACY_PUBLISH_DIR = "/config/www/pilotsuite' in src_text, (
            f"LEGACY_PUBLISH_DIR must use /config/www/pilotsuite, found:\n"
            f"{[l for l in src_text.splitlines() if 'LEGACY_PUBLISH_DIR' in l]}"
        )
        assert 'LEGACY_PUBLISH_DIR = "/config/www/copilot_ha' not in src_text

    def test_no_stale_copilot_ha_in_legacy_constants(self):
        """LEGACY_* constants must not contain copilot_ha string literals."""
        src_text = SRC.read_text()
        tree = ast.parse(src_text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.startswith("LEGACY_"):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            assert "copilot_ha" not in node.value.value, (
                                f"{target.id} contains stale copilot_ha reference: {node.value.value!r}"
                            )