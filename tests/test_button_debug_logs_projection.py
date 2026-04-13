"""Contract: button_debug_logs.py projections must use pilotsuite canonical identity."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current")
SRC = REPO_ROOT / "custom_components/pilotsuite/button_debug_logs.py"


# --------------------------------------------------------------------------- #
# BDL1 – pilotsuite unique_ids on all buttons
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "cls_name,expected_unique_id",
    [
        ("CopilotAnalyzeLogsButton", "pilotsuite_analyze_logs"),
        ("CopilotRollbackLastFixButton", "pilotsuite_rollback_last_fix"),
        ("CopilotDevLogTestPushButton", "pilotsuite_devlog_push_test"),
        ("CopilotDevLogPushLatestButton", "pilotsuite_devlog_push_latest"),
        ("CopilotDevLogsFetchButton", "pilotsuite_devlogs_fetch"),
    ],
)
def test_bdl1_unique_ids_are_pilotsuite(cls_name, expected_unique_id):
    """BDL1: Each button class must have the pilotsuite-prefixed unique_id."""
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
                                f"BDL1 FAIL [{cls_name}]: unique_id is {val!r}, "
                                f"expected {expected_unique_id!r}"
                            )
                            return
    pytest.fail(f"BDL1: {cls_name}._attr_unique_id not found in source")


# --------------------------------------------------------------------------- #
# BDL2 – no stale copilot_ha notification_ids
# --------------------------------------------------------------------------- #
def test_bdl2_no_stale_notification_id():
    """BDL2: button_debug_logs.py must have no copilot_ha notification_ids."""
    content = SRC.read_text()
    lines_with_stale = [
        ln for ln in content.splitlines()
        if "copilot_ha" in ln.lower() and "notification_id" in ln
    ]
    assert not lines_with_stale, (
        f"BDL2 FAIL: stale copilot_ha notification_id found: {lines_with_stale}"
    )


# --------------------------------------------------------------------------- #
# BDL3 – AST scan: no unexplained copilot_ha literals
# --------------------------------------------------------------------------- #
def test_bdl3_ast_scan_no_unexplained_copilot_ha():
    """BDL3: AST scan must find zero unexplained copilot_ha literals."""
    content = SRC.read_text()
    tree = ast.parse(content)

    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                literals.append(node.value)

    assert not literals, f"BDL3 FAIL: unexplained copilot_ha literals remain: {literals}"