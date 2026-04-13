"""Contract: inventory_entities unique_id uses pilotsuite prefix."""
# Owner: HomeClaw-Lane / HA-403
# Filename contract: unique_id must use pilotsuite prefix, not copilot_ha.

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent / "custom_components" / "pilotsuite"
SOURCE_FILE = REPO_ROOT / "inventory_entities.py"

SRC = SOURCE_FILE.read_text()


class TestInventoryEntitiesProjection:
    """Projection guard for inventory_entities.py."""

    def test_il1_pilotsuite_unique_id(self):
        """IL1: _attr_unique_id uses pilotsuite prefix, not copilot_ha."""
        assert "pilotsuite_inventory_last_run" in SRC
        assert "copilot_ha_inventory_last_run" not in SRC

    def test_il2_no_stale_copilot_ha_literals(self):
        """IL2: No copilot_ha string literals remain in inventory_entities."""
        for i, line in enumerate(SRC.splitlines(), 1):
            assert "copilot_ha" not in line, f"L{i}: stale copilot_ha in {line.strip()!r}"

    def test_il3_ast_scan(self):
        """IL3: AST scan confirms no copilot_ha hardcodes in body."""
        tree = ast.parse(SRC)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    found.append(node.value)
        assert not found, f"AST constants with copilot_ha: {found!r}"

    # IL4: reserved for owner pragma if needed
