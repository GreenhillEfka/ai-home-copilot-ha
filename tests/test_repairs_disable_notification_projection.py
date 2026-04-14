"""Projection Contract Tests — repairs disable notification_ids (HA-440).

Verifies repairs.py uses pilotsuite_repair_disable_* notification_ids,
not copilot_ha_repair_disable_*.

Contract:
- notification_id for disable-failed uses pilotsuite_repair_disable_failed prefix
- notification_id for disable-details uses pilotsuite_repair_disable_details prefix
- AST scan: no copilot_ha_repair_disable_* literals in repairs.py

HA-440 — 2026-04-14
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite")
SRC = ROOT / "repairs.py"


class TestRepairsDisableNotificationCanonical:
    """Contract tests for repairs disable notification_id prefixes."""

    def test_disable_failed_notification_uses_pilotsuite(self):
        """_notify_repair_diagnostics for disable-failed must use pilotsuite_repair_disable_failed."""
        src_text = SRC.read_text()
        # Find the _safe_notification_id call inside _notify_repair_diagnostics for disable-failed
        lines = src_text.splitlines()
        found_pilotsuite = False
        found_copilot_ha = False
        for i, line in enumerate(lines):
            if "pilotsuite_repair_disable_failed" in line:
                found_pilotsuite = True
            if "copilot_ha_repair_disable_failed" in line:
                found_copilot_ha = True
        assert found_pilotsuite, "pilotsuite_repair_disable_failed not found in repairs.py"
        assert not found_copilot_ha, "copilot_ha_repair_disable_failed still present in repairs.py"

    def test_disable_details_notification_uses_pilotsuite(self):
        """_notify_repair_diagnostics for disable-details must use pilotsuite_repair_disable_details."""
        src_text = SRC.read_text()
        lines = src_text.splitlines()
        found_pilotsuite = False
        found_copilot_ha = False
        for i, line in enumerate(lines):
            if "pilotsuite_repair_disable_details" in line:
                found_pilotsuite = True
            if "copilot_ha_repair_disable_details" in line:
                found_copilot_ha = True
        assert found_pilotsuite, "pilotsuite_repair_disable_details not found in repairs.py"
        assert not found_copilot_ha, "copilot_ha_repair_disable_details still present in repairs.py"

    def test_ast_scan_no_copilot_ha_repair_disable_literals(self):
        """AST scan: no copilot_ha_repair_disable_* literals in repairs.py."""
        src_text = SRC.read_text()
        tree = ast.parse(src_text)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha_repair_disable" in node.value:
                    violations.append(f"Line {node.lineno}: {node.value!r}")

        assert not violations, f"Found copilot_ha_repair_disable literals:\n{violations}"
