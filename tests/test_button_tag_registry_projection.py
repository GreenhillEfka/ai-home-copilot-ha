"""Contract tests for button_tag_registry projection surface."""
from __future__ import annotations

import ast
import pytest

REPO_ROOT = "custom_components/pilotsuite"
ARTEFACT = f"{REPO_ROOT}/button_tag_registry.py"


class TestButtonTagRegistryProjection:
    """Source-guard contract for button_tag_registry.py."""

    def test_unique_id_is_canonical(self):
        """TR1: _attr_unique_id uses pilotsuite prefix, not copilot_ha."""
        with open(ARTEFACT, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "_attr_unique_id"
                    ):
                        value = ast.literal_eval(node.value)
                        assert "pilotsuite" in value, (
                            f"_attr_unique_id must use pilotsuite prefix, got: {value}"
                        )
                        assert "copilot_ha" not in value

    def test_notification_id_is_canonical(self):
        """TR2: persistent_notification uses pilotsuite prefix, not copilot_ha."""
        with open(ARTEFACT, encoding="utf-8") as f:
            content = f.read()

        assert "copilot_ha_tag_registry" not in content
        assert "pilotsuite_tag_registry" in content

    def test_no_stale_copilot_ha_literals(self):
        """TR3: AST scan — no copilot_ha hardcodes remain in this file."""
        with open(ARTEFACT, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        copilot_ha_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    copilot_ha_found.append(node.value)

        assert not copilot_ha_found, (
            f"Stale copilot_ha literals found: {copilot_ha_found}"
        )
