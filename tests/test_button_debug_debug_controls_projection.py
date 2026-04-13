"""Contract: button_debug_debug_controls.py projections must use pilotsuite canonical identity."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current")
SRC = REPO_ROOT / "custom_components/pilotsuite/button_debug_debug_controls.py"


# --------------------------------------------------------------------------- #
# BDC1 – pilotsuite unique_ids on all buttons
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "cls_name,expected_unique_id",
    [
        ("CopilotEnableDebug30mButton", "pilotsuite_enable_debug_30m"),
        ("CopilotDisableDebugButton", "pilotsuite_disable_debug"),
        ("CopilotClearErrorDigestButton", "pilotsuite_clear_error_digest"),
        ("CopilotClearAllLogsButton", "pilotsuite_clear_all_logs"),
    ],
)
def test_bdc1_unique_ids_are_pilotsuite(cls_name, expected_unique_id):
    """BDC1: Each button class must have the pilotsuite-prefixed unique_id."""
    content = SRC.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls_name:
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == "_attr_unique_id":
                            val = item.value.value if isinstance(item.value, ast.Constant) else None
                            assert val == expected_unique_id, (
                                f"BDC1 FAIL [{cls_name}]: unique_id is {val!r}, "
                                f"expected {expected_unique_id!r}"
                            )
                            return
    pytest.fail(f"BDC1: {cls_name}._attr_unique_id not found in source")


# --------------------------------------------------------------------------- #
# BDC2 – no stale copilot_ha notification_ids
# --------------------------------------------------------------------------- #
def test_bdc2_no_stale_notification_id():
    """BDC2: button_debug_debug_controls.py must have no copilot_ha notification_ids."""
    content = SRC.read_text()
    lines_with_stale = [
        ln for ln in content.splitlines()
        if "copilot_ha" in ln.lower() and "notification_id" in ln
    ]
    assert not lines_with_stale, (
        f"BDC2 FAIL: stale copilot_ha notification_id found: {lines_with_stale}"
    )


# --------------------------------------------------------------------------- #
# BDC3 – AST scan: no unexplained copilot_ha literals
# --------------------------------------------------------------------------- #
def test_bdc3_ast_scan_no_unexplained_copilot_ha():
    """BDC3: AST scan must find zero unexplained copilot_ha literals."""
    content = SRC.read_text()
    tree = ast.parse(content)

    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                literals.append(node.value)

    assert not literals, f"BDC3 FAIL: unexplained copilot_ha literals remain: {literals}"