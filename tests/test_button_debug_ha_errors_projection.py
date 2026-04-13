"""Contract: button_debug_ha_errors.py projections must use pilotsuite canonical identity."""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

REPO_ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current")
SRC = REPO_ROOT / "custom_components/pilotsuite/button_debug_ha_errors.py"


# --------------------------------------------------------------------------- #
# BDE1 – pilotsuite unique_id on CopilotHaErrorsFetchButton
# --------------------------------------------------------------------------- #
def test_bde1_ha_errors_fetch_unique_id_is_pilotsuite():
    """BDE1: CopilotHaErrorsFetchButton must have pilotsuite-prefixed unique_id."""
    content = SRC.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CopilotHaErrorsFetchButton":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == "_attr_unique_id":
                            val = item.value.value if isinstance(item.value, ast.Constant) else None
                            assert val == "pilotsuite_fetch_ha_errors", (
                                f"BDE1 FAIL: unique_id is {val!r}, expected pilotsuite_fetch_ha_errors"
                            )
                            return
    pytest.fail("BDE1: CopilotHaErrorsFetchButton._attr_unique_id not found in source")


# --------------------------------------------------------------------------- #
# BDE2 – no stale copilot_ha notification_id anywhere in the file
# --------------------------------------------------------------------------- #
def test_bde2_no_stale_copilot_ha_notification_id():
    """BDE2: button_debug_ha_errors.py must have no stale copilot_ha notification_id."""
    content = SRC.read_text()
    lines_with_stale = [
        ln for ln in content.splitlines()
        if "copilot_ha" in ln.lower() and "notification_id" in ln
    ]
    assert not lines_with_stale, (
        f"BDE2 FAIL: stale copilot_ha notification_id found: {lines_with_stale}"
    )


# --------------------------------------------------------------------------- #
# BDE3 – AST scan: no unexplained copilot_ha literals
# --------------------------------------------------------------------------- #
def test_bde3_ast_scan_no_unexplained_copilot_ha():
    """BDE3: AST scan must find zero unexplained copilot_ha literals."""
    content = SRC.read_text()
    tree = ast.parse(content)

    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                literals.append(node.value)

    assert not literals, f"BDE3 FAIL: unexplained copilot_ha literals remain: {literals}"