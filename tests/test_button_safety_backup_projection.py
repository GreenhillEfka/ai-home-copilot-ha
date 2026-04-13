"""Contract tests for button_safety_backup.py projection parity."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path("custom_components/pilotsuite/button_safety_backup.py")
MODULE = "custom_components.pilotsuite.button_safety_backup"


class TestButtonSafetyBackupProjection:
    """Guard: button_safety_backup.py unique_ids use pilotsuite prefix, not copilot_ha."""

    def test_bsb_unique_id_create_is_pilotsuite(self):
        """SB1: CopilotSafetyBackupCreateButton._attr_unique_id uses pilotsuite prefix."""
        source = COMPONENT.read_text()
        lines = source.split("\n")
        # Find class CopilotSafetyBackupCreateButton, then its _attr_unique_id assignment
        in_create_class = False
        for i, line in enumerate(lines):
            if "class CopilotSafetyBackupCreateButton" in line:
                in_create_class = True
            elif in_create_class and "_attr_unique_id" in line:
                assert "pilotsuite_safety_backup_create" in line, (
                    f"Line {i+1}: _attr_unique_id must use 'pilotsuite_safety_backup_create', got: {line.strip()}"
                )
                return
        pytest.fail("_attr_unique_id assignment for CopilotSafetyBackupCreateButton not found")

    def test_bsb_unique_id_status_is_pilotsuite(self):
        """SB2: CopilotSafetyBackupStatusButton._attr_unique_id uses pilotsuite prefix."""
        source = COMPONENT.read_text()
        lines = source.split("\n")
        in_status_class = False
        for i, line in enumerate(lines):
            if "class CopilotSafetyBackupStatusButton" in line:
                in_status_class = True
            elif in_status_class and "_attr_unique_id" in line:
                assert "pilotsuite_safety_backup_status" in line, (
                    f"Line {i+1}: _attr_unique_id must use 'pilotsuite_safety_backup_status', got: {line.strip()}"
                )
                return
        pytest.fail("_attr_unique_id assignment for CopilotSafetyBackupStatusButton not found")

    def test_bsb_no_stale_copilot_ha_in_unique_ids(self):
        """SB3: No copilot_ha unique_id literals remain in the module AST."""
        tree = ast.parse(COMPONENT.read_text())
        source = COMPONENT.read_text()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_attr_unique_id":
                        value = ast.get_source_segment(source, node) or ""
                        assert "copilot_ha" not in value, (
                            f"Stale copilot_ha literal found in _attr_unique_id assignment: {value}"
                        )
