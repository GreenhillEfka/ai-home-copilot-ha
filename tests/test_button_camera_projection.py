"""Contract guards for custom_components/pilotsuite/button_camera.py.

BC1: CopilotGenerateCameraDashboardButton _attr_unique_id is pilotsuite-prefixed
BC2: CopilotDownloadCameraDashboardButton _attr_unique_id is pilotsuite-prefixed
BC3: notification_id strings use pilotsuite prefix, not copilot_ha
BC4: no copilot_ha unique_id or notification_id hardcodes in AST
"""
from __future__ import annotations

import ast
import pytest
import re

SRC = "custom_components/pilotsuite/button_camera.py"


def _find_class_unique_id(tree: ast.AST, class_name: str):
    """Find _attr_unique_id assignment inside a specific class body."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id == "_attr_unique_id":
                            if isinstance(child.value, ast.Constant):
                                return child.value.value
    return None


class TestButtonCameraProjection:
    """Projection contract for CopilotGenerateCameraDashboardButton."""

    def test_bc1_generate_button_unique_id_is_pilotsuite(self):
        """BC1: generate button _attr_unique_id uses pilotsuite prefix."""
        with open(SRC) as f:
            src = f.read()
        tree = ast.parse(src)
        uid = _find_class_unique_id(tree, "CopilotGenerateCameraDashboardButton")
        assert uid is not None, "CopilotGenerateCameraDashboardButton _attr_unique_id not found"
        assert uid.startswith("pilotsuite_"), (
            f"generate button _attr_unique_id is {uid!r}, expected pilotsuite_ prefix"
        )
        assert not uid.startswith("copilot_ha_"), (
            f"generate button _attr_unique_id still uses copilot_ha_ prefix: {uid!r}"
        )

    def test_bc2_download_button_unique_id_is_pilotsuite(self):
        """BC2: download button _attr_unique_id uses pilotsuite prefix."""
        with open(SRC) as f:
            src = f.read()
        tree = ast.parse(src)
        uid = _find_class_unique_id(tree, "CopilotDownloadCameraDashboardButton")
        assert uid is not None, "CopilotDownloadCameraDashboardButton _attr_unique_id not found"
        assert uid.startswith("pilotsuite_"), (
            f"download button _attr_unique_id is {uid!r}, expected pilotsuite_ prefix"
        )
        assert not uid.startswith("copilot_ha_"), (
            f"download button _attr_unique_id still uses copilot_ha_ prefix: {uid!r}"
        )

    def test_bc3_no_copilot_ha_notification_id_hardcodes(self):
        """BC3: notification_id values use pilotsuite prefix, not copilot_ha."""
        with open(SRC) as f:
            src = f.read()
        # Scan for copilot_ha notification_id strings
        copilot_ha_nids = re.findall(r'notification_id\s*=\s*"copilot_ha_[^"]*"', src)
        assert len(copilot_ha_nids) == 0, (
            f"found {len(copilot_ha_nids)} stale copilot_ha notification_id hardcode(s): {copilot_ha_nids}"
        )

    def test_bc4_no_copilot_ha_unique_id_hardcodes(self):
        """BC4: _attr_unique_id values use pilotsuite prefix, not copilot_ha."""
        with open(SRC) as f:
            src = f.read()
        # Scan for copilot_ha _attr_unique_id strings
        copilot_ha_uids = re.findall(r'_attr_unique_id\s*=\s*"copilot_ha[^"]*"', src)
        assert len(copilot_ha_uids) == 0, (
            f"found {len(copilot_ha_uids)} stale copilot_ha _attr_unique_id hardcode(s): {copilot_ha_uids}"
        )