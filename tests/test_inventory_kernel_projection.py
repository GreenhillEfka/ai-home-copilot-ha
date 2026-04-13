"""Contract test: inventory_kernel.py pilotsuite canonicalization (HA-398)."""
import ast
import re
from pathlib import Path

import pytest

ARTIFACT = Path("custom_components/pilotsuite/inventory_kernel.py")
CONTENT = ARTIFACT.read_text()


class TestInventoryKernelCanonicalization:
    """IK1: EXPORT_DIR uses pilotsuite path."""
    def test_ik1_export_dir_pilotsuite(self):
        assert 'EXPORT_DIR = "/config/pilotsuite/exports"' in CONTENT

    """IK2: PUBLISH_DIR uses pilotsuite path."""
    def test_ik2_publish_dir_pilotsuite(self):
        assert 'PUBLISH_DIR = "/config/www/pilotsuite"' in CONTENT

    """IK3: URL path uses /local/pilotsuite/."""
    def test_ik3_url_local_pilotsuite(self):
        # f-strings: literal contains f"/local/pilotsuite/..."
        assert 'f"/local/pilotsuite/' in CONTENT or \
               'f\'/local/pilotsuite/' in CONTENT or \
               any('pilotsuite' in h for h in re.findall(r'/local/\w+', CONTENT))
        hits = re.findall(r'["\']/local/(?:copilot_ha|pilotsuite)/\w+', CONTENT)
        assert all("copilot_ha" not in h for h in hits)

    """IK4: notification_id uses pilotsuite."""
    def test_ik4_notification_id_pilotsuite(self):
        assert 'notification_id="pilotsuite_inventory"' in CONTENT

    """IK5: schema string uses pilotsuite_inventory."""
    def test_ik5_schema_pilotsuite(self):
        assert '"schema": "pilotsuite_inventory"' in CONTENT

    """IK6: base filename uses pilotsuite_inventory_ prefix."""
    def test_ik6_base_filename_pilotsuite(self):
        assert "pilotsuite_inventory_" in CONTENT

    """IK7: no copilot_ha hardcode strings in AST (IGNORES comments/Legacy)."""
    def test_ik7_no_copilot_ha_in_ast(self):
        tree = ast.parse(CONTENT)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and "legacy" not in node.value.lower():
                    found.append(node.value)
        assert not found, f"Unexpected copilot_ha strings: {found}"