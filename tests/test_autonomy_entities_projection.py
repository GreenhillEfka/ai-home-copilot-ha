"""Contract tests for autonomy_entities unique_id parity."""
import ast
import re
import pytest

from custom_components.pilotsuite import autonomy_entities as mod


class TestAutonomyEntitiesProjection:
    """Projection parity contract for autonomy_entities.py."""

    def test_zone_module_state_select_unique_id_uses_pilotsuite(self):
        """AE1: ZoneModuleStateSelect._attr_unique_id uses pilotsuite prefix."""
        source = open(mod.__file__).read()
        # Find the ZoneModuleStateSelect __init__ body
        match = re.search(
            r'class ZoneModuleStateSelect.*?(?=\nclass |\Z)',
            source,
            re.DOTALL,
        )
        assert match, "ZoneModuleStateSelect class not found"
        class_body = match.group()
        assert 'pilotsuite_zone_' in class_body, (
            "ZoneModuleStateSelect unique_id does not use pilotsuite_zone_ prefix. "
            "Expected pattern: pilotsuite_zone_<zone_id>_<module_id>_state"
        )
        assert 'copilot_ha_zone_' not in class_body, (
            "ZoneModuleStateSelect still contains copilot_ha_zone_ legacy unique_id"
        )

    def test_zone_scene_capture_button_unique_id_uses_pilotsuite(self):
        """AE2: ZoneSceneCaptureButton._attr_unique_id uses pilotsuite prefix."""
        source = open(mod.__file__).read()
        match = re.search(
            r'class ZoneSceneCaptureButton.*?(?=\nclass |\ndef |\Z)',
            source,
            re.DOTALL,
        )
        assert match, "ZoneSceneCaptureButton class not found"
        class_body = match.group()
        assert 'pilotsuite_zone_' in class_body, (
            "ZoneSceneCaptureButton unique_id does not use pilotsuite_zone_ prefix. "
            "Expected pattern: pilotsuite_zone_<zone_id>_scene_capture"
        )
        assert 'copilot_ha_zone_' not in class_body, (
            "ZoneSceneCaptureButton still contains copilot_ha_zone_ legacy unique_id"
        )

    def test_no_stale_copilot_ha_literal_in_autonomy_entities(self):
        """AE3: AST scan confirms no stale copilot_ha literals in the module."""
        source = open(mod.__file__).read()
        tree = ast.parse(source)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    found.append(f"{node.lineno}: {node.value!r}")
        assert not found, (
            f"Stale copilot_ha string literals found in autonomy_entities.py: {found}"
        )
