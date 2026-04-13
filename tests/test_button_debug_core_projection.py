"""Contract tests for button_debug_core.py projection parity."""
import ast
import pytest

from pathlib import Path

SRC = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/button_debug_core.py")


class BDC1:
    """Unique IDs must use pilotsuite prefix, not copilot_ha."""

    def test_unique_ids_are_pilotsuite_prefixed(self):
        src = SRC.read_text()
        for line in src.splitlines():
            if "_attr_unique_id" in line and "=" in line:
                val = line.split("=")[1].strip().strip('"').strip("'")
                assert val.startswith("pilotsuite_"), (
                    f"Stale copilot_ha unique_id: {val}"
                )


class BDC2:
    """No stale copilot_ha literals in notification_id calls."""

    def test_no_stale_copilot_ha_in_notification_ids(self):
        src = SRC.read_text()
        assert 'notification_id="copilot_ha' not in src
        assert "notification_id='copilot_ha" not in src


class BDC3:
    """AST scan: no unexplained copilot_ha string literals."""

    def test_no_unexplained_copilot_ha_literals(self):
        tree = ast.parse(SRC.read_text())
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and "pilotsuite" not in node.value:
                    found.append(node.value)
        assert not found, f"Unexplained copilot_ha literals: {found}"


class BDC4:
    """Owner pragma marker."""
    _owner = "homeclaw/ha-lane"


def test_all_bdc_contracts():
    BDC1().test_unique_ids_are_pilotsuite_prefixed()
    BDC2().test_no_stale_copilot_ha_in_notification_ids()
    BDC3().test_no_unexplained_copilot_ha_literals()
